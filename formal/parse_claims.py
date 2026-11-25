"""パーサー。スキーマ（claims.json）の claims の形式化から Spec.lean を書き出し、
検証器を呼び、Lean の値と定理のファイルを書き、Lean の出力から判定を読む。"""
import json
import re
from fractions import Fraction
from pathlib import Path

from verifiers import QUERIES

FORMAL = Path(__file__).parent
LEAN = FORMAL / "lean"
SCHEMA = FORMAL / "claims.json"
STANDARD_AXIOMS = ["propext", "Classical.choice", "Quot.sound"]
LITERAL = {
    "String": lambda value: json.dumps(value, ensure_ascii=False),
    "Bool": lambda value: str(bool(value)).lower(),
    "ℕ": lambda value: str(int(value)),
    "ℚ": lambda value: f"(({Fraction(value).numerator} : ℚ) / {Fraction(value).denominator})",
    "String × String": lambda value: f"({json.dumps(value[0], ensure_ascii=False)}, {json.dumps(value[1], ensure_ascii=False)})",
}
# proved% は、証明が通った定理だけを参照する。通らなかった定理は Lean が sorry で埋めて残すので、名前があるだけでは使えない
HEADER = ["import Spec", "import Proofs", "import Values", "open Spec Values",
          "open Lean Elab Term in",
          "elab \"proved% \" theoremName:ident : term => do",
          "  let name ← realizeGlobalConstNoOverloadWithInfo theoremName",
          "  if (← collectAxioms name).contains ``sorryAx then throwError \"{name} は証明されていない\"",
          "  return mkConst name"]


def _structures() -> dict[str, list[tuple[str, str]]]:
    """Spec.lean にある構造体の、(項目の名前, 型) の並び。"""
    spec = (LEAN / "Spec.lean").read_text(encoding="utf-8")
    return {name: re.findall(r"^  (\w+) : (.+)$", body, re.M)
            for name, body in re.findall(r"^structure (\w+) where\n((?:  .*\n)+)", spec, re.M)}


def lean_literal(lean_type: str, value) -> str:
    if lean_type.startswith("List "):
        item_type = lean_type.removeprefix("List ").strip("()")
        return "[" + ", ".join(lean_literal(item_type, item) for item in value) + "]"
    if lean_type in LITERAL:
        return LITERAL[lean_type](value)
    # 構造体の値は、項目ごとの値をまとめたもの
    return "{ " + ", ".join(f"{field} := {lean_literal(field_type, value[field])}" for field, field_type in _structures()[lean_type]) + " }"


def _binders(signature: str) -> list[tuple[str, str]]:
    """明示の引数 (a b : T) を、(名前, 型) の組にする。"""
    return [(name, binder_type.strip()) for names, binder_type in re.findall(r"\(([^():]+):((?:[^()]|\([^()]*\))+)\)", signature)
            for name in names.split()]


def write_spec(record: dict) -> None:
    """claims の形式化（claim ごとの定義と命題）から、Spec.lean を書き出す。Lean が使う前に定義を求めるので、lean_order の順に並べる。"""
    claims = {claim["id"]: claim for claim in record["claims"]}
    blocks = ["\n".join(filter(None, [claims[i]["definitions"], f"/-- {claims[i]['explanation']} -/", claims[i]["proposition"]]))
              for i in record["lean_order"]]
    (LEAN / "Spec.lean").write_text("import Mathlib\n/-! claims.json から生成する。手で編集しない。 -/\n\nnamespace Spec\n\n"
                                    + "\n\n".join(blocks) + "\n\nend Spec\n", encoding="utf-8")


def load_schema() -> dict:
    """スキーマの宣言の部分（検証の結果を除いたもの）。命題の引数と、証明の有無を読み足す。"""
    record = json.loads(SCHEMA.read_text(encoding="utf-8"))
    proofs = (LEAN / "Proofs.lean").read_text(encoding="utf-8")
    for claim in record["claims"]:
        claim.pop("result", None)
        signature = re.match(rf"abbrev {claim['id']}\b(.*?) : Prop :=", claim["proposition"], re.S).group(1)
        claim["arguments"] = [{"name": name, "type": binder_type} for name, binder_type in _binders(signature)]
        claim["axiom_in_proofs"] = f"axiom {claim['id']}_axiom" in proofs
        unknown = [a["name"] for a in claim["arguments"] if a["name"] not in record["variables"] and a["name"] not in claim.get("declared", {})]
        if unknown:
            raise ValueError(f"{claim['id']}: 値の取り方が claims.json に無い: {unknown}")
    for variable in record["variables"].values():
        variable.pop("verified", None)
    # 抜けを止める
    claims = {claim["id"]: claim for claim in record["claims"]}
    children = {parent: [claim for claim in record["claims"] if claim["parent"] == parent] for parent in claims}
    declarations = [i for i, claim in claims.items() if claim["kind"] == "declaration" and not children[i][0]["id"].startswith("C")]
    missing = [i for i in declarations if f"def {i}.value" not in claims[i]["definitions"]]
    if missing:
        raise ValueError(f"宣言に、値の定義（.value）が無い: {missing}")
    unused = [i for i in declarations if not re.search(rf"\b{i}\b", claims[claims[i]["parent"]]["proposition"])
              or f"{i}.value" not in [value for child in children[i] for value in child.get("declared", {}).values()]]
    if unused:
        raise ValueError(f"宣言が、上の claim の式か、下の信頼性条件で使われていない: {unused}")
    # 宣言の値は、declared で引数として渡す。信頼性条件の式の中で直接参照すると、どの宣言の検証かが読めなくなる
    direct = [i for i, claim in claims.items() if i.startswith("R") and re.search(r"\bC\d\d\b", claim["proposition"].split(":=", 1)[1])]
    if direct:
        raise ValueError(f"信頼性条件が、宣言を式の中で直接参照している: {direct}")
    return record


def stored(record: dict) -> dict:
    """スキーマに書くもの。読み足したもの（命題の引数、証明の有無）は書かない。"""
    return record | {"claims": [{k: v for k, v in claim.items() if k not in ("arguments", "axiom_in_proofs")} for claim in record["claims"]]}


def _query(repository: str, mode: str, name: str, variable: dict):
    # fields があれば、項目ごとに問い合わせて、構造体の値にまとめる
    if "fields" in variable:
        return {field: _query(repository, mode, name, part) for field, part in variable["fields"].items()}
    return QUERIES[variable.get("verifier", "GitHub")][variable["query"]](repository, mode, name, **variable.get("args", {}))


def query_values(record: dict, repository: str, mode: str) -> tuple[dict, dict[str, str]]:
    """変数を、検証器に問い合わせる。(JSON の値, 取れなかった理由) を返す。"""
    values, errors = {}, {}
    for name, variable in record["variables"].items():
        try:
            values[name] = _query(repository, mode, name, variable)
        except Exception as error:  # 取れなかった値を使う claim だけを、未検証にする
            errors[name] = str(error)
    return values, errors


def write_values(record: dict) -> None:
    """検証済みの値から、Values.lean を書く。"""
    lines = ["import Spec", "/-! 検証済みの値。parse_claims.py が生成する。手で編集しない。 -/", "namespace Values", "open Spec"]
    for name, variable in record["variables"].items():
        if "verified" in variable:
            lines.append(f"def {name} : {variable['type']} := {lean_literal(variable['type'], variable['verified']['value'])}")
    (LEAN / "Values.lean").write_text("\n".join(lines + ["end Values", ""]), encoding="utf-8")


def _statement(claim: dict) -> str:
    # 宣言の値を受け取る引数には、declared に書いた宣言の値（C03.value など）を入れる
    declared = claim.get("declared", {})
    return " ".join([claim["id"]] + [declared.get(argument["name"], argument["name"]) for argument in claim["arguments"]])


def _proof(claim: dict) -> str:
    return f"{claim['id']}_axiom" if claim["kind"] == "axiom" else f"{claim['id']}_holds"


def candidates(record: dict, available: set[str]) -> list[str]:
    """各 claim の、真である定理と偽である（否定の）定理。通ったほうが判定になる。値が揃った claim だけを書く。"""
    claims = {claim["id"]: claim for claim in record["claims"]}
    proofs = (LEAN / "Proofs.lean").read_text(encoding="utf-8")
    axioms, lines, derived = [], [], {}
    for claim in record["claims"]:
        name, statement = claim["id"], _statement(claim)
        if not {a["name"] for a in claim["arguments"]} - set(claim.get("declared", {})) <= available:
            continue
        if claim["kind"] == "declaration":
            lines.append(f"#print axioms Spec.{name}_holds")
        elif claim["kind"] == "axiom":
            # 値を含む公理は、検証された値に対してだけ宣言する
            if not claim["axiom_in_proofs"]:
                axioms.append(f"axiom {name}_axiom : {statement}")
            lines.append(f"#print axioms {name}_axiom")
        elif claim["kind"] == "derived":
            theorem, premises = claim["derived"]["theorem"], claim["derived"]["from"]
            signature = re.search(rf"theorem {theorem}\b(.*?) :\n", proofs, re.S).group(1)
            holes = " ".join("_" for _ in _binders(signature))
            # by_comparison は，前提のあとに，値の比較（Lean が計算で決める）を 1 つ渡す
            compared = " (by decide +kernel)" if claim["derived"].get("by_comparison") else ""
            derived[name] = [f"theorem {name}_holds : {statement} := {theorem} {holes} " + " ".join(_proof(claims[i]) for i in premises) + compared,
                             f"#print axioms {name}_holds"]
            if refutation := claim["derived"].get("refutation"):
                derived[name] += [f"theorem {name}_fails : ¬ ({statement}) := {refutation} {holes} " + " ".join(_proof(claims[i]) for i in premises) + compared,
                                  f"#print axioms {name}_fails"]
            # 前提が 1 つ偽なら偽。h から各前提を取り出す式は、連言なら並びから決まる。そうでなければ paths に書く
            paths = claim["derived"].get("paths")
            if paths or re.search(r"\b[CR]\d\d\b.*∧", claim["proposition"].split(":=", 1)[1], re.S):
                parts = [paths[i] if paths else "h" + (".1" if n == 0 else ".2" * n + (".1" if n < len(premises) - 1 else ""))
                         for n, i in enumerate(premises)]
                derived[name] += [f"theorem {name}_fails : ¬ ({statement}) := fun h => by first "
                                  + " ".join(f"| exact (proved% {premise}_fails) {part}" for premise, part in zip(premises, parts)),
                                  f"#print axioms {name}_fails"]
        else:
            lines += [f"theorem {name}_holds : {statement} := by decide +kernel",
                      f"theorem {name}_fails : ¬ ({statement}) := by decide +kernel",
                      f"#print axioms {name}_holds", f"#print axioms {name}_fails"]
    # 導く claims は、derived_order の順（前提が先）に置く
    return axioms + lines + [line for name in record["derived_order"] if name in derived for line in derived[name]]


def read_axioms(lean_output: str) -> dict[str, list[str] | None]:
    """定理ごとの、依存する公理。証明が通らなかった定理は sorryAx に依存する。出力に無い定理は None。"""
    flat = re.sub(r"\s+", " ", lean_output)
    short = lambda name: name.removeprefix("Spec.")
    axioms = {short(name): [] for name in re.findall(r"'([\w.]+)' does not depend on any axioms", flat)}
    axioms |= {short(name): [short(axiom) for axiom in listed.split(", ")]
               for name, listed in re.findall(r"'([\w.]+)' depends on axioms: \[([^\]]*)\]", flat)}
    return axioms


def judge(record: dict, axioms: dict, errors: dict[str, str]) -> dict[str, dict]:
    """claim ごとの結果。真か偽かは、通った定理で決まる。前提が欠けた claim は inconclusive にする。"""
    claims = {claim["id"]: claim for claim in record["claims"]}
    declared = {f"{claim['id']}_axiom" for claim in record["claims"] if claim["kind"] == "axiom"}
    allowed = set(record["axioms"]) | declared
    results = {}

    def passed(name: str) -> list[str] | None:
        used = axioms.get(name)
        return used if used is not None and "sorryAx" not in used and set(used) <= allowed else None

    for claim in record["claims"]:
        name = claim["id"]
        lacking = sorted({a["name"] for a in claim["arguments"]} & set(errors))
        if claim["kind"] == "axiom":
            results[name] = {"status": "unverifiable", "reason": claim["unverifiable"],
                             "axiom": f"{name}_axiom" if axioms.get(f"{name}_axiom") is not None else None}
        elif lacking:
            results[name] = {"status": "unverified", "reason": "値が取れない: " + "、".join(f"{n}（{errors[n]}）" for n in lacking)}
        elif (used := passed(f"{name}_holds")) is not None:
            results[name] = {"status": "verified", "verdict": "真", "axioms": sorted(used)}
        elif (used := passed(f"{name}_fails")) is not None:
            results[name] = {"status": "verified", "verdict": "偽", "axioms": sorted(used)}
        else:
            results[name] = {"status": "inconclusive"}
    # inconclusive の理由: 成り立たなかった前提
    for claim in record["claims"]:
        result = results[claim["id"]]
        if result["status"] != "inconclusive":
            continue
        failed = [i for i in claim.get("derived", {}).get("from", [])
                  if not (results[i]["status"] == "unverifiable" and results[i]["axiom"]) and results[i].get("verdict") != "真"]
        result["reason"] = ("成り立たなかった前提: " + "、".join(failed)) if failed else "真の定理も偽の定理も通らなかった"
    # 信頼性の伝播: C の下にある信頼性条件（下の C の分も含む）の判定を集める。C そのものの判定は変えない
    def below(parent: str) -> list[str]:
        return [i for claim in record["claims"] if claim["parent"] == parent
                for i in ([claim["id"]] if claim["id"].startswith("R") else below(claim["id"]))]
    for claim in record["claims"]:
        conditions = below(claim["id"])
        if not conditions:
            continue
        false = [i for i in conditions if results[i].get("verdict") == "偽"]
        unverifiable = [i for i in conditions if results[i]["status"] == "unverifiable"]
        unknown = [i for i in conditions if results[i].get("verdict") != "真" and i not in false and i not in unverifiable]
        results[claim["id"]]["reliability"] = {"status": "偽" if false else "不明" if unknown else "真",
                                               "false": false, "unknown": unknown, "unverifiable": unverifiable}
    return results


def write_theorems(record: dict, results: dict, available: set[str]) -> None:
    """判定が付いた命題を、真なら定理、偽なら否定の定理として Theorems.lean に書く。"""
    keep = {f"{name}_{'holds' if result['verdict'] == '真' else 'fails'}" for name, result in results.items() if "verdict" in result}
    lines = HEADER + ["/-! 各命題の判定。parse_claims.py が生成する。手で編集しない。 -/"]
    for line in candidates(record, available):
        theorem = re.match(r"theorem (\w+)", line)
        if line.startswith("axiom ") or (theorem and theorem.group(1) in keep):
            lines.append(line)
    (LEAN / "Theorems.lean").write_text("\n".join(lines) + "\n", encoding="utf-8")

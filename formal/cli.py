"""ワークフローが呼ぶ入口。

  python formal/cli.py run full|sanity      宣言（claims.json）が指定する commit を取り出し、その中身だけで実験を実行する
  python formal/cli.py execute full|sanity  データを用意し、実験を実行し、観測したものを run-output/ に集める（取り出した commit の中で呼ばれる）
  python formal/cli.py lean                 claims.json の claims の形式化から、Spec.lean を書き出す
  python formal/cli.py verify full|sanity   変数の値を検証器から取り、Lean で各 claim を判定し、結果をスキーマに書く
"""
import hashlib
import json
import math
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

FORMAL = Path(__file__).parent
RUN_OUTPUT = Path("run-output")
SCHEMA = FORMAL / "claims.json"
EXECUTION = Path("execution")
THREAD_COUNT_VARIABLES = ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]


def run(mode: str) -> None:
    commit = re.search(r'commit := "([0-9a-f]{40})"',
                       "\n".join(claim["definitions"] for claim in json.loads(SCHEMA.read_text(encoding="utf-8"))["claims"])).group(1)
    subprocess.run(["git", "worktree", "add", "--detach", str(EXECUTION), commit], check=True)
    subprocess.run(["python3", "formal/cli.py", "execute", mode], cwd=EXECUTION, check=True)
    shutil.rmtree(RUN_OUTPUT, ignore_errors=True)
    shutil.copytree(EXECUTION / RUN_OUTPUT, RUN_OUTPUT)
    # 取り出した commit の番号と、取り出した後に書き換えたファイルの有無は、実験コードとは別に記録する
    head = subprocess.run(["git", "-C", str(EXECUTION), "describe", "--always", "--abbrev=40", "--dirty", "--exclude", "*"],
                          check=True, capture_output=True, text=True).stdout.strip()
    _write("repository_commit.json", {"commit": head})


def _write(name: str, value) -> None:
    (RUN_OUTPUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _prepare_dataset(dataset: dict, mode: str) -> dict:
    """データのファイルを、実験が読む場所に用意する。試運転では、同じ形の乱数の表を書く（本番のデータで先に実験しないため）。"""
    path = Path(dataset["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode == "sanity":
        generator = random.Random(0)
        shape = dataset["sanity"]
        rows = ["\t".join(shape["columns"])] + ["\t".join(f"{generator.gauss(100.0, 20.0):.1f}" for _ in shape["columns"])
                                                 for _ in range(shape["sampleCount"])]
        path.write_text("\n".join(rows) + "\n")
        location = f"sanity:{dataset['name']}"
    else:
        location = dataset["location"]
        path.write_bytes(urllib.request.urlopen(location).read() if "://" in location else Path(location).read_bytes())
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    return {"name": dataset["name"], "location": location, "checksum": hashlib.sha256(path.read_bytes()).hexdigest(),
            "sampleCount": len(lines) - 1, "columns": lines[0].split()}


def _gpu_names() -> list[str]:
    if not shutil.which("nvidia-smi"):
        return []
    listed = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True).stdout
    return [line.strip() for line in listed.splitlines() if line.strip()]


def _environment() -> dict:
    """計算機の OS、CPU、メモリ、GPU。実験コードではなく、ここで測る。"""
    release = dict(line.split("=", 1) for line in Path("/etc/os-release").read_text().splitlines() if "=" in line)
    processors = Path("/proc/cpuinfo").read_text().strip().split("\n\n")
    fields = [dict((key.strip(), value.strip()) for key, value in (line.split(":", 1) for line in processor.splitlines() if ":" in line))
              for processor in processors]
    return {"osName": release["NAME"].strip('"'), "osVersion": release["VERSION_ID"].strip('"'), "kernelRelease": platform.release(),
            "cpuModel": fields[0].get("model name", ""), "cpuArchitecture": platform.machine(),
            "physicalCoreCount": len({(field.get("physical id"), field.get("core id")) for field in fields}),
            "logicalCpuCount": os.cpu_count(),
            # メモリは実測が公称をわずかに下回るので、GiB の端数を切り上げる
            "memoryGibibytes": math.ceil(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30),
            "gpuNames": _gpu_names(), "nodeCount": 1}


def _process_tree(root: int) -> list[int]:
    parents = {}
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                parents[int(entry.name)] = int((entry / "stat").read_text().rsplit(")", 1)[1].split()[1])
            except (OSError, IndexError):
                pass
    tree, frontier = [root], [root]
    while frontier:
        frontier = [pid for pid, parent in parents.items() if parent in frontier]
        tree += frontier
    return tree


def _status(pid: int) -> dict:
    try:
        return dict(line.split(":", 1) for line in Path(f"/proc/{pid}/status").read_text().splitlines())
    except OSError:
        return {}


def _gpu_process_ids() -> set[int]:
    if not shutil.which("nvidia-smi"):
        return set()
    listed = subprocess.run(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"], capture_output=True, text=True).stdout
    return {int(line) for line in listed.split() if line.isdigit()}


def _run_and_monitor(command: list[str], environment: dict) -> dict:
    """実験のプロセスを起動し、終わるまで、プロセスの数、スレッドの数、メモリ使用量、GPU を使うプロセスの数を測る。"""
    process = subprocess.Popen(command, env=environment)
    peak = {"peakMemoryMebibytes": 0, "peakThreadCount": 0, "peakProcessCount": 0, "peakGpuProcessCount": 0}
    while True:
        finished, status, usage = os.wait4(process.pid, os.WNOHANG)
        if finished:
            break
        statuses = [status for status in map(_status, _process_tree(process.pid)) if "Threads" in status]
        memory = max((int(status.get("VmRSS", "0 kB").split()[0]) for status in statuses), default=0)
        peak["peakMemoryMebibytes"] = max(peak["peakMemoryMebibytes"], math.ceil(memory / 1024))
        peak["peakThreadCount"] = max(peak["peakThreadCount"], sum(int(status["Threads"]) for status in statuses))
        peak["peakProcessCount"] = max(peak["peakProcessCount"], len(statuses))
        peak["peakGpuProcessCount"] = max(peak["peakGpuProcessCount"], len(_gpu_process_ids() & set(_process_tree(process.pid))))
        time.sleep(0.01)
    if status != 0:
        sys.exit(f"実験のコマンドが失敗した: {command}")
    # ru_maxrss は KiB。終了時に OS が報告する、実験のプロセスの最大のメモリ使用量
    return {"final": {"maxMemoryMebibytes": math.ceil(usage.ru_maxrss / 1024)}, "sampled": peak}


def execute(mode: str) -> None:
    config = json.loads((FORMAL / "execution.json").read_text(encoding="utf-8"))
    shutil.rmtree(RUN_OUTPUT, ignore_errors=True)
    RUN_OUTPUT.mkdir()
    _write("prepared.json", [_prepare_dataset(dataset, mode) for dataset in config["datasets"]])
    subprocess.run(config["setup_command"], check=True)

    # 並列数は、スレッドの数を決める環境変数と、使える GPU の指定で渡す
    parallelism = config["parallelism"]
    variables = {name: str(parallelism["threadCount"]) for name in THREAD_COUNT_VARIABLES}
    variables["CUDA_VISIBLE_DEVICES"] = ",".join(str(n) for n in range(parallelism["gpuCount"]))
    calls = RUN_OUTPUT / "observed_calls.json"
    observing = {"PYTHONPATH": str((FORMAL / "observe").resolve()), "OBSERVED_FUNCTIONS": json.dumps(config["observed_functions"]),
                 "OBSERVED_CALLS_PATH": str(calls.resolve())}
    usage = _run_and_monitor(config["command"], os.environ | variables | observing)
    if not calls.exists():
        sys.exit("関数の呼び出しの記録が書かれていない")
    _write("usage.json", usage | {"configured": parallelism})
    _write("environment.json", _environment())

    python = config["command"][0]
    language = subprocess.run([python, "-c", "import platform; print(platform.python_implementation(), platform.python_version())"],
                              check=True, capture_output=True, text=True).stdout.strip()
    installed = subprocess.run([python, "-c", "import importlib.metadata, json; print(json.dumps(sorted([d.metadata['Name'].lower(), d.version] "
                                              "for d in importlib.metadata.distributions())))"],
                               check=True, capture_output=True, text=True).stdout
    _write("code.json", {"language": language, "dependencies": json.loads(installed), "setupCommand": config["setup_command"],
                         "command": config["command"], "environmentVariables": sorted(map(list, variables.items()))})
    for path in config["outputs"]:
        target = RUN_OUTPUT / "outputs" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def write_schema(record: dict) -> None:
    import parse_claims
    # 有理数（Fraction）は "分子/分母" の文字列で書く。Values.lean を作るときに有理数に戻る
    SCHEMA.write_text(json.dumps(parse_claims.stored(record), ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def lean() -> None:
    import parse_claims
    parse_claims.write_spec(parse_claims.load_schema())


def verify(mode: str) -> None:
    """検証器の値と判定の結果を、スキーマの verified と result に書き足す。"""
    import parse_claims
    repository = os.environ.get("GITHUB_REPOSITORY") or subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
        check=True, capture_output=True, text=True).stdout.strip()
    record = parse_claims.load_schema()
    parse_claims.write_spec(record)

    values, errors = parse_claims.query_values(record, repository, mode)
    for name, value in values.items():
        record["variables"][name]["verified"] = {"value": value, "mode": mode, "verify_run": os.environ.get("GITHUB_RUN_ID")}
    for name, reason in errors.items():
        print(f"値が取れない {name}: {reason}")
    parse_claims.write_values(record)
    lean = FORMAL / "lean"
    subprocess.run(["lake", "build", "Spec", "Proofs", "Values"], cwd=lean, check=True)

    available = set(values)
    path = lean / "Candidates.lean"
    path.write_text("\n".join(parse_claims.HEADER + parse_claims.candidates(record, available)) + "\n", encoding="utf-8")
    output = subprocess.run(["lake", "env", "lean", path.name], cwd=lean, capture_output=True, text=True).stdout
    path.unlink()
    results = parse_claims.judge(record, parse_claims.read_axioms(output), errors)
    for claim in record["claims"]:
        claim["result"] = results[claim["id"]]
    parse_claims.write_theorems(record, results, available)
    write_schema(record)
    for name, result in results.items():
        print(f"{name}: {result['status']} {result.get('verdict', '')}" + (f"（{result['reason']}）" if "reason" in result else "")
              + (f" 信頼性: {result['reliability']['status']}" if "reliability" in result else ""))
    # 真か偽か inconclusive かは研究の結果。検証として失敗なのは、未検証の claim か、公理が宣言されていない claim があるときだけ
    if any(result["status"] == "unverified" or (result["status"] == "unverifiable" and result["axiom"] is None)
           for result in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    command, arguments = sys.argv[1], sys.argv[2:]
    {"run": run, "execute": execute, "lean": lean, "verify": verify}[command](*arguments)

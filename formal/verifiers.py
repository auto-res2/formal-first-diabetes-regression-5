"""検証器。確かめてから値を返す。claims の形は知らない。

問い合わせは (repository, mode, 変数名, **args) を受ける。mode は "full"（本番）か "sanity"（試運転）。
値の元になる run は、その mode の成功した最新の run。番号は claims に書かない。
"""
import functools
import hashlib
import io
import json
import subprocess
import zipfile
from fractions import Fraction

BRANCH = "main"
EXPERIMENT_WORKFLOW = "run_experiment.yml"
ARTIFACT = "run-output"
OUTPUT_PATH = "outputs/results/metrics.json"
OBSERVED_CALLS_PATH = "observed_calls.json"
PREPARED_PATH = "prepared.json"


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


@functools.cache
def _runs(repository: str, mode: str) -> list[dict]:
    """実験のワークフローの、その mode の run（失敗したものも含む）。新しい順。mode は起動時の入力で、run の名前の末尾に入っている。"""
    # ponytail: run が 100 件を超えたら、ページをめくる必要がある
    runs = json.loads(_gh("api", f"repos/{repository}/actions/workflows/{EXPERIMENT_WORKFLOW}/runs?branch={BRANCH}&per_page=100"))
    return [run for run in runs["workflow_runs"] if run["display_title"].split()[-1] == mode]


def _evidence_run(repository: str, mode: str) -> dict:
    succeeded = [run for run in _runs(repository, mode) if run["conclusion"] == "success"]
    if not succeeded:
        raise ValueError(f"成功した {mode} の run が無い")
    return succeeded[0]


@functools.cache
def _artifact(repository: str, run: int) -> zipfile.ZipFile:
    """artifact がその run のもので、中身が GitHub の記録した digest と一致することを確かめて開く。"""
    artifacts = json.loads(_gh("api", f"repos/{repository}/actions/runs/{run}/artifacts"))["artifacts"]
    matches = [a for a in artifacts if a["name"] == ARTIFACT and not a["expired"]]
    if len(matches) != 1:
        raise ValueError(f"run {run} に artifact {ARTIFACT!r} が {len(matches)} 個ある")
    archive = subprocess.run(["gh", "api", f"repos/{repository}/actions/artifacts/{matches[0]['id']}/zip"],
                             check=True, capture_output=True).stdout
    if "sha256:" + hashlib.sha256(archive).hexdigest() != matches[0]["digest"]:
        raise ValueError(f"artifact {ARTIFACT!r} の中身が、GitHub の記録した digest と一致しない")
    return zipfile.ZipFile(io.BytesIO(archive))


def _read(repository: str, mode: str, path: str) -> bytes:
    return _artifact(repository, _evidence_run(repository, mode)["id"]).read(path)


def _at(value, keys: list):
    for key in keys:
        value = value[key]
    return value


def _sha256(value) -> str:
    """実験のプロセスの中の記録（formal/observe/sitecustomize.py）と同じ表記（JSON）での SHA-256。"""
    return hashlib.sha256(json.dumps(value).encode()).hexdigest()


def _calls(repository: str, mode: str, function: str) -> list[dict]:
    """実験のプロセスの中で記録された、その関数の呼び出し。"""
    return [call for call in json.loads(_read(repository, mode, OBSERVED_CALLS_PATH)) if call["function"] == function]


def _only_call(repository: str, mode: str, function: str) -> dict:
    calls = _calls(repository, mode, function)
    if len(calls) != 1:
        raise ValueError(f"{function} の呼び出しが {len(calls)} 回ある")
    return calls[0]


def experiment_output(repository: str, mode: str, variable: str, key: str):
    """実験の出力の、キーの値。小数は書かれた桁のままの有理数で読む。"""
    return json.loads(_read(repository, mode, OUTPUT_PATH), parse_float=Fraction)[key]


def artifact_json(repository: str, mode: str, variable: str, path: str, keys: list = ()):
    """artifact にある JSON の、キーをたどった先の値。"""
    return _at(json.loads(_read(repository, mode, path)), keys)


def observed_calls(repository: str, mode: str, variable: str, function: str, with_model_parameters: bool = False) -> list[dict]:
    """その関数の呼び出しごとの、関数の名前と、渡された引数（設定値）。メソッドでは、モデルのパラメータも設定値に含められる。"""
    return [{"functionName": call["function"],
             "arguments": (call.get("modelParameters", []) if with_model_parameters else []) + call["settings"]}
            for call in _calls(repository, mode, function)]


def observed_call_values(repository: str, mode: str, variable: str, function: str, paths: list[list]) -> list:
    """その関数の呼び出しごとの、記録の中の値（paths の順）。すべての呼び出しの分を 1 つの並びにする。"""
    return [_at(call, keys) for call in _calls(repository, mode, function) for keys in paths]


def observed_call_lists(repository: str, mode: str, variable: str, function: str, paths: list[list]) -> list[list]:
    """その関数の呼び出しごとに、記録の中の並び（paths の順）をつなげたもの。"""
    return [[item for keys in paths for item in _at(call, keys)] for call in _calls(repository, mode, function)]


def observed_only_call_value(repository: str, mode: str, variable: str, function: str, keys: list):
    """1 回だけ呼ばれた関数の、記録の中の値。"""
    return _at(_only_call(repository, mode, function), keys)


def observed_call_settings(repository: str, mode: str, variable: str, function: str, setting: str) -> list[str]:
    """その関数の呼び出しごとの、名前で指定した設定値。"""
    return [value for call in _calls(repository, mode, function) for name, value in call["settings"] if name == setting]


def prepared_file_column_checksums(repository: str, mode: str, variable: str, paths: list[str]) -> list[list[str]]:
    """用意したファイル（1 行目は列の名前）ごとの、列ごとの値の SHA-256。"""
    checksums = []
    for path in paths:
        rows = [[float(value) for value in line.split()] for line in _read(repository, mode, path).decode().splitlines()[1:] if line.strip()]
        checksums.append([_sha256(list(column)) for column in zip(*rows)])
    return checksums


def observed_column_names(repository: str, mode: str, variable: str, loader: str, consumer: str, arrays: list[str], single: bool = False):
    """読み込んだ表の列のうち、次の関数に渡された配列の列になっているものの名前。列は、値の SHA-256 で対応させる。"""
    names = json.loads(_read(repository, mode, PREPARED_PATH))[0]["columns"]
    loaded = _only_call(repository, mode, loader)["returned"][0]["columnSha256s"]
    if len(set(loaded)) != len(loaded):
        raise ValueError("読み込んだ表に、値がすべて同じ列がある")
    passed = [checksum for array in arrays for checksum in _only_call(repository, mode, consumer)["arrays"][array]["columnSha256s"]]
    found = [names[loaded.index(checksum)] for checksum in passed]
    return found[0] if single else found


def _row_keys(arrays: list[dict]) -> list[tuple]:
    """行ごとの、配列をまたいだ SHA-256 の組。"""
    return list(zip(*(array["rowSha256s"] for array in arrays)))


def observed_row_indexes(repository: str, mode: str, variable: str, source_function: str, source_arrays: list[str],
                         target_function: str, target_arrays: list[str] = (), target_returned: list[int] = ()) -> list[int]:
    """ある関数が受け取った（または返した）行が、元の関数が受け取った行の何番目か。行は、値の SHA-256 で対応させる。"""
    source = _only_call(repository, mode, source_function)
    keys = _row_keys([source["arrays"][name] for name in source_arrays])
    if len(set(keys)) != len(keys):
        raise ValueError("元の行に、値がすべて同じ行がある")
    target = _only_call(repository, mode, target_function)
    return [keys.index(key) for key in _row_keys([target["arrays"][name] for name in target_arrays]
                                                  + [target["returned"][n] for n in target_returned])]


QUERIES = {"GitHub": {f.__name__: f for f in (
    experiment_output, artifact_json, observed_calls, observed_call_values, observed_call_lists, observed_only_call_value,
    observed_call_settings, prepared_file_column_checksums, observed_column_names, observed_row_indexes)}}

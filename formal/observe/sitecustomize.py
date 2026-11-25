"""実験のプロセスの中で、指定された関数の呼び出しを記録する。実験コードは、これを呼ばない。

実験を起動する側（formal/cli.py）が、PYTHONPATH にこのディレクトリを入れ、
OBSERVED_FUNCTIONS（関数の名前の JSON の並び）と OBSERVED_CALLS_PATH（記録の書き出し先）を渡す。
"""
import atexit
import functools
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path

CALLS: list[dict] = []
_inside_observed_call = False


def _sha256(value) -> str:
    """値を JSON で表したものの SHA-256。配列は Python の数の並び（tolist）にしてから渡す。"""
    return hashlib.sha256(json.dumps(value).encode()).hexdigest()


def _array(array) -> dict:
    rows = array.tolist()
    # 1 次元の配列は、それ自体を 1 つの列として扱う。2 次元の表の列と、同じ表記で比べられる
    columns = array.T.tolist() if array.ndim == 2 else [rows]
    return {"shape": list(array.shape), "sha256": _sha256(rows),
            "rowSha256s": [_sha256(row) for row in rows], "columnSha256s": [_sha256(column) for column in columns]}


def _model_state(model) -> str:
    """当てはめで決まった属性（名前が _ で終わるもの）の SHA-256。当てはめる前は、属性が無い。"""
    fitted = {name: value.tolist() if hasattr(value, "tolist") else value
              for name, value in sorted(vars(model).items()) if name.endswith("_")}
    return _sha256(fitted)


def _returned(result):
    import numpy
    if isinstance(result, numpy.ndarray):
        return [_array(result)]
    if isinstance(result, (list, tuple)) and all(isinstance(item, numpy.ndarray) for item in result):
        return [_array(item) for item in result]
    if isinstance(result, (float, numpy.floating)):
        return {"value": repr(float(result))}
    return None


def _observed(name: str, function):
    signature = inspect.signature(function)

    @functools.wraps(function)
    def observed(*args, **kwargs):
        global _inside_observed_call
        # 記録する関数が内部で別の記録する関数を呼んでも、外側の呼び出しだけを記録する
        if _inside_observed_call:
            return function(*args, **kwargs)
        import numpy
        record = {"function": name, "settings": [], "arrays": {}, "files": {}}
        model = None
        for parameter, value in signature.bind(*args, **kwargs).arguments.items():
            named = [(f"{parameter}[{n}]", item) for n, item in enumerate(value)] if isinstance(value, tuple) else [(parameter, value)]
            for label, item in named:
                if parameter == "self":
                    model = item
                    record["modelParameters"] = [[key, repr(setting)] for key, setting in sorted(item.get_params().items())]
                    record["modelStateBefore"] = _model_state(item)
                elif isinstance(item, numpy.ndarray):
                    record["arrays"][label] = _array(item)
                elif isinstance(item, (str, os.PathLike)) and Path(item).is_file():
                    record["files"][label] = {"path": str(item), "sha256": hashlib.sha256(Path(item).read_bytes()).hexdigest()}
                else:
                    record["settings"].append([label, repr(item)])
        _inside_observed_call = True
        try:
            result = function(*args, **kwargs)
        finally:
            _inside_observed_call = False
        record["returned"] = _returned(result)
        if model is not None:
            record["modelStateAfter"] = _model_state(model)
        CALLS.append(record)
        return result
    return observed


def _install(name: str) -> None:
    """名前（モジュール.関数、または モジュール.クラス.メソッド）が指すものを、記録する版に差し替える。"""
    parts = name.split(".")
    for split in range(len(parts) - 1, 0, -1):
        try:
            owner = importlib.import_module(".".join(parts[:split]))
        except ImportError:
            continue
        for attribute in parts[split:-1]:
            owner = getattr(owner, attribute)
        setattr(owner, parts[-1], _observed(name, getattr(owner, parts[-1])))
        return
    raise ImportError(f"記録する関数が見つからない: {name}")


if "OBSERVED_FUNCTIONS" in os.environ and "OBSERVED_CALLS_PATH" in os.environ:
    for _name in json.loads(os.environ["OBSERVED_FUNCTIONS"]):
        _install(_name)
    atexit.register(lambda: Path(os.environ["OBSERVED_CALLS_PATH"]).write_text(json.dumps(CALLS, indent=1) + "\n"))

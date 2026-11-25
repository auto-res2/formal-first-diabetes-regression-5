"""スキーマ（claims.json）の検証済みの値と判定を、論文が読み込む LaTeX のマクロに書き出す。

論文の各文は claims の ID を付けて書く。ここで、文面が前提にしている判定と、すべての claims が論文に出てくることを確かめる。
使い方: python formal/write_report_values.py <スキーマを置いた commit>
"""
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

FORMAL = Path(__file__).parent
REPORT = FORMAL.parent / "report"
# 論文の文面が前提にしている判定。これ以外の検証できる claims は、すべて真として書いている
WRITTEN_AS = {"C01": "偽", "R33": "偽", "Reliable.C09": "偽", "Reliable.C02": "偽", "Reliable.C01": "偽"}

schema_text = (FORMAL / "claims.json").read_text(encoding="utf-8")
schema = json.loads(schema_text)
claims = {claim["id"]: claim for claim in schema["claims"]}
for claim in schema["claims"]:
    result = claim["result"]
    expected = WRITTEN_AS.get(claim["id"], "真")
    if result["status"] == "verified" and result["verdict"] != expected:
        sys.exit(f"{claim['id']} の判定は {result['verdict']} だが、論文は {expected} として書かれている")
    if result["status"] not in ("verified", "unverifiable"):
        sys.exit(f"{claim['id']} は {result['status']} で、論文に書けない")
report = (REPORT / "report.tex").read_text(encoding="utf-8")
missing = [claim["id"] for claim in schema["claims"] if f"\\cid{{{claim['id']}}}" not in report]
if missing:
    sys.exit(f"論文に出てこない claims: {missing}")

value = {name: variable["verified"]["value"] for name, variable in schema["variables"].items()}
declared_environment = claims["C09"]["definitions"]
declared = lambda field: re.search(rf'{field} := "?([^",}}\n]+)"?', declared_environment).group(1)
macros = {
    "SchemaCommit": sys.argv[1],
    "NSamples": value["preparedDatasets"][0]["sampleCount"], "NFeatures": len(value["observedFeatureColumns"]),
    "NTrain": len(value["observedTrainIndex"]), "NTest": len(value["observedTestIndex"]),
    "TestMse": f"{float(Fraction(value['outputTestMse'])):.2f}",
    "DeclaredCpuModel": declared("cpuModel"), "DeclaredKernelRelease": declared("kernelRelease"),
    "ObservedCpuModel": value["observedEnvironment"]["cpuModel"], "ObservedKernelRelease": value["observedEnvironment"]["kernelRelease"],
    "LogicalCpuCount": value["observedEnvironment"]["logicalCpuCount"], "MemoryGib": value["observedEnvironment"]["memoryGibibytes"],
    "MemoryUsageLimit": declared("memoryUsageLimitMebibytes"), "MaxMemoryUsage": value["finalMaxMemoryMebibytes"],
    "RepositoryCommit": value["observedCommit"][:7],
}
lines = [f"\\newcommand{{\\{name}}}{{{text}}}" for name, text in macros.items()]
# claims と値の、スキーマの中の行。論文から、その行へリンクする
schema_lines = schema_text.splitlines()
for claim in schema["claims"]:
    line = next(i for i, text in enumerate(schema_lines, 1) if text.strip() == f'"id": "{claim["id"]}",')
    lines.append(f"\\expandafter\\def\\csname line{claim['id']}\\endcsname{{{line}}}")
for name in re.findall(r"\\val\{(\w+)\}", report):
    line = next(i for i, text in enumerate(schema_lines, 1) if text.startswith(f'    "{name}": {{'))
    lines.append(f"\\expandafter\\def\\csname line{name}\\endcsname{{{line}}}")
(REPORT / "values.tex").write_text("\n".join(dict.fromkeys(lines)) + "\n", encoding="utf-8")

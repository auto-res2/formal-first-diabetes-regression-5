# formal-first-diabetes-regression-5

メインの claim を導く手順の宣言（C）と、宣言ごとの信頼性条件（R）を、実験の前に Lean で宣言する試行。

研究の指示: Efron らの糖尿病データセットに線形回帰モデルを当てはめ，テストデータに対する MSE が 3400 を下回るかを調べる

```
C01（メインの claim）: 出力された MSE < 3400
└─ C02（再現性条件）: 宣言した手順で、MSE が値として定まる
    ├─ C03 データセットのダウンロード   ─ R01〜R03
    ├─ C04 データセットの読み込み       ─ R04〜R09
    ├─ C05 データセットの分割           ─ R10〜R17
    ├─ C06 学習・フィッティング         ─ R18〜R21
    ├─ C07 推論・予測                   ─ R22〜R26
    ├─ C08 評価指標の計算               ─ R27〜R32
    ├─ C09 ハードウェア・OS             ─ R33〜R34
    └─ C10 コード・依存ライブラリ       ─ R35〜R37
```

- C と C の線は、下の値や処理で、上の値や真偽が決まること
- C と R の線は、その C に当てる信頼性条件。R が偽でも C は変わらず、その C の信頼性が偽になる
- 各 C の信頼性は、Lean の命題 `Reliable.C`。最下層の C では、その C の R の連言。上の C では、下の C の `Reliable` の連言
  - `Reliable.C03 = R01 ∧ R02 ∧ R03`、`Reliable.C02 = Reliable.C03 ∧ … ∧ Reliable.C10`、`Reliable.C01 = Reliable.C02`
- 最後に言うことは 2 つ。`main_claim`（C01。メインの claim の成立）と、`main_reliability`（`Reliable.C01`。メインの claim に対する信頼性条件の成立）
- 「関数は、信頼できる」などの、検証器が無い R は、公理として置く（検証不能）

## 結果

本番は 1 回実行した（[実験の run](https://github.com/auto-res2/formal-first-diabetes-regression-5/actions/runs/45671266200)、[検証の run](https://github.com/auto-res2/formal-first-diabetes-regression-5/actions/runs/45671354628)）。

- `main_claim`: C01（出力された MSE < 3400）は偽。テストデータに対する MSE は 3424.26
- `main_reliability`: `Reliable.C01` は偽。計算環境の宣言（C09）が、信頼性条件を満たさなかった
  - R33 が偽。宣言した CPU とカーネルの版（Intel Xeon 6975P-C、7.0.0-1014-aws。試運転で読んだ値）に対して、本番の runner は AMD EPYC 9V74、7.0.0-1017-azure だった
  - これを受けて `Reliable.C09`、`Reliable.C02`、`Reliable.C01` が偽
- ほかの宣言（C03〜C08、C10）は、信頼性条件を満たした。`Reliable.C04`〜`Reliable.C08` は、検証器の無い条件（公理に置いた R04、R10、R15、R17、R18、R22、R27）に依存する
- 57 claims: 真 45、偽 5、検証不能 7
- 検証された値は [`formal/lean/Values.lean`](formal/lean/Values.lean)、各 claim の判定の定理は [`formal/lean/Theorems.lean`](formal/lean/Theorems.lean)。どちらも検証の run が生成したもの
- 論文: [`report/report.pdf`](report/report.pdf)（各文に、元になった claims の ID を付けた）

## 置いてあるもの

- スキーマ: [`formal/claims.json`](formal/claims.json)（claims の形式化、値の取り方。検証の結果もここに書く）
  - claim 1 つが Lean の命題 1 つで、命題の名前が claim の ID
  - `formal/lean/Spec.lean` は、ここから生成する（commit しない）
- 証明に必要なもの: [`formal/lean/Proofs.lean`](formal/lean/Proofs.lean)
- 実験コード: [`src/run_experiment.py`](src/run_experiment.py)（記録を取る処理は持たない）
- 観測: 実験コードの外で行う
  - [`formal/observe/sitecustomize.py`](formal/observe/sitecustomize.py): 実験のプロセスの中で、宣言された関数の呼び出し（引数、渡されたデータのチェックサム、返した値）を記録する
  - [`formal/cli.py`](formal/cli.py) の `execute`: データの用意、計算機の計測、実行中のプロセスの計測、言語と依存ライブラリの版の記録
- 実行の設定: [`formal/execution.json`](formal/execution.json)
- 検証器: [`formal/verifiers.py`](formal/verifiers.py)（run の artifact から値を取る）

## 流れ

1. 実行に関するもの（実験コード、依存の固定、実行の設定、観測の処理）を commit する
2. その commit の番号を、宣言（C10）に書いて commit する
3. 実験と検証を、GitHub Actions で実行する。実験は、宣言が指定する commit を取り出して、その中身だけで実行する

```bash
python3 formal/cli.py lean                        # claims.json から Spec.lean を書き出す（手元で Lean を通すとき）
gh workflow run run_experiment.yml -f mode=full   # 実験（GitHub Actions）
gh workflow run verify_claims.yml -f mode=full    # 検証（GitHub Actions）。結果は artifact の claims.json
```

`mode=sanity` は試運転。データは、同じ形の乱数の表に置き換える（本番のデータで先に実験しないため）。

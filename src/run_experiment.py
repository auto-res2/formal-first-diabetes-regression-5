"""糖尿病データセットに線形回帰モデルを当てはめ、テストデータに対する MSE を出力する。

データのファイルは、実行の前に用意されている。使った関数や渡したデータの記録は、このコードでは取らない。
"""
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

DATA_PATH = Path("data/diabetes.tab.txt")
RESULTS_PATH = Path("results/metrics.json")


def main() -> None:
    table = np.loadtxt(DATA_PATH, skiprows=1)
    features, target = table[:, :-1], table[:, -1]
    train_features, test_features, train_target, test_target = train_test_split(
        features, target, test_size=0.2, random_state=0)
    model = LinearRegression()
    model.fit(train_features, train_target)
    prediction = model.predict(test_features)
    test_mse = mean_squared_error(test_target, prediction)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps({"testMse": float(test_mse)}) + "\n")


if __name__ == "__main__":
    main()

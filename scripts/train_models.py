# ML 모델 학습 후 joblib·성능 지표 저장
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import ML_SAMPLE_ROWS
from src.ml_models import train_models
from src.paths import MODELS, PROCESSED

SAMPLE_PATH = PROCESSED / "ml_train_sample.csv"
METRICS_PATH = PROCESSED / "model_metrics.json"


# 학습용 샘플 CSV가 있으면 로드, 없으면 ml_train.csv에서 무작위 추출 후 저장
def build_sample(n: int = ML_SAMPLE_ROWS) -> pd.DataFrame:
    if SAMPLE_PATH.exists():
        return pd.read_csv(SAMPLE_PATH, encoding="utf-8")
    chunk = pd.read_csv(PROCESSED / "ml_train.csv", encoding="utf-8", nrows=600_000)
    sample = chunk.sample(n=min(n, len(chunk)), random_state=42)
    sample.to_csv(SAMPLE_PATH, index=False, encoding="utf-8")
    return sample


# Linear·RF·RF Tuned 학습 후 모델 파일·비교 지표 저장
def main():
    MODELS.mkdir(exist_ok=True)
    df = build_sample()
    print("Training on", len(df), "rows...")
    results = train_models(df, max_rows=len(df))
    print(results["comparison"].to_string())
    print("Best:", results["best_params"])
    # 3종 모델을 models/ 디렉터리에 직렬화
    joblib.dump(results["linear"], MODELS / "linear_regression.joblib")
    joblib.dump(results["rf"], MODELS / "random_forest.joblib")
    joblib.dump(results["tuned"], MODELS / "rf_tuned.joblib")
    METRICS_PATH.write_text(
        json.dumps(
            {
                "comparison": results["comparison"].to_dict(orient="records"),
                "best_params": results["best_params"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

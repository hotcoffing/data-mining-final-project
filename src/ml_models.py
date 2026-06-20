import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import ML_MAX_ROWS, ML_RANDOM_STATE, ML_TEST_DAYS

CAT_FEATURES = ["season"]
NUM_FEATURES = ["hour", "dow", "is_weekend", "month", "cluster_id"]
TARGET = "bike_count_mean"


def _preprocessor() -> ColumnTransformer:
    """수치 표준화 + 계절 원핫 인코딩."""
    return ColumnTransformer(
        [
            ("num", StandardScaler(), NUM_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CAT_FEATURES,
            ),
        ]
    )


def build_linear_pipeline() -> Pipeline:
    return Pipeline([("prep", _preprocessor()), ("model", LinearRegression())])


def build_rf_pipeline(n_estimators: int = 50) -> Pipeline:
    return Pipeline(
        [
            ("prep", _preprocessor()),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=n_estimators, random_state=ML_RANDOM_STATE, n_jobs=-1
                ),
            ),
        ]
    )


def time_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """월별로 마지막 N일을 테스트, 나머지를 학습으로 분리 (시계열 누수 방지)."""
    df = df.copy()
    df["cluster_id"] = pd.to_numeric(df["cluster_id"], errors="coerce").fillna(-1).astype(int)
    df["date"] = pd.to_datetime(df["date"])
    test_parts, train_parts = [], []
    for _, grp in df.groupby(df["date"].dt.to_period("M")):
        grp = grp.sort_values("date")
        unique_dates = sorted(grp["date"].dt.date.unique())
        if len(unique_dates) <= ML_TEST_DAYS:
            split = max(1, len(unique_dates) // 2)
            test_dates = set(unique_dates[-split:])
        else:
            test_dates = set(unique_dates[-ML_TEST_DAYS:])
        test_parts.append(grp[grp["date"].dt.date.isin(test_dates)])
        train_parts.append(grp[~grp["date"].dt.date.isin(test_dates)])
    train = pd.concat(train_parts, ignore_index=True) if train_parts else df.iloc[:0]
    test = pd.concat(test_parts, ignore_index=True) if test_parts else df
    if len(train) == 0:
        train, test = train_test_split(df, test_size=0.2, random_state=ML_RANDOM_STATE)
    return train, test


def evaluate(y_true, y_pred) -> dict:
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": mean_squared_error(y_true, y_pred) ** 0.5,
        "R2": r2_score(y_true, y_pred),
    }


def train_models(df: pd.DataFrame, max_rows: int = ML_MAX_ROWS) -> dict:
    """선형회귀·RF·GridSearch RF 3종 학습 및 성능 비교."""
    if len(df) > max_rows:
        df = df.sample(n=max_rows, random_state=ML_RANDOM_STATE)
    train, test = time_split(df)
    x_train, y_train = train[NUM_FEATURES + CAT_FEATURES], train[TARGET]
    x_test, y_test = test[NUM_FEATURES + CAT_FEATURES], test[TARGET]

    linear = build_linear_pipeline()
    linear.fit(x_train, y_train)
    linear_metrics = evaluate(y_test, linear.predict(x_test))

    rf = build_rf_pipeline()
    rf.fit(x_train, y_train)
    rf_metrics = evaluate(y_test, rf.predict(x_test))

    param_grid = {
        "model__n_estimators": [100, 150],
        "model__max_depth": [None, 16],
        "model__min_samples_leaf": [1, 3],
    }
    grid = GridSearchCV(
        build_rf_pipeline(),
        param_grid,
        cv=2,
        scoring="neg_mean_absolute_error",
        n_jobs=-1,
    )
    grid.fit(x_train, y_train)
    tuned = grid.best_estimator_
    tuned_metrics = evaluate(y_test, tuned.predict(x_test))

    comparison = pd.DataFrame(
        [
            {"model": "Linear Regression", **linear_metrics},
            {"model": "Random Forest", **rf_metrics},
            {"model": "RF Tuned", **tuned_metrics},
        ]
    )

    return {
        "train": train,
        "test": test,
        "linear": linear,
        "rf": rf,
        "tuned": tuned,
        "comparison": comparison,
        "best_params": grid.best_params_,
        "models_dict": {
            "Linear Regression": linear,
            "Random Forest": rf,
            "RF Tuned": tuned,
        },
    }

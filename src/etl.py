import pandas as pd

from src.config import AVAILABILITY_ENCODING, ETL_CHUNK_SIZE, SEASON_MAP
from src.paths import AVAILABILITY_MONTHS, PROCESSED, availability_file
from src.stations import norm_station_no


def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """일시에서 hour·요일·주말·계절 특성 파생."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    dt = pd.to_datetime(df["date"])
    df["month"] = dt.dt.month
    df["dow"] = dt.dt.dayofweek
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["season"] = df["month"].map(SEASON_MAP)
    return df


def _process_chunk(chunk: pd.DataFrame, station_keys: set) -> pd.DataFrame:
    chunk.columns = [c.strip('"') for c in chunk.columns]
    out = pd.DataFrame(
        {
            "date": chunk.iloc[:, 0].str.strip('"'),
            "station_no_norm": chunk.iloc[:, 1].map(norm_station_no),
            "station_name": chunk.iloc[:, 2].astype(str).str.strip(),
            "hour": pd.to_numeric(chunk.iloc[:, 3], errors="coerce").astype("Int64"),
            "bike_count": pd.to_numeric(chunk.iloc[:, 4], errors="coerce").fillna(0).astype(int),
        }
    )
    return out[out["station_no_norm"].isin(station_keys)]


def load_availability_month(
    month: str,
    stations: pd.DataFrame,
    chunksize: int = ETL_CHUNK_SIZE,
) -> pd.DataFrame:
    path = availability_file(month)
    station_keys = set(stations["station_no_norm"])
    parts = []
    for chunk in pd.read_csv(path, encoding=AVAILABILITY_ENCODING, chunksize=chunksize):
        parts.append(_process_chunk(chunk, station_keys))
    df = pd.concat(parts, ignore_index=True)
    df = df.merge(
        stations[
            ["station_no_norm", "station_name", "district", "lat", "lng", "cluster_id"]
        ],
        on="station_no_norm",
        how="left",
        suffixes=("_avail", "_st"),
    )
    return _add_time_features(df)


def aggregate_zone_hour(station_hour: pd.DataFrame) -> pd.DataFrame:
    """대여소×시간 → 구역×시간 평균 거치대수 집계 (ML 학습 테이블)."""
    g = station_hour.groupby(["date", "hour", "cluster_id"], as_index=False)
    zone = g.agg(
        bike_count_mean=("bike_count", "mean"),
        bike_count_max=("bike_count", "max"),
        availability_rate=("bike_count", lambda s: (s > 0).mean()),
    )
    meta = station_hour.groupby(["date", "hour", "cluster_id"], as_index=False).first()
    for col in ["month", "dow", "is_weekend", "season"]:
        zone[col] = meta[col]
    return zone


def run_etl(stations: pd.DataFrame, months=AVAILABILITY_MONTHS, rebuild: bool = True) -> dict:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    paths = {
        "station_hour": PROCESSED / "availability_station_hour.csv",
        "zone_hour": PROCESSED / "availability_zone_hour.csv",
        "ml_train": PROCESSED / "ml_train.csv",
    }
    if not rebuild and all(p.exists() for p in paths.values()):
        return {k: pd.read_csv(v, encoding="utf-8") for k, v in paths.items()}

    frames = [load_availability_month(m, stations) for m in months]
    station_hour = pd.concat(frames, ignore_index=True)
    station_hour.to_csv(paths["station_hour"], index=False, encoding="utf-8")

    zone_hour = aggregate_zone_hour(station_hour)
    zone_hour.to_csv(paths["zone_hour"], index=False, encoding="utf-8")
    zone_hour.to_csv(paths["ml_train"], index=False, encoding="utf-8")

    return {
        "station_hour": station_hour,
        "zone_hour": zone_hour,
        "ml_train": zone_hour,
    }

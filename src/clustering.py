import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from src.config import CLUSTER_EPS_M, EARTH_RADIUS_M
from src.paths import PROCESSED
from src.stations import haversine_m


def cluster_stations(stations: pd.DataFrame) -> pd.DataFrame:
    """DBSCAN(haversine)으로 약 200m 구역 군집화."""
    df = stations.copy()
    coords = np.radians(df[["lat", "lng"]].values)
    clustering = DBSCAN(
        eps=CLUSTER_EPS_M / EARTH_RADIUS_M,
        min_samples=1,
        metric="haversine",
        algorithm="ball_tree",
    )
    df["cluster_id"] = clustering.fit_predict(coords)

    centers = (
        df.groupby("cluster_id")[["lat", "lng"]]
        .mean()
        .rename(columns={"lat": "cluster_lat", "lng": "cluster_lng"})
    )
    return df.merge(centers, left_on="cluster_id", right_index=True)


def cluster_diameter_stats(stations: pd.DataFrame) -> pd.DataFrame:
    """구역별 최대 직경 통계 (리포트용)."""
    rows = []
    for cid, grp in stations.groupby("cluster_id"):
        lats, lngs = grp["lat"].values, grp["lng"].values
        max_d = 0.0
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                max_d = max(max_d, haversine_m(lats[i], lngs[i], lats[j], lngs[j]))
        rows.append(
            {"cluster_id": cid, "n_stations": len(grp), "max_diameter_m": max_d}
        )
    return pd.DataFrame(rows)


def save_stations(stations: pd.DataFrame) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    stations.to_csv(PROCESSED / "stations.csv", index=False, encoding="utf-8")

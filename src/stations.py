import re

import numpy as np
import pandas as pd

from src.config import EARTH_RADIUS_M
from src.paths import station_xlsx


# 대여소번호 정규화 (앞자리 0 제거, 숫자만 추출)
def norm_station_no(value) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip().strip('"')
    digits = re.sub(r"\D", "", s)
    return digits.lstrip("0") or "0"


# 2025 대여소 XLSX 로드 및 컬럼 정제
def load_stations(xlsx_path=None) -> pd.DataFrame:
    path = xlsx_path or station_xlsx()
    raw = pd.read_excel(path, header=None)
    df = raw.iloc[5:].copy()  # 상단 메타 행 스킵
    df.columns = [
        "station_no",
        "station_name",
        "district",
        "address",
        "lat",
        "lng",
        "installed_at",
        "lcd_slots",
        "qr_slots",
        "op_mode",
    ]
    df = df.dropna(subset=["station_no"]).copy()
    df["station_name"] = df["station_name"].astype(str).str.strip()
    df["station_no_norm"] = df["station_no"].map(norm_station_no)
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
    df["qr_slots"] = pd.to_numeric(df["qr_slots"], errors="coerce")
    return df.dropna(subset=["lat", "lng"]).reset_index(drop=True)


# 가용성 샘플과 대여소 마스터 조인 매칭 통계
def join_match_stats(avail_sample: pd.DataFrame, stations: pd.DataFrame) -> dict:
    a_keys = set(avail_sample["station_no_norm"].unique())
    b_keys = set(stations["station_no_norm"].unique())
    matched = a_keys & b_keys
    return {
        "avail_unique": len(a_keys),
        "station_unique": len(b_keys),
        "matched": len(matched),
        "match_rate_pct": round(len(matched) / max(len(a_keys), 1) * 100, 2),
        "avail_only": len(a_keys - b_keys),
        "station_only": len(b_keys - a_keys),
    }


# 두 좌표 간 haversine 직선거리 (m)
def haversine_m(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlon / 2) ** 2
    return float(2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(a)))


# 주어진 좌표에서 가장 가까운 대여소 1곳 반환
def nearest_station(stations: pd.DataFrame, lat: float, lng: float) -> pd.Series:
    dists = stations.apply(
        lambda r: haversine_m(lat, lng, r["lat"], r["lng"]), axis=1
    )
    idx = dists.idxmin()
    row = stations.loc[idx].copy()
    row["distance_m"] = dists.loc[idx]
    return row


# 좌표를 가장 가까운 구역(cluster)에 매핑하고 중심까지 거리 반환
def assign_cluster(stations: pd.DataFrame, lat: float, lng: float) -> tuple[int, float]:
    if "cluster_id" not in stations.columns:
        raise ValueError("stations must have cluster_id")
    centers = (
        stations.groupby("cluster_id")[["cluster_lat", "cluster_lng"]]
        .first()
        .reset_index()
    )
    dists = centers.apply(
        lambda r: haversine_m(lat, lng, r["cluster_lat"], r["cluster_lng"]), axis=1
    )
    idx = dists.idxmin()
    return int(centers.loc[idx, "cluster_id"]), float(dists.loc[idx])

from datetime import datetime, timedelta

import pandas as pd

from src.config import (
    CLUSTER_WARN_M,
    FEASIBILITY_MODEL,
    MAX_RENT_RETRIES,
    MIN_BIKES_DEFAULT,
    RENT_RETRY_HOURS,
    SEASON_MAP,
)
from src.kakao_map import geocode_or_coords, get_duration
from src.stations import assign_cluster, nearest_station


def _features_for(rent_time: datetime, cluster_id: int) -> pd.DataFrame:
    """대여 시각·구역으로 ML 입력 특성 1행 생성."""
    return pd.DataFrame(
        [
            {
                "hour": rent_time.hour,
                "dow": rent_time.weekday(),
                "is_weekend": int(rent_time.weekday() >= 5),
                "month": rent_time.month,
                "season": SEASON_MAP[rent_time.month],
                "cluster_id": int(cluster_id),
            }
        ]
    )


def _predict_all(models: dict, features: pd.DataFrame) -> dict[str, float]:
    return {name: float(pipe.predict(features)[0]) for name, pipe in models.items()}


def _feasibility_pred(preds: dict[str, float]) -> float:
    """판정용 예측값 — RF Tuned 우선, 없으면 최댓값 사용."""
    if FEASIBILITY_MODEL in preds:
        return preds[FEASIBILITY_MODEL]
    return max(preds.values())


def _retry_until_available(
    models: dict,
    rent_time: datetime,
    cluster_id: int,
    min_bikes: int,
) -> tuple[dict[str, float], datetime, int, bool]:
    """가용 대수 부족 시 대여 시각을 1시간씩 앞당겨 최대 N회 재예측."""
    rent_time_adjusted = False
    for attempt in range(MAX_RENT_RETRIES + 1):
        preds = _predict_all(models, _features_for(rent_time, cluster_id))
        if _feasibility_pred(preds) >= min_bikes:
            return preds, rent_time, attempt, rent_time_adjusted
        if attempt < MAX_RENT_RETRIES:
            rent_time -= timedelta(hours=RENT_RETRY_HOURS)
            rent_time_adjusted = True
    return preds, rent_time, MAX_RENT_RETRIES, rent_time_adjusted


def print_origin_prediction_summary(result: dict) -> None:
    preds = result["predictions"]
    avg_pred = sum(preds.values()) / len(preds)
    if not result["timing_feasible"]:
        status = "대여 어려움 (할당 시간 내 대여소 도착 불가)"
    elif result["feasible"]:
        status = "대여 가능"
    else:
        status = "대여 어려움 (예상 대수 부족)"
    print("=" * 52)
    print(f"출발 구역 ID: {result['origin_cluster']}")
    print(f"가장 가까운 대여소: {result['nearest_station']}")
    if result.get("origin_cluster_warning"):
        print(f"⚠ {result['origin_cluster_warning']}")
    print(f"할당 가능 소요시간: {result['available_minutes']:.0f}분")
    print(f"예상 도보 소요: {result['walk_sec']/60:.0f}분 ({result['walk_mode']})")
    print(f"예상 평균 거치대수: {avg_pred:.1f}대")
    for name, val in preds.items():
        print(f"  - {name}: {val:.1f}대")
    print(f"판정: {status}  ({FEASIBILITY_MODEL} 기준 {result['min_bikes']}대 이상)")
    print(f"권장 출발 시각: {result['depart_home']:%Y-%m-%d %H:%M}")
    print(f"예상 대여 시각(대여소 도착): {result['rent_time']:%Y-%m-%d %H:%M}")
    if result.get("rent_time_adjusted"):
        print(f"※ 가용성 부족으로 대여 시각을 {result['retry_count']}회 앞당겨 재계산했습니다.")
    if not result["feasible"] and result["timing_feasible"]:
        print("※ 해당 조건에서는 따릉이 대여가 어려울 수 있습니다.")
    print("=" * 52)


def predict_origin_rental(
    stations: pd.DataFrame,
    models: dict,
    origin_address: str | None,
    available_minutes: float,
    min_bikes: int = MIN_BIKES_DEFAULT,
    origin_lat: float | None = None,
    origin_lng: float | None = None,
    reference_time: datetime | None = None,
) -> dict:
    """출발지 주소·할당 시간으로 가장 가까운 구역 대여소 가용성 예측."""
    ref = reference_time or datetime.now()
    olat, olng, origin_mode = geocode_or_coords(origin_address, origin_lat, origin_lng)

    origin_cluster, origin_dist = assign_cluster(stations, olat, olng)
    cluster_stations = stations[stations["cluster_id"] == origin_cluster]
    near = nearest_station(cluster_stations, olat, olng)

    walk_sec, walk_mode = get_duration((olat, olng), (near["lat"], near["lng"]), "walk")
    timing_feasible = walk_sec <= available_minutes * 60

    rent_time = ref + timedelta(seconds=walk_sec)
    depart_home = ref

    preds, rent_time, retry_count, rent_time_adjusted = _retry_until_available(
        models, rent_time, origin_cluster, min_bikes
    )
    if rent_time_adjusted:
        depart_home = rent_time - timedelta(seconds=walk_sec)

    bikes_ok = _feasibility_pred(preds) >= min_bikes
    feasible = timing_feasible and bikes_ok

    origin_warning = None
    if origin_dist > CLUSTER_WARN_M:
        origin_warning = (
            f"출발지가 구역 중심에서 {origin_dist:.0f}m 떨어져 있습니다 ({CLUSTER_WARN_M}m 초과)."
        )

    return {
        "depart_home": depart_home,
        "rent_time": rent_time,
        "reference_time": ref,
        "available_minutes": available_minutes,
        "origin_cluster": origin_cluster,
        "origin_dist_m": origin_dist,
        "origin_cluster_warning": origin_warning,
        "nearest_station": near["station_name"],
        "nearest_station_lat": float(near["lat"]),
        "nearest_station_lng": float(near["lng"]),
        "origin_lat": olat,
        "origin_lng": olng,
        "walk_sec": walk_sec,
        "walk_mode": walk_mode,
        "geo_modes": {"origin": origin_mode},
        "predictions": preds,
        "feasible": feasible,
        "timing_feasible": timing_feasible,
        "bikes_feasible": bikes_ok,
        "min_bikes": min_bikes,
        "rent_time_adjusted": rent_time_adjusted,
        "retry_count": retry_count,
    }

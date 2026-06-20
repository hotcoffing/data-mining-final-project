import os

import requests
from dotenv import load_dotenv

from src.config import (
    BIKE_SPEED_KMH,
    KAKAO_GEOCODE_URL,
    KAKAO_MOBILITY_URL,
    KAKAO_REST_PLACEHOLDER,
    WALK_SPEED_KMH,
)
from src.stations import haversine_m

load_dotenv()

WALK_SPEED_MPS = WALK_SPEED_KMH * 1000 / 3600
BIKE_SPEED_MPS = BIKE_SPEED_KMH * 1000 / 3600


def _rest_api_key() -> str:
    return os.getenv("KAKAO_REST_API_KEY", "").strip()


def has_rest_api_key() -> bool:
    key = _rest_api_key()
    return bool(key and key != KAKAO_REST_PLACEHOLDER)


def _geocode_error_message(status_code: int, body: str = "") -> str:
    hints = [
        "1) developers.kakao.com → 제품 설정 → 카카오맵(로컬) 활성화",
        "2) REST API 키 사용 (JavaScript 키 아님)",
        "3) REST API 키 → 호출 허용 IP 비우거나 현재 PC IP 등록",
        "4) 클라이언트 시크릿 사용 중이면 비활성화",
    ]
    detail = f" (응답: {body[:200]})" if body else ""
    return (
        f"Kakao Local API {status_code} — 지오코딩 권한/설정 문제{detail}\n"
        + "\n".join(hints)
        + "\n\nNotebook 첫 셀 FORCE_COORD_MODE = True 로 좌표 Demo 실행 가능."
    )


def _mode_label(use_api: bool) -> str:
    return "Kakao API" if use_api else "Demo (haversine)"


def geocode(address: str) -> tuple[float, float, str]:
    key = _rest_api_key()
    if not key or key == KAKAO_REST_PLACEHOLDER:
        raise RuntimeError(
            "KAKAO_REST_API_KEY not set. .env에 REST API 키를 설정하거나 좌표 Demo를 사용하세요."
        )
    headers = {"Authorization": f"KakaoAK {key}"}
    resp = requests.get(
        KAKAO_GEOCODE_URL, headers=headers, params={"query": address}, timeout=10
    )
    if resp.status_code in (401, 403):
        raise RuntimeError(_geocode_error_message(resp.status_code, resp.text))
    resp.raise_for_status()
    docs = resp.json().get("documents", [])
    if not docs:
        raise ValueError(f"Address not found: {address}")
    doc = docs[0]
    return float(doc["y"]), float(doc["x"]), _mode_label(True)


def _demo_duration(
    origin: tuple[float, float], dest: tuple[float, float], mode: str
) -> float:
    dist = haversine_m(origin[0], origin[1], dest[0], dest[1])
    speed = WALK_SPEED_MPS if mode == "walk" else BIKE_SPEED_MPS
    return dist / speed


def _mobility_duration(origin: tuple[float, float], dest: tuple[float, float]) -> float | None:
    key = os.getenv("KAKAO_MOBILITY_API_KEY", "").strip()
    if not key:
        return None
    headers = {"Authorization": f"KakaoAK {key}", "Content-Type": "application/json"}
    params = {
        "origin": f"{origin[1]},{origin[0]}",
        "destination": f"{dest[1]},{dest[0]}",
        "priority": "RECOMMEND",
    }
    try:
        resp = requests.get(KAKAO_MOBILITY_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        routes = resp.json().get("routes", [])
        if not routes:
            return None
        return float(routes[0]["summary"]["duration"])
    except Exception:
        return None


def get_duration(
    origin: tuple[float, float],
    dest: tuple[float, float],
    mode: str = "walk",
) -> tuple[float, str]:
    api_sec = _mobility_duration(origin, dest)
    if api_sec is not None:
        return api_sec, _mode_label(True)
    return _demo_duration(origin, dest, mode), _mode_label(False)


def geocode_or_coords(
    address: str | None,
    lat: float | None,
    lng: float | None,
) -> tuple[float, float, str]:
    if lat is not None and lng is not None:
        return lat, lng, "Coordinates (direct)"
    if address:
        return geocode(address)
    raise ValueError("Provide address or lat/lng")

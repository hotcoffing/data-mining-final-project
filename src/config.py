# 프로젝트 전역 설정 상수

# 월 → season 매핑 (ML 특성·ETL 공통)
SEASON_MAP: dict[int, str] = {
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "fall", 10: "fall", 11: "fall",
}

# 공간 군집화·거리 계산
EARTH_RADIUS_M = 6371000.0
CLUSTER_EPS_M = 200  # DBSCAN 구역 반경 (m)
CLUSTER_DIAMETER_REPORT_M = 250  # 리포트용 직경 임계값 (m)
CLUSTER_WARN_M = 200  # 출발지-구역 중심 경고 거리 (m)

# Kakao API 미사용 시 Demo 이동 속도 (km/h)
WALK_SPEED_KMH = 4.5
BIKE_SPEED_KMH = 15

# 예측 판정·재시도
MIN_BIKES_DEFAULT = 1
MAX_RENT_RETRIES = 6
RENT_RETRY_HOURS = 1
FEASIBILITY_MODEL = "RF Tuned"  # 대여 가능 판정에 사용할 모델명

# ML 학습
ML_MAX_ROWS = 200_000
ML_SAMPLE_ROWS = 80_000
ML_RANDOM_STATE = 42
ML_TEST_DAYS = 7  # 월별 hold-out 테스트 일수

# ETL
ETL_CHUNK_SIZE = 100_000
JOIN_SAMPLE_ROWS = 80_000
AVAILABILITY_ENCODING = "cp949"

# Notebook 데모 기본값
DEMO_ADDRESS = "서울특별시 마포구 월드컵로 72"
DEMO_ORIGIN_LAT = 37.5556
DEMO_ORIGIN_LNG = 126.9106
DEMO_AVAILABLE_MINUTES = 30
DEMO_REF_TIME = "2024-04-15 08:00"

# Kakao API
KAKAO_REST_PLACEHOLDER = "your_rest_api_key_here"
KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KAKAO_MOBILITY_URL = "https://apis-navi.kakaomobility.com/v1/directions"

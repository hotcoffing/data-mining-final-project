# Project-wide configuration constants.

SEASON_MAP: dict[int, str] = {
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "fall", 10: "fall", 11: "fall",
}

EARTH_RADIUS_M = 6371000.0
CLUSTER_EPS_M = 200
CLUSTER_DIAMETER_REPORT_M = 250
CLUSTER_WARN_M = 200

WALK_SPEED_KMH = 4.5
BIKE_SPEED_KMH = 15

MIN_BIKES_DEFAULT = 1
MAX_RENT_RETRIES = 6
RENT_RETRY_HOURS = 1
FEASIBILITY_MODEL = "RF Tuned"

ML_MAX_ROWS = 200_000
ML_SAMPLE_ROWS = 80_000
ML_RANDOM_STATE = 42
ML_TEST_DAYS = 7

ETL_CHUNK_SIZE = 100_000
JOIN_SAMPLE_ROWS = 80_000
AVAILABILITY_ENCODING = "cp949"

DEMO_ADDRESS = "서울특별시 마포구 월드억로 72"
DEMO_ORIGIN_LAT = 37.5556
DEMO_ORIGIN_LNG = 126.9106
DEMO_AVAILABLE_MINUTES = 30
DEMO_REF_TIME = "2024-04-15 08:00"

KAKAO_REST_PLACEHOLDER = "your_rest_api_key_here"
KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KAKAO_MOBILITY_URL = "https://apis-navi.kakaomobility.com/v1/directions"

from pathlib import Path

# 프로젝트 루트·주요 디렉터리
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
DOCS = ROOT / "docs"

# ETL에 사용할 2024 가용성 월 (대표 3개월)
AVAILABILITY_MONTHS = ("2401", "2404", "2407")


# data/ 하위에서 키워드가 포함된 디렉터리 탐색
def find_subdir(keyword: str) -> Path:
    for d in DATA.iterdir():
        if d.is_dir() and keyword in d.name:
            return d
    raise FileNotFoundError(f"No data subdir matching: {keyword}")


# 2024년 대여가능 수량 CSV 디렉터리
def availability_dir() -> Path:
    return find_subdir("2024")


# 2025년 대여소 마스터 XLSX 경로 (25.12월 기준 우선)
def station_xlsx() -> Path:
    station_dir = find_subdir("2025")
    for f in station_dir.glob("*.xlsx"):
        if "25.12" in f.name or "12" in f.name:
            return f
    return sorted(station_dir.glob("*.xlsx"))[-1]


# 월별 가용성 CSV 파일 경로 (예: data_2401.csv)
def availability_file(month: str) -> Path:
    return availability_dir() / f"data_{month}.csv"

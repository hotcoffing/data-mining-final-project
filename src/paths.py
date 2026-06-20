from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
DOCS = ROOT / "docs"

AVAILABILITY_MONTHS = ("2401", "2404", "2407")


def find_subdir(keyword: str) -> Path:
    for d in DATA.iterdir():
        if d.is_dir() and keyword in d.name:
            return d
    raise FileNotFoundError(f"No data subdir matching: {keyword}")


def availability_dir() -> Path:
    return find_subdir("2024")


def station_xlsx() -> Path:
    station_dir = find_subdir("2025")
    for f in station_dir.glob("*.xlsx"):
        if "25.12" in f.name or "12" in f.name:
            return f
    return sorted(station_dir.glob("*.xlsx"))[-1]


def availability_file(month: str) -> Path:
    return availability_dir() / f"data_{month}.csv"

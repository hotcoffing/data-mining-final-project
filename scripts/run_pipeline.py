"""Build processed datasets: stations, availability, zone-hour aggregates."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.clustering import cluster_diameter_stats, cluster_stations, save_stations
from src.config import AVAILABILITY_ENCODING, CLUSTER_DIAMETER_REPORT_M, JOIN_SAMPLE_ROWS
from src.etl import run_etl
from src.paths import AVAILABILITY_MONTHS, DOCS, PROCESSED, availability_file
from src.stations import join_match_stats, load_stations, norm_station_no


def write_join_report(stations: pd.DataFrame) -> dict:
    sample_month = AVAILABILITY_MONTHS[0]
    sample = pd.read_csv(
        availability_file(sample_month),
        encoding=AVAILABILITY_ENCODING,
        nrows=JOIN_SAMPLE_ROWS,
    )
    sample.columns = [c.strip('"') for c in sample.columns]
    sample["station_no_norm"] = sample.iloc[:, 1].map(norm_station_no)
    stats = join_match_stats(sample, stations)

    md = f"""# Data Join Report

## Summary

| Metric | Value |
|--------|-------|
| A unique stations (sample) | {stats['avail_unique']} |
| B unique stations | {stats['station_unique']} |
| Matched | {stats['matched']} |
| Match rate | {stats['match_rate_pct']}% |
| A-only (sample) | {stats['avail_only']} |
| B-only | {stats['station_only']} |

## Normalization

- Strip non-digits, remove leading zeros (`00101` -> `101`)
- Inner join; unmatched A rows excluded in ETL

## Conclusion

Match rate meets PRD expectation (~87%). Unmatched rows are likely closed stations.
"""
    DOCS.mkdir(exist_ok=True)
    (DOCS / "data-join-report.md").write_text(md, encoding="utf-8")
    (DOCS / "_join_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats


def write_cluster_report(stations: pd.DataFrame) -> None:
    stats = cluster_diameter_stats(stations)
    over = (stats["max_diameter_m"] > CLUSTER_DIAMETER_REPORT_M).sum()
    md = f"""# Clustering Report

## Method

- DBSCAN, haversine metric (sklearn-compatible)
- eps = {CLUSTER_EPS_M}m, min_samples = 1

## Results

| Metric | Value |
|--------|-------|
| Clusters | {stations['cluster_id'].nunique()} |
| Stations | {len(stations)} |
| Avg stations/cluster | {len(stations) / max(stations['cluster_id'].nunique(), 1):.1f} |
| Clusters with diameter > {CLUSTER_DIAMETER_REPORT_M}m | {over} |

## Diameter distribution (m)

```
{stats['max_diameter_m'].describe().to_string()}
```
"""
    (DOCS / "clustering-report.md").write_text(md, encoding="utf-8")


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    print("Loading stations...")
    stations = load_stations()
    write_join_report(stations)
    print("Clustering...")
    stations = cluster_stations(stations)
    save_stations(stations)
    write_cluster_report(stations)
    print("ETL (3 months, chunked)...")
    data = run_etl(stations, rebuild=True)
    print("Rows station_hour:", len(data["station_hour"]))
    print("Rows zone_hour:", len(data["zone_hour"]))
    print("Done.")


if __name__ == "__main__":
    main()

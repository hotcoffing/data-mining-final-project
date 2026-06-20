# Clustering Report

## Method

- DBSCAN, haversine metric (sklearn-compatible)
- eps = 200m / 6371000 rad, min_samples = 1

## Results

| Metric | Value |
|--------|-------|
| Clusters | 1706 |
| Stations | 2799 |
| Avg stations/cluster | 1.6 |
| Clusters with diameter > 250m | 140 |

## Diameter distribution (m)

```
count    1706.000000
mean       66.549071
std       121.027773
min         0.000000
25%         0.000000
50%         0.000000
75%       111.089931
max       994.987919
```

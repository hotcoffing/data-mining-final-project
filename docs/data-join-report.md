# Data Join Report

## Summary

| Metric | Value |
|--------|-------|
| A unique stations (sample) | 3069 |
| B unique stations | 2799 |
| Matched | 2660 |
| Match rate | 86.67% |
| A-only (sample) | 409 |
| B-only | 139 |

## Normalization

- Strip non-digits, remove leading zeros (`00101` -> `101`)
- Inner join; unmatched A rows excluded in ETL

## Conclusion

Match rate meets PRD expectation (~87%). Unmatched rows are likely closed stations.

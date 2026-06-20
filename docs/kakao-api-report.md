# Kakao API Report

## Endpoints

| Step | API | URL |
|------|-----|-----|
| Geocoding | Local REST | `https://dapi.kakao.com/v2/local/search/address.json` |
| Directions | Mobility | `https://apis-navi.kakaomobility.com/v1/directions` |

## Environment

- `KAKAO_REST_API_KEY` - required for address geocoding
- `KAKAO_MOBILITY_API_KEY` - optional; enables route duration API

## Demo fallback

When Mobility key is missing or API fails:

| Segment | Speed |
|---------|-------|
| Walk (home to station) | 4.5 km/h |
| Bike (station to dest) | 15 km/h |

Duration = haversine distance / speed.

## Implementation

See `src/kakao_map.py`: `geocode()`, `get_duration()`, `geocode_or_coords()`.

## Key policy

API keys are loaded from `.env`. If keys are needed, ask the project owner.

## Notebook usage

- Default demo uses coordinates (Mangwon to Gwanghwamun) without API keys
- Set `USE_ADDRESS=True` in notebook when `KAKAO_REST_API_KEY` is configured

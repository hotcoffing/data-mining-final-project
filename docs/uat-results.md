# UAT Results

## UAT-1 Prediction output

Sample: Mangwon (37.5556, 126.9106) -> Gwanghwamun (37.5759, 126.9769), arrival 2024-04-15 09:00

```
Recommended depart home: 2024-04-15 08:34:52
Predictions (bike count): Linear=11.8, RF=17.0, RF Tuned=17.8
Mode: Demo haversine (coordinates, no API key)
```

## UAT-2 Clustering visualization

- `data/processed/stations.csv` with 1706 clusters (DBSCAN ~200m)
- Folium map in Notebook section 3

## UAT-3 Model comparison

| Model | MAE | RMSE | R2 |
|-------|-----|------|-----|
| Linear Regression | 7.318 | 9.786 | 0.009 |
| Random Forest | 5.167 | 7.384 | 0.436 |
| RF Tuned | 5.015 | 7.119 | 0.475 |

Best params: `max_depth=None, min_samples_leaf=3, n_estimators=150`

## UAT-4 Kakao map pipeline

- `src/kakao_map.py`: geocoding + Mobility API + demo fallback
- Demo mode verified; set `.env` for address-based input

## UAT-5 Reproducibility

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py
python scripts/train_models.py
jupyter notebook notebooks/ddareungi_departure_prediction.ipynb
```

## UAT-6 Encoding

UTF-8 verified for project documents and generated outputs.

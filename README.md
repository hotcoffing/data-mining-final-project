# 집에서 언제 출발해야 따릉이를 탈 수 있을까?

데이터마이닝 기말 프로젝트 — 군집화, 회귀, Random Forest, 카카오맵 API

## Quick start

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py
python scripts/train_models.py
jupyter notebook notebooks/ddareungi_departure_prediction.ipynb
```

## 입력

- **출발 주소** + **할당 가능 소요시간(분)**
- REST API 키 없거나 IP 미등록 시 좌표 Demo 자동 대체

## 문서

- `prd.md`, `techspec.md`, `tasks.md`
- `docs/uat-experience.md` — UAT 경험 요약 (레포트용)
- `docs/` — 조인·군집·API·UAT 리포트

## 구조

```
src/
  config.py      # 공통 상수
  stations.py    # 대여소 로드·구역 매핑
  clustering.py  # DBSCAN 군집화
  etl.py         # 가용성 ETL
  ml_models.py   # ML 학습
  predict.py     # 가용성 예측
  kakao_map.py   # 지오코딩·소요시간
scripts/
  run_pipeline.py
  train_models.py
  generate_notebook.py  # Notebook 재생성용
```

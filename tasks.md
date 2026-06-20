# Tasks: 집에서 언제 출발해야 따릉이를 탈 수 있을까?

| 항목 | 내용 |
|------|------|
| 문서 버전 | 0.2 (승인) |
| 작성일 | 2026-06-18 |
| 상위 문서 | `prd.md` v0.2, `techspec.md` v0.2 |
| 상태 | **승인 완료** — 구현 완료 |

---

## 1. 운영 규칙

### 1.1 진행 순서

- 태스크는 **ID 오름차순**으로 진행한다.
- 선행 태스크 AC **전부 충족** 후 다음 태스크 착수.
- **검수**: 태스크 완료마다 담당자(메인/서브)가 AC 자가 점검 → 메인 세션이 통합 검수.

### 1.2 인코딩 AC (공통)

모든 태스크에 아래 AC가 **암묵적 포함**이다. 표에 **ENC** 로 중복 표기한다.

| AC-ENC | Cursor에서 해당 태스크가 생성·수정한 한글 파일이 **깨짐 없이** 표시된다. |
| AC-ENC2 | 텍스트 산출물은 **UTF-8** 저장 (`Path.read_text(encoding="utf-8")` 통과). |

### 1.3 서브에이전트 ↔ `docs/` 매핑

| 태스크 | 서브에이전트 | `docs/` 산출물 |
|--------|-------------|----------------|
| T-02 | 권장 | `docs/data-join-report.md` |
| T-04 | 권장 | `docs/clustering-report.md` |
| T-11 | 권장 | `docs/kakao-api-report.md` |
| T-15 | 메인 | `docs/uat-results.md` |

서브에이전트 완료 시 **UTF-8 마크다운 보고서 필수**. 메인 세션이 보고서를 읽고 Notebook·AC에 반영.

---

## 2. 태스크 목록 요약

| ID | 제목 | 담당 | 선행 | UAT |
|----|------|------|------|-----|
| T-01 | 프로젝트 scaffold | 메인 | ? | UAT-5, UAT-6 |
| T-02 | 대여소 로드·조인 검증 | 서브 | T-01 | ? |
| T-03 | ETL ? 가용 데이터 3개월 | 메인 | T-02 | ? |
| T-04 | 군집화 (~200m) | 서브 | T-03 | UAT-2 |
| T-05 | 구역×시간 집계·Feature Table | 메인 | T-04 | ML-02 |
| T-06 | Notebook EDA 섹션 | 메인 | T-05 | ? |
| T-07 | Train/Test 분할 | 메인 | T-05 | ? |
| T-08 | 선형 회귀 | 메인 | T-07 | UAT-3 |
| T-09 | Random Forest | 메인 | T-07 | UAT-3 |
| T-10 | RF 하이퍼파라미터 튜닝 | 메인 | T-09 | UAT-3 |
| T-11 | 카카오 API 헬퍼 | 서브 | T-01 | UAT-4 |
| T-12 | 모델 비교·시각화 | 메인 | T-08, T-09, T-10 | UAT-3 |
| T-13 | 사용자 입력·예측 파이프라인 | 메인 | T-05, T-11, T-12 | UAT-1 |
| T-14 | Notebook 통합·재현성 | 메인 | T-06~T-13 | UAT-5 |
| T-15 | UAT 결과 기록 | 메인 | T-14 | UAT-1~6 |

---

## 3. 태스크 상세

### T-01 ? 프로젝트 scaffold

**목표**: techspec §1.3, §9, §10에 따른 디렉터리·환경·보안 기반 마련.

**산출물**

- `requirements.txt`
- `.env.example`
- `.gitignore` (`.env`, `data/processed/` optional cache, `models/`, `__pycache__`)
- 디렉터리: `notebooks/`, `data/processed/`, `models/`, `docs/`, `src/` (선택)

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | `requirements.txt`에 techspec §9 패키지 포함 |
| AC-02 | `.env.example`에 `KAKAO_REST_API_KEY`, `KAKAO_MOBILITY_API_KEY` placeholder |
| AC-03 | `.gitignore`에 `.env` 포함 |
| AC-04 | ENC, ENC2 |

---

### T-02 ? 대여소 로드·조인 검증

**목표**: B(25.12월 XLSX) 파싱 및 A↔B `station_no_norm` 조인 가능성 검증.

**담당**: **서브에이전트** → `docs/data-join-report.md`

**작업**

1. XLSX `iloc[5:]` 파싱 (techspec §3.2)
2. `norm_station_no` 구현·단위 테스트 수준 검증
3. `data_2401.csv` 샘플(≥5만 행)과 inner join 매칭률 산출
4. 미매칭 건수·원인(폐쇄 추정) 요약

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | `docs/data-join-report.md`에 매칭률·미매칭 수·정규화 규칙 기록 |
| AC-02 | 매칭률 ?85% 이상 또는 PRD §4.5(?87%)와 ±5%p 이내 설명 |
| AC-03 | `src/` 또는 Notebook에 재사용 가능 `norm_station_no`, `load_stations()` 초안 |
| AC-04 | ENC, ENC2 |

**선행**: T-01

---

### T-03 ? ETL: 가용 데이터 3개월

**목표**: `data_2401`, `data_2404`, `data_2407` 청크 ETL → processed CSV.

**작업**

1. `cp949` + `chunksize=100_000` 로 월별 순차 처리
2. inner join stations (T-02) ? 미매칭 제외
3. 파생: `date`, `hour`, `month`, `dow`, `is_weekend`, `season`
4. 출력: `data/processed/availability_station_hour.csv` (UTF-8)
5. `REBUILD` 플래그로 캐시 재사용

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | 3개월 데이터 포함, 전월 **전량 한 번에** `read_csv` 없음 |
| AC-02 | `availability_station_hour.csv` UTF-8, 필수 컬럼 §3.4 준수 |
| AC-03 | 행 수·대여소 수·월별 분포 stdout/보고 |
| AC-04 | ENC, ENC2 |

**선행**: T-02

---

### T-04 ? 군집화 (~200m)

**목표**: ML-01 ? AgglomerativeClustering haversine 200m 구역.

**담당**: **서브에이전트** → `docs/clustering-report.md`

**작업**

1. `stations.csv`에 `cluster_id`, `cluster_lat`, `cluster_lng` 부여
2. `distance_threshold=200/6371000`, `metric=haversine`, `linkage=average`
3. 구역 직경 histogram · cluster 수 · 평균 대여소/구역
4. folium 지도 HTML 또는 Notebook 내 표시 준비

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | `data/processed/stations.csv` (UTF-8)에 cluster 컬럼 존재 |
| AC-02 | `docs/clustering-report.md`에 cluster 수, 직경 분포, 200m 근거 |
| AC-03 | 대부분 구역 max pairwise ≤ 250m (이상치 구역 목록 명시) |
| AC-04 | ENC, ENC2 |

**선행**: T-03

---

### T-05 ? 구역×시간 집계·Feature Table

**목표**: ML-02 ? `availability_zone_hour.csv`, `ml_train.csv`.

**작업**

1. `(date, hour, cluster_id)` 집계 → `bike_count_mean`, `bike_count_max`, `availability_rate`
2. `ml_train.csv`: feature + target `bike_count_mean`
3. techspec §6.2 feature 컬럼 포함

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | `availability_zone_hour.csv`, `ml_train.csv` UTF-8 저장 |
| AC-02 | 타깃 = `bike_count_mean` (techspec §6.1) |
| AC-03 | 구역·시간별 집계 샘플 5행 Notebook/문서 출력 |
| AC-04 | ENC, ENC2 |

**선행**: T-04

---

### T-06 ? Notebook EDA 섹션

**목표**: techspec §8 섹션 2 ? 월/시간대별 가용 분포.

**산출물**: `notebooks/ddareungi_departure_prediction.ipynb` EDA 셀

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | 시간대별·요일별 `bike_count_mean` 시각화 ≥2종 |
| AC-02 | `bike_count=0` 비율 보고 |
| AC-03 | Notebook JSON UTF-8, 한글 마크다운 셀 정상 |
| AC-04 | ENC, ENC2 |

**선행**: T-05

---

### T-07 ? Train/Test 분할

**목표**: techspec §6.3 ? 월별 **마지막 7일** test.

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | 각 월(2401, 2404, 2407) 마지막 7일이 test에만 포함 |
| AC-02 | train/test 행 수·기간 Notebook에 출력 |
| AC-03 | test date가 train max date 이후 (누수 없음) |
| AC-04 | ENC, ENC2 |

**선행**: T-05

---

### T-08 ? 선형 회귀 (ML-03)

**목표**: `LinearRegression` + Pipeline(scaler + one-hot).

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | test set MAE, RMSE, R² 출력 |
| AC-02 | `models/linear_regression.joblib` 저장 (optional) |
| AC-03 | Notebook 섹션 6 해당 |
| AC-04 | ENC, ENC2 |

**선행**: T-07

---

### T-09 ? Random Forest (ML-04)

**목표**: `RandomForestRegressor(n_estimators=100, random_state=42)`.

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | T-08과 **동일 test set**·동일 feature |
| AC-02 | MAE, RMSE, R² 출력 |
| AC-03 | `models/random_forest.joblib` 저장 (optional) |
| AC-04 | ENC, ENC2 |

**선행**: T-07

---

### T-10 ? RF 하이퍼파라미터 튜닝 (ML-05)

**목표**: GridSearchCV, techspec §6.4 param_grid.

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | 튜닝 **전**(T-09) vs **후** MAE/RMSE/R² **비교 표** |
| AC-02 | best params Notebook 출력 |
| AC-03 | `cv=3`, `scoring=neg_mean_absolute_error` |
| AC-04 | ENC, ENC2 |

**선행**: T-09

---

### T-11 ? 카카오 API 헬퍼

**목표**: MAP-01 ? 지오코딩·소요시간·Demo fallback.

**담당**: **서브에이전트** → `docs/kakao-api-report.md`

**작업**

1. `geocode(address)` ? Local REST API
2. `get_duration(origin, dest, mode)` ? Mobility 또는 haversine fallback
3. `.env` 로드; **키 없으면 사용자에게 요청** (techspec §7.1)
4. API/Demo 모드 stdout 표시

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | `docs/kakao-api-report.md`에 엔드포인트·fallback·샘플 응답 |
| AC-02 | `src/kakao_map.py` 또는 Notebook §10 함수화 |
| AC-03 | Demo 모드만으로도 파이프라인 실행 가능 |
| AC-04 | API 키 하드코딩 **금지** |
| AC-05 | ENC, ENC2 |

**선행**: T-01

---

### T-12 ? 모델 비교·시각화

**목표**: UAT-3 ? 3모델 성능 비교 차트.

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | Linear / RF / Tuned RF MAE·RMSE·R² **한 표** |
| AC-02 | bar chart 또는 유사 시각화 1종 이상 |
| AC-03 | Notebook 섹션 9 |
| AC-04 | ENC, ENC2 |

**선행**: T-08, T-09, T-10

---

### T-13 ? 사용자 입력·예측 파이프라인

**목표**: NB-01, UAT-1 ? §7.4 권장 출발 시각.

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | `ipywidgets` 또는 `input()` 으로 출발·도착·희망 도착 시각 입력 |
| AC-02 | PRD §5.2 예시(망원역→광화문) 또는 동등 시나리오 1건 **실행 가능** |
| AC-03 | 출력: 권장 출발 시각, 예상 대여 시각, 3모델 예측 거치대수 |
| AC-04 | 소요시간(도보+자전거) 출력, API/Demo 모드 표시 |
| AC-05 | ENC, ENC2 |

**선행**: T-05, T-11, T-12

---

### T-14 ? Notebook 통합·재현성

**목표**: techspec §8 전 섹션(0~12) 통합, top-to-bottom 실행.

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-01 | `notebooks/ddareungi_departure_prediction.ipynb` 섹션 0~12 구성 |
| AC-02 | `pip install -r requirements.txt` 후 **Restart & Run All** 성공 (API 키 없을 때 Demo 모드) |
| AC-03 | `REBUILD=False` 시 processed 캐시로 2회차 실행 시간 단축 확인 |
| AC-04 | folium 구역 지도 표시 (UAT-2) |
| AC-05 | ENC, ENC2 |

**선행**: T-06, T-13

---

### T-15 ? UAT 결과 기록

**목표**: `docs/uat-results.md` (UTF-8) ? PRD §7 전 항목.

**Acceptance Criteria**

| ID | 기준 |
|----|------|
| AC-UAT1 | 샘플 입력 예측 결과 스크린샷 또는 텍스트 로그 |
| AC-UAT2 | 군집화 지도 확인 기록 |
| AC-UAT3 | 3모델 성능 비교 기록 |
| AC-UAT4 | 카카오/Demo 소요시간 반영 기록 |
| AC-UAT5 | requirements 재현 절차·결과 |
| AC-UAT6 | prd/techspec/tasks/docs 한글 표시 확인 |
| AC-ENC | ENC, ENC2 |

**선행**: T-14

---

## 4. 구현 후 최종 체크리스트

| PRD | 태스크 | 확인 |
|-----|--------|------|
| ML-01 | T-04 | ? |
| ML-02 | T-05 | ? |
| ML-03 | T-08 | ? |
| ML-04 | T-09 | ? |
| ML-05 | T-10 | ? |
| MAP-01 | T-11, T-13 | ? |
| NB-01 | T-13 | ? |
| DOC-01 | 전 태스크 ENC | ? |
| C-04 | T-03 | ? |
| C-05 | 전 태스크 ENC2 | ? |

---

## 5. 검수 요청

`tasks.md` v0.1 초안에 대한 승인 또는 수정 지시를 요청한다.

1. 태스크 15개(T-01~T-15) 분해 ? 승인 / 통합·분할 요청
2. 서브에이전트 3건(T-02, T-04, T-11) ? 승인 / 변경
3. Notebook 단일 파일 통합 ? 승인 / 다중 Notebook

---

*본 문서는 UTF-8로 저장되었습니다. 검수 승인 후 4단계 구현(T-01부터)을 진행합니다.*

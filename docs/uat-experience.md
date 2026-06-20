# UAT 경험 요약 (레포트 작성용)

> 데이터마이닝 기말 프로젝트 ? 「집에서 언제 출발해야 따릉이를 탈 수 있을까?」  
> 본 문서는 Notebook·API·ML 파이프라인을 직접 실행하며 확인한 **UAT(사용자 수용 테스트) 경험**을 레포트에 옮기기 쉽게 정리한 요약본임.

---

## 1. 테스트 환경

| 항목 | 내용 |
|------|------|
| OS | Windows 10/11 |
| Python | Anaconda (conda-base, 3.13.x) |
| 실행 방식 | `pip install` → `run_pipeline.py` → `train_models.py` → Jupyter Notebook |
| 데이터 | 2024 가용성(2401/2404/2407), 2025.12 대여소 마스터 |
| API | `.env`에 `KAKAO_REST_API_KEY`, `KAKAO_MOBILITY_API_KEY` (선택) |

---

## 2. UAT 시나리오 및 결과

### UAT-1: 예측 출력 (핵심 기능)

**입력**: 출발 주소 + 할당 가능 소요시간(분)

**기대 동작**:
1. 주소 → 좌표 변환 (Kakao Local API)
2. 가장 가까운 구역(cluster) 매핑
3. 구역 내 최근접 대여소 선택
4. 도보 소요시간 계산 (Kakao Mobility 또는 Demo)
5. 대여소 도착 시각 기준 ML 예측 → 평균 거치대수·가능/불가 판정

**실행 결과 (예시)**:

| 조건 | 결과 |
|------|------|
| REST API + IP 등록 완료 | 주소 지오코딩 성공, 도보 `Kakao API` 표시 |
| REST API IP 미등록 (401) | `ip mismatched! callerIp=...` 오류 후 **좌표 Demo 자동 대체** |
| REST 키 없음 | 망원 인근 고정 좌표 Demo, `Demo (haversine)` 표시 |

**판정 로직**: 3개 모델 예측값을 모두 출력하되, **판정은 RF Tuned 기준** (검증 성능 최우수)

---

### UAT-2: 군집화 시각화

- DBSCAN(haversine, eps?200m)으로 **1,706개 구역** 생성
- Folium 지도에서 대여소 점 분포 확인 가능
- 예측 시 출발지가 구역 중심에서 200m 초과 시 **경고 메시지** 출력 (예: 294m)

---

### UAT-3: ML 모델 비교

| 모델 | MAE | RMSE | R² |
|------|-----|------|-----|
| Linear Regression | 7.32 | 9.79 | **0.009** |
| Random Forest | 5.17 | 7.38 | 0.436 |
| RF Tuned | **5.02** | **7.12** | **0.475** |

**UAT 관찰**:
- 선형회귀는 R²?0으로 **실질 예측력 거의 없음**
- 동일 입력에서 Linear 9.3대 vs RF 0.8대처럼 **큰 차이 발생 가능**
- 레포트·실사용 판정에는 **RF Tuned를 기준**으로 서술하는 것이 타당함

**최적 하이퍼파라미터**: `n_estimators=150`, `max_depth=None`, `min_samples_leaf=3`

---

### UAT-4: 카카오 API 연동

| API | 용도 | 성공 조건 | 실패 시 |
|-----|------|-----------|---------|
| Local REST | 주소→좌표 | 카카오맵(로컬) 활성화, REST 키, **호출 허용 IP** | 401/403 → Demo 좌표 대체 |
| Mobility | 도보/경로 소요시간 | REST 키 + 길찾기 API 권한 | Demo(직선거리+속도) |

**실제 겪은 오류**:
```
401 ip mismatched! callerIp=58.121.67.99
```
→ 카카오 개발자 콘솔 REST API 키 설정에서 **호출 허용 IP에 PC IP 추가** 또는 **IP 제한 해제**로 해결

---

### UAT-5: 재현성

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py
python scripts/train_models.py
jupyter notebook notebooks/ddareungi_departure_prediction.ipynb
```

- `REBUILD=False` 시 `data/processed/` 캐시 재사용 → 2회차 실행 시간 단축 확인
- 산출물 UTF-8 인코딩 유지

---

## 3. 대표 테스트 케이스 (레포트 인용용)

### 케이스 A ? API 정상 (주소 모드)

```
출발 주소: (사용자 입력)
할당 시간: 15분
출발 구역 ID: 1582
가장 가까운 대여소: 쌍용아파트2단지 정문
예상 도보 소요: 2분 (Kakao API)
예상 평균 거치대수: 3.6대
  - Linear Regression: 9.3대
  - Random Forest: 0.8대
  - RF Tuned: 0.7대
판정: RF Tuned 기준 → 대여 어려움 (0.7대 < 1대)
```

### 케이스 B ? Demo 대체 (IP 오류)

```
Kakao Local API 401 ? ip mismatched
→ 좌표 Demo로 대체
출발 구역: 망원역 인근 (고정 좌표)
예상 도보: 0분 (Demo)
판정: 대여 가능 (RF Tuned 17.8대)
```

---

## 4. 확인된 제한사항 (레포트 한계 섹션용)

1. **학습 데이터 시점**: 2024년 패턴 → 현재(2026) 시각 예측 시 시간대 특성만 유사하게 반영
2. **선형회귀 한계**: 비선형·구역별 패턴 미반영 → 비교·베이스라인 용도로만 적합
3. **구역 경계**: 200m DBSCAN 기준이나 실제 출발지가 구역 중심에서 멀면 경고 발생
4. **API 의존**: IP 제한·할당량 등 카카오 콘솔 설정 필요, 실패 시 Demo로 degrade
5. **Mobility API**: 자동차 길찾기 기반 ? 도보 전용 API는 아님

---

## 5. 레포트 작성 시 권장 서술 포인트

### 방법론
- 공간: DBSCAN haversine ~200m 구역화
- 시계열: 월별 마지막 7일 hold-out 분리
- 모델: Linear(베이스라인) + RF + GridSearch RF
- 의사결정: 출발 주소·할당 시간 → 최근접 대여소 → RF Tuned 예측 대수로 판정

### 결과
- RF Tuned가 MAE·R² 모두 최우수
- 카카오 API 연동 시 실제 주소 기반 예측 가능
- 이른 아침·특정 구역은 가용 대수 낮게 예측됨 (RF)

### 개선 방향 (선택)
- 판정 모델을 RF Tuned 단일로 고정 (현재 코드 반영됨)
- 호출 허용 IP 사전 등록 가이드 문서화
- 2025 데이터 추가 시 재학습

---

## 6. 관련 산출물 경로

| 문서/파일 | 내용 |
|-----------|------|
| `docs/data-join-report.md` | A↔B 조인율 ~87% |
| `docs/clustering-report.md` | DBSCAN 구역 통계 |
| `docs/kakao-api-report.md` | API 엔드포인트·Demo fallback |
| `docs/uat-results.md` | 수치 기반 UAT 로그 |
| `data/processed/model_metrics.json` | ML 성능 JSON |
| `src/config.py` | 공통 상수 (리팩터링 후) |

---

## 7. UAT 체크리스트 (최종)

- [x] ETL·군집화 파이프라인 실행
- [x] 3종 ML 모델 학습·성능 비교
- [x] Notebook Section 5 데모 예측
- [x] Notebook Section 6 위젯 입력·지도 출력
- [x] Kakao REST 지오코딩 (IP 등록 후)
- [x] API 실패 시 Demo fallback
- [x] RF vs Linear 예측 차이 관찰·해석
- [x] UTF-8 재현성

---

*작성 기준: 프로젝트 구현·Notebook UAT 세션 경험 종합*

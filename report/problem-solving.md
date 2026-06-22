# 문제 해결 과정 요약

> 데이터마이닝 기말 프로젝트 개발·UAT 중 발생한 이슈와 대응을 정리한 문서입니다.

---

## 1. 데이터 통합 (ETL)

| 문제 | 원인 | 해결 |
|------|------|------|
| 가용성(A)와 대여소 마스터(B) 조인률 저하 | 대여소 번호 형식 불일치 (`00101` vs `101`) | 숫자만 추출 후 앞자리 0 제거하는 `norm_station_no()` 정규화 |
| 미매칭 행 처리 | 폐쇄·신규 대여소 등 | Inner join, A-only 행은 ETL에서 제외 (매칭률 **~87%**) |
| 대용량 CSV 메모리 부족 | 월별 가용성 수백만 행 | `chunksize` 청크 단위 읽기 + 월 3개(2401/2404/2407) 샘플링 |

---

## 2. 공간 군집화

| 문제 | 원인 | 해결 |
|------|------|------|
| 개별 대여소 단위 예측 시 노이즈 | 인접 대여소 가용성이 유사 | **DBSCAN**(haversine, eps **200m**)으로 구역(`cluster_id`) 생성 |
| 출발지가 구역 중심과 멀 때 | 200m 구역 밖 주소 입력 | 200m 초과 시 **경고 메시지** 출력, 가장 가까운 구역으로 매핑 |

---

## 3. 머신러닝 모델

| 문제 | 원인 | 해결 |
|------|------|------|
| Linear Regression R² ? 0 | 비선형·교호작용(시간×구역) 미반영 | **Random Forest** + **GridSearch** 도입 |
| 모델 간 예측값 차이 큼 (예: 9.3대 vs 0.7대) | 선형 모델 한계 | 대여 가능 **판정은 RF Tuned 기준** (`FEASIBILITY_MODEL`) |
| 학습·테스트 누수 | 무작위 분할 | 월별 마지막 **7일 hold-out** 시계열 분할 |

**최종 성능 (RF Tuned)**: MAE **5.02**, R² **0.475**

---

## 4. Kakao API 연동

| 문제 | 증상 | 해결 |
|------|------|------|
| IP 미등록 | `401 ip mismatched` | 콘솔에 PC IP 등록 또는 IP 제한 해제 |
| Local API 미활성 | `403` | 카카오맵(로컬) 제품 활성화, **REST 키** 사용 |
| 주소 오타 | 지오코딩 결과 없음 | 사용자 입력 검증, 오타 시 Demo로 **대체하지 않음** (명확한 오류 메시지) |
| API 불가 환경 | 제출·데모 시 키/IP 없음 | **Demo fallback**: haversine 직선거리 + 고정 속도(도보 4.5km/h) |
| Mobility 키 없음 | 길찾기 API 미호출 | Demo 소요시간으로 자동 전환 |

---

## 5. 예측 흐름·Notebook

| 문제 | 해결 |
|------|------|
| 초기 OD(출발·도착) 흐름이 주제와 불일치 | **출발 주소 + 할당 시간(분)** 입력으로 재설계 (`predict_origin_rental`) |
| 가용 대수 부족 시각 | 대여 시각을 1시간씩 최대 6회 **앞당겨 재예측** |
| Notebook Section 6 셀 유실 | `generate_notebook.py`로 셀 구조 복구·재생성 |
| `has_rest_api_key` ImportError | 모듈 reload 및 Notebook setup 셀에서 키 존재 여부 판별 |
| Windows 한글 깨짐 | 파일 읽기·쓰기 `encoding='utf-8'` 통일, `config.py` 데모 주소 재저장 |

---

## 6. 코드 구조

- 파이프라인 로직을 **`src/` 모듈**로 분리 (`config`, `etl`, `clustering`, `stations`, `ml_models`, `predict`, `kakao_map`)
- 실행 진입점은 **`scripts/run_pipeline.py`**, **`scripts/train_models.py`** 두 개로 단순화
- 미사용 레거시(`recommend_departure`, `write_*.py` 등) 제거

---

## 7. 교훈 (레포트 결론용)

1. **공공데이터 조인**은 키 정규화가 성능보다 먼저다.
2. **군집화**로 공간 단위를 맞추면 가용성 예측이 현실에 가까워진다.
3. **선형회귀는 베이스라인**으로 두고, 실제 판정은 **RF Tuned**처럼 검증된 모델을 쓴다.
4. **외부 API**는 실패를 전제로 Demo fallback을 설계해야 제출·발표가 안정적이다.
5. **재현성**은 `run_pipeline` → `train_models` → Notebook 순서와 `data/processed/` 산출물로 확보한다.

---

## 관련 문서

| 문서 | 내용 |
|------|------|
| `docs/data-join-report.md` | 조인 통계 |
| `docs/clustering-report.md` | DBSCAN 결과 |
| `docs/kakao-api-report.md` | API 엔드포인트·fallback |
| `docs/uat-experience.md` | UAT 시나리오·체크리스트 |
| `docs/uat-results.md` | 수치 결과 로그 |

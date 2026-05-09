# ZirSave — 지르코니아 디스크 네스팅 최적화

여러 치과 보철 STL 파일을 원형 지르코니아 디스크에 배치하여 폐기율을 최소화하는 서비스입니다.
FastAPI 백엔드 + 모듈형 코어 알고리즘 구조로 되어 있습니다.

## 주요 기능

- 다중 STL 업로드 → 자동 파싱 → 디스크 배치 → 결과 JSON 반환
- **PCA 기반 3D orientation 자동 정렬** — 임의 회전된 STL도 최적 milling 자세 추정
- **Circle-aware 그리디 네스팅** — 원형 디스크 영역만 탐색 (사각형 bin-packing 후 폐기 방식 대비 효율)
- **멀티 디스크 자동 분산** — 한 디스크에 못 들어간 파트는 다음 디스크로 롤오버
- **90° 회전 탐색** — 원본 자세로 못 들어가는 경우 회전 시도
- 디스크 두께 (`disk_thickness`)로 feasibility 판정 → 초과 파트는 `unplaced`로 분류

## 디렉토리 구조

```
core/                   # 알고리즘 (백엔드와 독립)
  stl_parser.py         # PCA orientation + axis-aligned bbox
  bin_packing.py        # circle-aware greedy + 멀티 디스크 + 90° 회전
  waste_calc.py         # 멀티 디스크 면적 기준 폐기율
backend/
  main.py               # FastAPI 진입점
  routers/upload.py     # POST /upload
  routers/optimize.py   # POST /optimize, GET /optimize/result/{id}
  models.py / db.py     # SQLAlchemy 모델 (Postgres, fallback: in-memory)
  log_shipper.py        # JSONL 에러 로그 수집기
docs/                   # PRD / TSD / 통합 계획
tests/unit/             # 단위 테스트
```

## 알고리즘 개요

### 1. STL 파싱 (`core/stl_parser.py`)

1. STL의 모든 삼각형 vertex 수집
2. **PCA**로 주축 정렬 (`numpy.linalg.eigh`로 공분산 행렬 분해)
3. 정렬된 점군의 axis-aligned bbox extent 계산
4. extent 내림차순 정렬 → `width ≥ height ≥ depth`
5. `feasible = depth ≤ disk_thickness`

> **PCA의 한계**: 분산 기반이므로 L자/十자 같은 비대칭 형상은 진짜 minimum-volume bbox와
> 다소 차이가 날 수 있음. 일반 치과 크라운 (볼록 형상)에서는 거의 영향 없음.

### 2. 네스팅 (`core/bin_packing.py`)

1. 입력 아이템을 면적 내림차순 정렬
2. 각 아이템에 대해 그리드 (`step` mm) 위에서 첫 유효 위치 탐색
   - `is_rect_inside_circle`: 4 꼭짓점이 원 안 (수학적으로 tight)
   - 기존 배치 사각형과 비겹침
   - numpy 메쉬그리드로 벡터화 → Python 이중 루프 대비 수십 배 빠름
3. 0° 실패 시 90° 회전 재시도
4. 한 디스크 다 채우면 다음 디스크 (최대 `max_disks=10`)
5. 출력:
   ```json
   {
     "disks": [{"disk_index": 0, "items": [{"file_id", "x", "y", "angle", "w", "h"}, ...]}],
     "unplaced": [{"file_id", "reason"}, ...]
   }
   ```

### 3. 폐기율 (`core/waste_calc.py`)

```
waste_rate = 1 - (Σ placed_item_area) / (n_disks × π × r²)
```

모든 디스크 합산 면적이 분모. (Phase 2: bbox → convex hull로 교체 예정)

## API

| Method | Path                           | 설명                                                     |
| ------ | ------------------------------ | -------------------------------------------------------- |
| `POST` | `/upload`                      | STL 다중 업로드, `disk_config` JSON 수신, `case_id` 반환 |
| `POST` | `/optimize?case_id=…`          | 네스팅 실행, `result_id`, `waste_rate`, `n_disks` 반환   |
| `GET`  | `/optimize/result/{result_id}` | placement JSON 조회                                      |

요청/응답 상세는 [docs/TSD.md](docs/TSD.md) 참조.

## 셋업

```bash
pip install -r requirements.txt
cp .env.example .env  # DATABASE_URL 설정 (없으면 in-memory 모드)
uvicorn backend.main:app --reload
```

### 의존성

- `fastapi`, `uvicorn`, `sqlalchemy` — 웹/DB
- `numpy`, `numpy-stl` — STL 파싱 + PCA
- `pytest` — 테스트
- (선택) `redis`, `rq` — 비동기 잡 큐

## 테스트

```bash
python -m pytest tests/unit/ -v
```

샘플 STL이 [free-dental-model-prepared-10-upper-dental-separate-crowns/](free-dental-model-prepared-10-upper-dental-separate-crowns/)에 있어 end-to-end 검증 가능.

## 성능 (참고)

| 시나리오                  | step   | 시간    |
| ------------------------- | ------ | ------- |
| 60개 아이템 / 98mm 디스크 | 1.0 mm | ~60 ms  |
| 60개 아이템 / 98mm 디스크 | 0.5 mm | ~260 ms |
| STL 1개 (PCA 포함)        | —      | ~16 ms  |

## 로드맵

- **Phase 2**
  - Convex hull 면적 기반 정확한 폐기율
  - 임의 각도 회전 탐색 (현재는 0°/90°만)
- **Phase 3**
  - React + Three.js 시각화 프론트엔드
  - WeasyPrint PDF 리포트
- **추후 검토**
  - Rotating-calipers 기반 진짜 minimum-volume bbox
  - NFP(No-Fit Polygon) 기반 비사각형 네스팅

## 라이선스

내부 프로젝트.

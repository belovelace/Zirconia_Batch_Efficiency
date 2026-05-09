# Zirconia Batch Efficiency (ZirSave)

GCS 8기 프로토타입 — 지르코니아 디스크 위에 STL 파일을 2D bin-packing으로 자동 배치하여 재료 낭비율을 최소화하는 최적화 엔진.

---

## 개요

치과 보철물(크라운 등)의 STL 파일을 업로드하면, 지르코니아 원형 디스크 상의 최적 배치 위치를 계산하고 폐기율을 반환합니다.

| 레이어         | 기술 스택                                            |
| -------------- | ---------------------------------------------------- |
| Backend API    | Python 3.11 + FastAPI                                |
| Core Algorithm | `core/` 패키지 (stl_parser, bin_packing, waste_calc) |
| DB             | PostgreSQL (SQLAlchemy) / SQLite fallback            |
| 로깅           | JSONL `server_errors.log` + HTTP log shipper         |
| 테스트         | pytest (unit + integration)                          |

---

## 디렉토리 구조

```
.
├── backend/          # FastAPI 앱 (라우터, DB, 로그 shipper)
│   ├── main.py
│   ├── routers/
│   │   ├── upload.py     # POST /upload
│   │   └── optimize.py   # POST /optimize
│   ├── db.py
│   ├── models.py
│   ├── log_shipper.py
│   └── utils.py
├── core/             # 핵심 알고리즘
│   ├── stl_parser.py     # PCA orientation + axis-aligned bbox
│   ├── bin_packing.py    # circle-aware greedy + 멀티 디스크 + 90° 회전
│   └── waste_calc.py     # 멀티 디스크 면적 기준 폐기율
├── app/              # 앱 설정, 헬스체크, 메트릭
├── tests/            # 유닛 및 통합 테스트
├── docs/             # PRD, TSD, DATABASE 설계 문서
└── docker/           # 컨테이너 설정
```

---

## 빠른 시작

### 요구사항

- Python 3.11+
- PostgreSQL (또는 SQLite 자동 fallback)

### 설치

```bash
pip install -r requirements.txt
```

### 환경 변수

`.env` 파일을 생성하세요:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/zirsave
# SQLite fallback: sqlite:///./zirsave.db
LOG_COLLECTOR_URL=http://your-collector/logs   # 선택 사항
```

### 서버 실행

```bash
uvicorn backend.main:app --reload
```

---

## API

### `POST /upload`

STL 파일 업로드 및 파싱.

```json
// Response
{
  "file_id": "uuid",
  "width": 12.5,
  "height": 10.3,
  "depth": 8.1,
  "feasible": true
}
```

### `POST /optimize`

케이스 내 파일들을 원형 디스크(들)에 배치 최적화.

```json
// Request
{
  "case_id": "uuid",
  "disk_diameter": 98.0
}

// Response
{
  "result_id": "uuid",
  "waste_rate": 0.23,
  "n_disks": 1
}
```

### `GET /optimize/result/{result_id}`

배치 결과 JSON 조회.

```json
{
  "disks": [
    {
      "disk_index": 0,
      "items": [{ "file_id": "...", "x": 12.0, "y": 8.0, "angle": 0, "w": 12.5, "h": 10.3 }]
    }
  ],
  "unplaced": [{ "file_id": "...", "reason": "too_large_for_disk" }]
}
```

---

## 핵심 알고리즘

### 1. STL 파싱 (`core/stl_parser.py`)

1. STL의 모든 삼각형 vertex 수집 (numpy-stl)
2. **PCA**로 주축 정렬 (`numpy.linalg.eigh`로 공분산 행렬 분해) — 임의 회전된 STL도 안정적인 milling 자세로 보정
3. 정렬된 점군의 axis-aligned bbox extent 계산
4. extent 내림차순 정렬 → `width ≥ height ≥ depth`
5. `feasible = depth ≤ disk_thickness`

> **PCA의 한계**: 분산 기반이라 L자/十자 같은 비대칭 형상은 진짜 minimum-volume bbox와 다소 차이날 수 있음. 일반 치과 크라운 (볼록 형상)에서는 영향 무시 가능.

### 2. 네스팅 (`core/bin_packing.py`)

1. 입력 아이템을 면적 내림차순 정렬
2. 각 아이템에 대해 그리드 (`step` mm) 위에서 첫 유효 위치 탐색
   - `is_rect_inside_circle`: 4 꼭짓점이 원 안 (수학적으로 tight)
   - 기존 배치 사각형과 비겹침
   - **numpy 메쉬그리드로 벡터화** → Python 이중 루프 대비 수십 배 빠름
3. 0° 실패 시 **90° 회전 재시도**
4. 한 디스크 다 채우면 **다음 디스크로 롤오버** (최대 `max_disks=10`)

> 이전 rectpack 기반 구현은 사각형 bin의 (0,0) 코너부터 채우는 휴리스틱이 inscribed circle 밖이라 첫 아이템부터 reject되는 구조적 결함이 있어 제거됨.

### 3. 폐기율 (`core/waste_calc.py`)

```
waste_rate = 1 - (Σ placed_item_area) / (n_disks × π × r²)
```

모든 디스크 합산 면적이 분모. (Phase 2: bbox → convex hull로 교체 예정)

---

## 성능 (참고)

| 시나리오                  | step   | 시간    |
| ------------------------- | ------ | ------- |
| 60개 아이템 / 98mm 디스크 | 1.0 mm | ~60 ms  |
| 60개 아이템 / 98mm 디스크 | 0.5 mm | ~260 ms |
| STL 1개 (PCA 포함)        | —      | ~16 ms  |

---

## 테스트

```bash
pytest tests/unit/
```

샘플 STL이 [free-dental-model-prepared-10-upper-dental-separate-crowns/](free-dental-model-prepared-10-upper-dental-separate-crowns/)에 있어 end-to-end 검증 가능.

---

## 로드맵

- **Phase 2**: convex hull 면적 기반 정확한 폐기율, 임의 각도 회전 탐색
- **Phase 3**: React + Three.js 시각화 프론트엔드, WeasyPrint PDF 리포트
- **추후 검토**: rotating-calipers 기반 진짜 minimum-volume bbox, NFP 기반 비사각형 네스팅

---

## 문서

- [PRD](docs/PRD.md)
- [TSD](docs/TSD.md)
- [Database 설계](docs/DATABASE.md)
- [통합 계획](docs/ZIRSAVE_INTEGRATED_PLAN.md)

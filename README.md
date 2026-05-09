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
│   ├── stl_parser.py     # STL 파싱 + Z축 제약 검사
│   ├── bin_packing.py    # 원형 디스크 2D 배치 최적화
│   └── waste_calc.py     # 폐기율 계산 (Convex Hull)
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

케이스 내 파일들을 원형 디스크에 배치 최적화.

```json
// Request
{
  "case_id": "uuid",
  "disk_diameter": 98.0
}

// Response
{
  "placements": [...],
  "waste_rate": 0.23
}
```

---

## 핵심 알고리즘

1. **STL 파싱** (`stl_parser.py`) — numpy-stl로 XY 바운딩 박스 및 Z 깊이 추출, `depth <= disk_thickness` 로 가공 가능 여부 판별
2. **Bin Packing** (`bin_packing.py`) — rectpack 기반 초기 배치 후, 네 꼭짓점 원 내부 판별(그리드 탐색)으로 유효 위치 확정
3. **폐기율 계산** (`waste_calc.py`) — 배치된 아이템의 Convex Hull 면적 대비 디스크 면적으로 폐기율 산출

---

## 테스트

```bash
pytest tests/unit/
```

---

## 문서

- [PRD](docs/PRD.md)
- [TSD](docs/TSD.md)
- [Database 설계](docs/DATABASE.md)
- [통합 계획](docs/ZIRSAVE_INTEGRATED_PLAN.md)

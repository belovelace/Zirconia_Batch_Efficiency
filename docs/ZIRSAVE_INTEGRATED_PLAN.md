# ZirSave — 통합 개발 계획

> 여러 STL 파일을 지르코니아 디스크에 최적 배치하고 폐기율을 계산하는 시스템  
> 현재 상태: `zirsave_packing.py` (2D bin packing, 내접 정사각형 근사) 동작 확인 완료

---

## 1. 현재 구현 상태

```
완료
├── STL 파싱 (numpy-stl)
├── XY 바운딩 박스 추출
├── 2D bin packing (rectpack)
├── 폐기율 계산
└── matplotlib 시각화

미완
├── 원형 디스크 코너 영역 미활용 (내접 정사각형 근사 → 21.5% 손실)
├── Z축(깊이) 제약 미반영
├── 실제 치아 윤곽 미반영 (바운딩 박스 과대 추정)
├── 회전 각도 0°/90° 제한
└── 웹 인터페이스 없음
```

---

## 2. 전체 로드맵

```
Phase 0  현재 ──▶  Phase 1  ──▶  Phase 2  ──▶  Phase 3  ──▶  Phase 4
알고리즘 기반       Z축·원형       윤곽·회전       백엔드 API      프론트엔드
(완료)             개선            개선            구축            + 배포
                  (1주)           (2주)           (2주)           (2주)
```

---

## 3. 알고리즘 개선 계획

### Phase 1 — Z축 제약 + 원형 디스크 정밀화 (1주)

#### 1-1. Z축 제약 추가

**문제:** 보철물 높이가 디스크 두께를 초과해도 현재는 그냥 배치된다.

**개선:**
```python
# stl_parser.py
def parse_stl(stl_path, disk_thickness=20.0):
    ...
    depth = m.z.max() - m.z.min()
    feasible = depth <= disk_thickness  # 배치 가능 여부
    return {"width": w, "height": h, "depth": depth, "feasible": feasible}
```

추가 CLI 파라미터:
```bash
--disk_thickness 20   # 기본값 20mm (국내 표준)
```

완료 기준: depth 초과 아이템이 `unplaced`로 분류되고 리포트에 사유 명시

---

#### 1-2. 원형 디스크 영역 정밀화

**문제:** 내접 정사각형 근사로 디스크 코너 영역(전체의 21.5%) 미사용

**개선: 직사각형 네 꼭짓점이 원 내부인지 판별**

```python
# bin_packing.py
def is_rect_inside_circle(x, y, w, h, cx, cy, r):
    corners = [(x, y), (x+w, y), (x, y+h), (x+w, y+h)]
    return all((px-cx)**2 + (py-cy)**2 <= r**2 for px, py in corners)

def optimize_placement_circular(items, disk_diameter):
    r  = disk_diameter / 2
    cx = cy = r
    # 격자 기반으로 유효 위치 탐색 (step: 1mm)
    ...
```

완료 기준: 동일 아이템 세트에서 배치 수 증가 또는 폐기율 5%p 이상 개선

---

### Phase 2 — 윤곽 정밀화 + 회전 최적화 (2주)

#### 2-1. Convex Hull 기반 실제 윤곽 근사

**문제:** 타원형 치아를 직사각형으로 근사 → 실제 점유 면적 20~30% 과대 추정

**개선: 폐기율 계산에만 convex hull 면적 적용**
```python
# waste_calc.py
from scipy.spatial import ConvexHull

def get_convex_hull_area(stl_path):
    m = mesh.Mesh.from_file(stl_path)
    pts = np.column_stack([m.x.flatten(), m.y.flatten()])
    hull = ConvexHull(pts)
    return hull.volume  # 2D에서 volume = 면적
```

> 배치 충돌 계산은 여전히 바운딩 박스 사용.  
> convex hull은 폐기율 수치에만 적용 (정확도 vs 계산 단순성 균형)

---

#### 2-2. 임의 각도 회전 탐색

**문제:** 0°/90° 제한으로 긴 보철물(브릿지 등) 최적 각도 미탐색

**개선: 15° 간격으로 최소 바운딩 박스 각도 탐색**
```python
def get_optimal_rotation(stl_path, angle_step=15):
    pts = get_2d_points(stl_path)
    best_area, best_angle = float('inf'), 0
    for angle in range(0, 180, angle_step):
        rad = np.radians(angle)
        rot = np.array([[np.cos(rad), -np.sin(rad)],
                        [np.sin(rad),  np.cos(rad)]])
        rotated = pts @ rot.T
        w = rotated[:, 0].ptp()
        h = rotated[:, 1].ptp()
        if w * h < best_area:
            best_area, best_angle = w * h, angle
    return best_angle
```

완료 기준: 동일 아이템 세트에서 폐기율 추가 3%p 이상 개선

---

### 알고리즘 개선 완료 기준 요약

| Phase | 항목 | 완료 기준 |
|-------|------|-----------|
| 1 | Z축 제약 | depth 초과 아이템 자동 필터링 |
| 1 | 원형 디스크 | 폐기율 5%p 이상 개선 |
| 2 | Convex hull | 폐기율 수치 실제에 근접 |
| 2 | 회전 최적화 | 폐기율 추가 3%p 이상 개선 |

---

## 4. MVP 제품 개발 계획

알고리즘 Phase 1 완료 후 병행 시작.

### 기술 스택

```
Frontend    React 18 + Three.js r128
Backend     Python 3.11 + FastAPI
Algorithm   core/ 모듈 (Phase 1~2 완성본)
DB          PostgreSQL (Supabase)
Report      WeasyPrint (HTML → PDF)
Infra       Vercel (Frontend) + Railway (Backend)
```

---

### Sprint 1 — 코어 모듈 분리 리팩토링 (1주)

현재 모놀리식 `zirsave_packing.py`를 모듈로 분리한다.

```
core/
├── stl_parser.py      # STL 파싱, 정규화, Z축 체크
├── bin_packing.py     # 배치 최적화 (원형 + 회전)
├── waste_calc.py      # 폐기율 계산 (convex hull)
└── visualizer.py      # matplotlib 시각화 (개발용)
```

완료 기준: `from core.bin_packing import optimize_placement` 로 기존과 동일하게 동작

---

### Sprint 2 — FastAPI 백엔드 (2주)

#### 엔드포인트

| Method | Path | 기능 |
|--------|------|------|
| POST | `/upload` | STL 멀티파일 수신 → 파싱 → case 저장 |
| POST | `/optimize` | case_id 받아 배치 최적화 실행 |
| GET | `/result/{case_id}` | 배치 결과 + 폐기율 JSON 반환 |
| GET | `/report/{case_id}` | PDF 리포트 생성 + 다운로드 |

#### 데이터 스키마

```python
# schemas.py
class DiskConfig(BaseModel):
    diameter: float = 98.0        # mm
    thickness: float = 20.0       # mm
    zirconia_type: str = "3Y"     # 3Y / 4Y / 5Y

class CaseCreate(BaseModel):
    disk_config: DiskConfig
    file_names: list[str]

class PlacementResult(BaseModel):
    case_id: str
    placed: list[dict]
    unplaced: list[dict]
    waste_rate: float
    n_disks: int
```

#### DB 테이블

```sql
cases   (id, created_at, disk_config jsonb)
files   (id, case_id, filename, bbox_w, bbox_h, depth)
results (id, case_id, placement jsonb, waste_rate, n_disks)
```

완료 기준: `curl -X POST /upload -F "files=@crown.stl"` 로 폐기율 JSON 반환

---

### Sprint 3 — React 프론트엔드 (2주)

#### 화면 구성

```
┌─────────────────────────────────────────┐
│  1. 파일 업로드                          │
│     [ STL 파일 drag & drop ]            │
│     디스크 지름: [98mm ▼]  두께: [20mm] │
│     종류: [3Y ▼]                        │
│     [ 최적화 실행 ]                     │
├─────────────────────────────────────────┤
│  2. 배치 결과 시각화 (Three.js)         │
│     ○ 디스크 탑뷰                       │
│     각 보철물 색상 구분                  │
│     마우스 hover → 이름·크기 툴팁       │
├─────────────────────────────────────────┤
│  3. 리포트 카드                         │
│     배치 성공: N개   폐기율: XX.X%      │
│     미배치: N개 (사유 표시)             │
│     [ PDF 리포트 다운로드 ]             │
└─────────────────────────────────────────┘
```

#### 컴포넌트 구조

```
src/
├── App.jsx
├── components/
│   ├── FileUpload.jsx        # drag & drop, 파일 목록
│   ├── DiskConfig.jsx        # 지름·두께·종류 설정
│   ├── PlacementViewer.jsx   # Three.js 2D 탑뷰
│   ├── WasteSummary.jsx      # 폐기율 카드
│   └── ReportDownload.jsx    # PDF 다운로드 버튼
└── api/
    └── zirsave.js            # FastAPI 호출 함수
```

완료 기준: 브라우저에서 STL 업로드 → 배치 시각화 → PDF 다운로드 전 과정 동작

---

### Sprint 4 — 배포 + 베타 테스트 (1주)

```
Vercel   프론트엔드 배포 (자동 CI/CD)
Railway  FastAPI 백엔드 배포
Supabase PostgreSQL 프로덕션 DB
```

베타 테스트 체크리스트:
- [ ] 실제 치과 STL 파일 업로드 테스트 (기공소 1~2곳)
- [ ] 모바일 브라우저 동작 확인
- [ ] 디스크 지름 변경 (98mm / 71mm / 88mm) 테스트
- [ ] 10개 이상 STL 동시 업로드 성능 테스트

---

## 5. 전체 타임라인

| 주차 | 작업 | 산출물 |
|------|------|--------|
| 1주 | 알고리즘 Phase 1 (Z축 + 원형 디스크) | 개선된 `zirsave_packing.py` |
| 2~3주 | 알고리즘 Phase 2 (윤곽 + 회전) + Sprint 1 리팩토링 | `core/` 모듈 완성 |
| 4~5주 | Sprint 2 FastAPI 백엔드 | API 서버 동작 |
| 6~7주 | Sprint 3 React 프론트엔드 | 웹앱 로컬 동작 |
| 8주 | Sprint 4 배포 + 베타 테스트 | 실URL 접속 가능 |

---

## 6. 최종 디렉토리 구조

```
zirsave/
├── backend/
│   ├── main.py
│   ├── routers/
│   │   ├── upload.py
│   │   ├── optimize.py
│   │   └── report.py
│   ├── core/
│   │   ├── stl_parser.py
│   │   ├── bin_packing.py
│   │   ├── waste_calc.py
│   │   └── visualizer.py
│   ├── models/
│   │   └── schemas.py
│   └── db/
│       └── database.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   └── App.jsx
│   └── package.json
├── notebooks/
│   └── algorithm_validation.ipynb
├── stl_samples/
├── zirsave_packing.py        # 현재 동작 확인된 스크립트
└── PLAN.md
```

---

## 7. 다음 즉시 실행 액션

```
1. Phase 1-1: zirsave_packing.py에 --disk_thickness 파라미터 추가
2. Phase 1-2: 원형 디스크 판별 함수 구현 및 폐기율 비교
3. 위 두 개 완료 후 core/ 모듈 분리 시작
```

---

*ZirSave Integrated Development Plan | 신은지 | 가천대학교 GCS*

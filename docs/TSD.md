# ZirSave — TSD (Technical Specification Document)

시스템 개요
- ZirSave는 STL 파일을 파싱하여 XY 바운딩 박스를 추출하고, 지르코니아 원형 디스크 상에 2D bin-packing 알고리즘으로 배치한다. Phase1에서는 Z축 제약과 원형 디스크 내부 판별을 추가한다.

아키텍처
- Frontend: React 18 + Three.js (향후)
- Backend: Python 3.11 + FastAPI
- Core Algorithm: core/ 패키지 (stl_parser.py, bin_packing.py, waste_calc.py, visualizer.py)
- DB: PostgreSQL (Supabase)
- Reporting: WeasyPrint

모듈별 상세
1) stl_parser.py
   - 기능: STL 파싱, 좌표 정규화(원점 이동), XY 바운딩 박스(w,h) 및 Z 깊이(depth) 계산, feasible 플래그 (depth <= disk_thickness)
   - 주요 함수:
     - parse_stl(stl_path, disk_thickness=20.0) -> {width, height, depth, feasible}
   - 의존성: numpy-stl, numpy

2) bin_packing.py
   - 기능: 2D bin packing 수행(원형 디스크 고려), 원형 내부 판별 함수 제공
   - 주요 함수:
     - is_rect_inside_circle(x, y, w, h, cx, cy, r) -> bool
     - optimize_placement_circular(items, disk_diameter, step=1) -> placement_result
   - 알고리즘:
     - rectpack 라이브러리 기반 초기 배치
     - 원형 디스크 유효성은 네 꼭짓점이 모두 원 내부인지 검사
     - 그리드 기반 탐색(step=1mm)으로 가능한 위치 탐색
   - 성능 고려:
     - step 파라미터로 탐색 정밀도 조절
     - 큰 파일/다수 아이템 시 타임아웃 또는 초기 휴리스틱 적용 검토

3) waste_calc.py
   - 기능: 폐기율 계산
   - 주요 함수:
     - get_convex_hull_area(stl_path) -> area
     - compute_waste_rate(placed_items, disk_area) -> float
   - 의존성: scipy (ConvexHull), numpy
   - 비고: Convex hull은 Phase2에서 배치 충돌 계산 대신이 아닌 폐기율 보정용으로만 사용

API 디자인 (FastAPI)
- POST /upload
  - 입력: multipart/form-data, files[] STL 파일, disk_config JSON
  - 동작: 각 STL을 parse_stl로 파싱, 파일 레코드 및 case 생성, 초기 응답은 case_id 반환 또는 즉시 최적화 수행 후 결과 반환(설정에 따름)

- POST /optimize
  - 입력: case_id
  - 동작: 해당 case의 파일 목록을 불러와 optimize_placement_circular 실행, 결과 저장(results 테이블)

- GET /result/{case_id}
  - 반환: PlacementResult JSON (placed, unplaced, waste_rate, n_disks)

- GET /report/{case_id}
  - 동작: results+metadata로 HTML 생성 → WeasyPrint로 PDF로 변환 후 반환

데이터베이스 스키마
- cases (id UUID PK, created_at timestamp, disk_config jsonb)
- files (id UUID PK, case_id FK, filename text, bbox_w float, bbox_h float, depth float, convex_area float NULL)
- results (id UUID PK, case_id FK, placement jsonb, waste_rate float, n_disks int, created_at timestamp)

배치 포맷 (placement json)
{
  "disks": [
    {
      "disk_index": 0,
      "items": [
        {"file_id": "...", "x": 12.0, "y": 34.0, "angle": 0, "w": 20.0, "h": 10.0}
      ]
    }
  ],
  "unplaced": [ {"file_id": "...", "reason": "depth_exceeded"} ]
}

성능 및 신뢰성
- 최적화는 CPU 바운드 작업: Worker pool 또는 비동기 태스크(BackgroundTasks, Celery/RQ) 사용 권장
- 대용량 업로드 시 chunked 처리 및 단계별 진행(파싱→검증→배치)
- 테스트: 알고리즘 정확성(단위 테스트), 상호운용성 테스트(API/Frontend)

운영(배포)
- Backend: Railway (Docker), 환경변수로 DB URL/SECRET 관리
- Frontend: Vercel
- DB: Supabase(Postgres)

참고 및 의존성
- numpy-stl, rectpack, scipy, fastapi, uvicorn, weasyprint

작성자: ZirSave 엔지니어링팀

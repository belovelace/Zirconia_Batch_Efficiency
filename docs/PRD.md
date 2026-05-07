# ZirSave — PRD (Product Requirements Document)

요약
- 목적: 여러 STL 파일을 지르코니아 디스크 상에 최적으로 배치하여 폐기율(waste rate)을 최소화하고, 결과를 리포트(PDF/JSON)로 제공한다.
- 주요 사용자: 치과 기공사, 임상 엔지니어, QA 담당자

핵심 기능 (MVP)
1. STL 업로드: 다중 STL 파일 수신 (웹/CLI)
2. 파싱 및 검증: STL에서 XY 바운딩 박스 및 Z 깊이(두께) 추출 — disk_thickness 검증
   - 참조: ZIRSAVE_INTEGRATED_PLAN.md:48-61
3. 최적화 엔진
   - 2D bin-packing 기반 배치
   - 원형 디스크 코너 유효영역 판별 (직사각형 네 꼭짓점 검사)
   - (Phase2 이후) convex hull 기반 폐기율 보정 및 임의 각도 회전 탐색
   - 참조: ZIRSAVE_INTEGRATED_PLAN.md:66-85, 90-131
4. 결과 제공
   - 배치 결과 JSON (placed/unplaced, waste_rate, n_disks)
   - PDF 리포트 (WeasyPrint)
   - 참조: ZIRSAVE_INTEGRATED_PLAN.md:185-211, 221

비기능 요구
- 정확도: Phase1 개선으로 동일 입력셋 대비 폐기율 5%p 이상 개선
  - 참조: ZIRSAVE_INTEGRATED_PLAN.md:85
- 성능: 10개 이상의 STL 동시업로드 시 허용 가능한 응답 시간(목표는 최적화 완료까지 30s 이내; 환경에 따라 조정)
- 확장성: 알고리즘(core/)은 API·프론트엔드와 분리된 모듈형으로 설계
  - 참조: ZIRSAVE_INTEGRATED_PLAN.md:169-176

MVP 완료 기준
- disk_thickness 파라미터(기본 20mm)로 Z축 초과 아이템이 unplaced로 분류되어 리포트에 표기될 것
  - 참조: ZIRSAVE_INTEGRATED_PLAN.md:56-63
- 원형 디스크 정밀화로 동일 아이템에서 배치 수 증가 또는 폐기율 5%p 개선 확인
  - 참조: ZIRSAVE_INTEGRATED_PLAN.md:82-85
- FastAPI 기반 /upload, /optimize, /result/{case_id}, /report/{case_id} 기본 흐름 동작
  - 참조: ZIRSAVE_INTEGRATED_PLAN.md:185-191

추후 로드맵
- Phase2: convex hull 폐기율 보정, 회전 최적화
- 웹 프론트엔드 (React + Three.js) 및 배포 (Vercel/Railway)
  - 참조: ZIRSAVE_INTEGRATED_PLAN.md:152-161, 225-246

작성자: ZirSave 기획팀

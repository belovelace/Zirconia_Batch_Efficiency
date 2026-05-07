# ZirSave — Test Cases

형식: 체크리스트 형태로 정리. 각 케이스는 Endpoint, Request(예시), Expected response(예시/스키마)를 포함합니다.

## 1. POST /upload

- [ ] Upload - 단일 정상 STL 파일 (성공)
  - Endpoint: POST /upload
  - Request (curl 예시):
    - curl -X POST "http://localhost:8000/upload" -F "files=@crown.stl" -F "disk_config={\"diameter\":98,\"thickness\":20}" 
  - Expected response (200 OK, JSON):
    {
      "case_id": "<uuid>",
      "placed": [ {"file_id":"<uuid>", "filename":"crown.stl", "x":12.0, "y":34.0, "angle":0} ],
      "unplaced": [],
      "waste_rate": 12.3,
      "n_disks": 1
    }

- [ ] Upload - 다중 STL 파일 (성공)
  - Endpoint: POST /upload
  - Request: multipart with files=@crown.stl files=@bridge.stl files=@inlay.stl and disk_config
  - Expected response (200 OK): JSON with placed list length >= 1, waste_rate as float, n_disks integer

- [ ] Upload - Z축(depth) 초과 아이템 (성공, unplaced 처리)
  - Endpoint: POST /upload
  - Request: files=@tall_item.stl (depth > disk_thickness), disk_config thickness=20
  - Expected response (200 OK): JSON where `unplaced` contains an entry for the file with reason `depth_exceeded` (or equivalent) and `placed` does not include it. Example:
    {
      "case_id":"<uuid>",
      "placed": [],
      "unplaced": [ {"file_id":"<uuid>", "filename":"tall_item.stl", "reason":"depth_exceeded"} ],
      "waste_rate": null,
      "n_disks": 0
    }

- [ ] Upload - 잘못된 파일 포맷 (실패)
  - Endpoint: POST /upload
  - Request: files=@not_a_stl.txt
  - Expected response (400 Bad Request): {"error":"invalid_file_format", "message":"uploaded file is not a valid STL"}

- [ ] Upload - 파일 미첨부 (실패)
  - Endpoint: POST /upload
  - Request: POST with no files field
  - Expected response (400 Bad Request): {"error":"no_files_provided"}

- [ ] Upload - 잘못된 disk_config (실패)
  - Endpoint: POST /upload
  - Request: disk_config malformed JSON or missing required fields
  - Expected response (400 Bad Request): {"error":"invalid_disk_config", "message":"disk_config missing or malformed"}

## 2. POST /optimize

- [ ] Optimize - 유효한 case_id (성공)
  - Endpoint: POST /optimize
  - Request (JSON): {"case_id":"<existing-case-uuid>"}
  - Expected response (200 OK, JSON): same shape as upload successful response (placement result)
    {
      "case_id":"<uuid>",
      "placed": [...],
      "unplaced": [...],
      "waste_rate": 10.5,
      "n_disks": 1
    }

- [ ] Optimize - 존재하지 않는 case_id (실패)
  - Endpoint: POST /optimize
  - Request: {"case_id":"00000000-0000-0000-0000-000000000000"}
  - Expected response (404 Not Found): {"error":"case_not_found", "message":"case_id not found"}

- [ ] Optimize - 이미 최적화된 케이스 재요청 (idempotency)
  - Endpoint: POST /optimize
  - Request: existing case_id that already has results
  - Expected response (200 OK): existing placement JSON returned or a 409/200 depending on implementation; at minimum should not crash. (권장: 200 with stored result)

## 3. GET /result/{case_id}

- [ ] Result - 최적화 후 결과 조회 (성공)
  - Endpoint: GET /result/{case_id}
  - Request: GET /result/<case_id>
  - Expected response (200 OK, JSON): PlacementResult 스키마
    {
      "case_id":"<uuid>",
      "placed": [ {"file_id":"<uuid>", "filename":"crown.stl", "x":12.0, "y":34.0, "angle":0} ],
      "unplaced": [ {"file_id":"<uuid>", "filename":"tall_item.stl", "reason":"depth_exceeded"} ],
      "waste_rate": 11.2,
      "n_disks": 1
    }

- [ ] Result - 결과 미존재(아직 최적화 안함) (실패)
  - Endpoint: GET /result/{case_id}
  - Request: GET /result/<case_without_result>
  - Expected response (404 Not Found): {"error":"result_not_found", "message":"no placement result for case_id"}

## 4. GET /report/{case_id}

- [ ] Report - PDF 리포트 생성 및 다운로드 (성공)
  - Endpoint: GET /report/{case_id}
  - Request: GET /report/<case_id_with_result>
  - Expected response (200 OK)
    - Content-Type: application/pdf
    - Content-Disposition: attachment; filename="zirsave_report_<case_id>.pdf"
    - Body: non-empty PDF binary (verify starts with %PDF)

- [ ] Report - 결과 미존재 또는 case 없음 (실패)
  - Endpoint: GET /report/{case_id}
  - Request: GET /report/<invalid_or_no_result_case>
  - Expected response (404 Not Found): {"error":"result_not_found", "message":"cannot generate report without placement result"}

## 5. 비기능/엣지 케이스

- [ ] 대용량 동시 업로드(성능) — 10개 이상의 STL (성공 목표)
  - Endpoint: POST /upload
  - Request: files=@1.stl ... @10.stl
  - Expected result: 200 OK with placement or case_id; end-to-end 응답 시간 목표: 최적화 완료까지 30초 이내(환경에 따라 유동적)

- [ ] 큰 파일(용량 제한) (실패)
  - Endpoint: POST /upload
  - Request: very_large_file.stl (초과 용량)
  - Expected response (413 Payload Too Large) 또는 400 에러와 명확한 메시지

- [ ] 잘못된 UUID 형식 입력 (실패)
  - Endpoint: POST /optimize or GET /result/{case_id}
  - Request: case_id = "not-a-uuid"
  - Expected response (400 Bad Request): {"error":"invalid_case_id"}

## 6. 보안/권한(선택적)

- [ ] 인증이 필요한 경우 인증 없을 때 접근 (실패)
  - Endpoint: 모든 쓰기/읽기 엔드포인트
  - Request: without Authorization header
  - Expected response (401 Unauthorized) — (현재 MVP에서 인증 미실装 시 스킵 가능)

- [ ] 업로드된 파일에 악성 콘텐츠(폴더 경로 주입 등) 검사
  - Expected: 서버가 파일을 안전하게 처리하고 파일명/메타데이터에 대한 적절한 정규화 적용

---

작성 지침
- 각 케이스는 자동화된 통합 테스트(예: pytest + requests) 또는 수동 검증 체크리스트로 사용할 수 있습니다.
- 응답 바디는 예시이며, 구현 시 정확한 필드명·에러 코드를 API 스펙과 맞춰 조정하세요.

작성자: ZirSave QA

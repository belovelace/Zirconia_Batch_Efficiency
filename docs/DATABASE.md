# ZirSave — DATABASE 설계

목표
- 케이스, 업로드된 STL 파일 메타데이터, 배치 결과를 저장하여 재현성과 리포트 생성을 지원한다.

ERD 요약
- cases 1 --- * files
- cases 1 --- * results

테이블 정의

1) cases
- id: UUID PRIMARY KEY (서버 생성)
- created_at: TIMESTAMP WITH TIME ZONE DEFAULT now()
- disk_config: JSONB (diameter, thickness, zirconia_type)

SQL
CREATE TABLE IF NOT EXISTS cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz DEFAULT now(),
  disk_config jsonb NOT NULL
);

2) files
- id: UUID PRIMARY KEY
- case_id: UUID REFERENCES cases(id) ON DELETE CASCADE
- filename: TEXT
- bbox_w: REAL
- bbox_h: REAL
- depth: REAL
- convex_area: REAL NULL -- Phase2에서 채워질 수 있음
- metadata: JSONB NULL -- 원본 파라미터(업로드 시 전달된 정보)

SQL
CREATE TABLE IF NOT EXISTS files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
  filename text NOT NULL,
  bbox_w real NOT NULL,
  bbox_h real NOT NULL,
  depth real NOT NULL,
  convex_area real,
  metadata jsonb
);

3) results
- id: UUID PRIMARY KEY
- case_id: UUID REFERENCES cases(id) UNIQUE
- placement: JSONB -- disks, items, unplaced
- waste_rate: REAL
- n_disks: INTEGER
- created_at: TIMESTAMP WITH TIME ZONE DEFAULT now()

SQL
CREATE TABLE IF NOT EXISTS results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id) UNIQUE,
  placement jsonb NOT NULL,
  waste_rate real NOT NULL,
  n_disks integer NOT NULL,
  created_at timestamptz DEFAULT now()
);

색인 및 성능
- files.case_id 인덱스 생성 (조회 성능)
- results.case_id 유니크 제약으로 케이스 당 최신 결과 1개 보장

마이그레이션 및 초기화 스크립트
- 초기화 스크립트 예시(파이썬 SQLAlchemy 또는 Alembic 사용 권장)

운영 고려사항
- 대량 업로드시 파일 메타데이터만 DB에 저장, 원본 파일은 S3같은 오브젝트 스토어에 보관 권장
- 백업 정책 및 스키마 버전 관리 (Alembic)

작성자: ZirSave 데이터팀

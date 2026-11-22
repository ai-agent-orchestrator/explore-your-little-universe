# 타로 실험 모드 실행·검증

2026-11-22 · [리팩터링 실행 계획](TAROT_REFACTORING_PLAN.md) R0~R6 구현.

기존 정적 Beta는 그대로 실행된다. 타로 모드는 별도의 로컬 FastAPI와 PostgreSQL·Neo4j·Chroma를 사용한다. `VITE_TAROT_API_URL` 없이 빌드하면 타로 탭과 타로 JavaScript 청크가 생성되지 않는다. `v1`, 기존 600개 스냅샷, 공개 Cypher import 파일, 루미 그림, Pages 워크플로는 변경하지 않았다.

## 준비

저장소 루트, Python 3.12, Node.js 22.12 이상을 기준으로 한다.

```powershell
.venv/Scripts/python -m pip install -r requirements-tarot.txt
```

검증한 주요 조합은 FastAPI 0.165.0, Pydantic 2.14.3, psycopg 3.3.9, psycopg-pool 3.3.3, LangGraph 1.2.24, langgraph-checkpoint-postgres 3.2.1, Chroma 1.5.9, LiteRT-LM API 0.18.0이다. 전체 직접 의존성은 [requirements-tarot.txt](../requirements-tarot.txt)에 고정했다.

로컬에서만 `.env.tarot`를 만들고 다음 값을 본인 환경에 맞게 설정한다. 이 파일은 Git에서 제외된다.

```dotenv
LUMI_POSTGRES_PASSWORD=YOUR_LOCAL_PASSWORD
LUMI_POSTGRES_DSN=postgresql://lumi:YOUR_LOCAL_PASSWORD@127.0.0.1:5433/lumi
LUMI_CHROMA_PATH=data/chroma
LUMI_LLM_BASE_URL=https://YOUR_COMPATIBLE_ENDPOINT/v1
LUMI_LLM_MODEL=YOUR_MODEL
LUMI_LLM_API_KEY=YOUR_PROVIDER_KEY
```

DSN 비밀번호에 특수문자가 있다면 URL 인코딩한다. LLM 세 값은 실제 OpenAI 호환 서비스의 값으로 바꾼다. 설정이 없으면 임의의 기본 키나 다른 모델로 대체하지 않고 `llm_not_configured`를 반환한다. 설정 후 생성·검수 요청은 해당 LLM 엔드포인트로 질문과 근거를 전달한다. 실제 LLM 호출 비용·품질은 이번 검증에서 측정하지 않았다.

Neo4j는 기존 `.env.mbti`와 `mbti-zodiac`를 사용한다. 임베딩 모델은 기존 `models/embeddinggemma-2-text-270m.litertlm`을 재사용한다.

```powershell
# PostgreSQL만 시작. 기존 기본 포트 5432와 분리한다.
docker compose --env-file .env.tarot -f tarot_lab/compose.yaml up -d
.venv/Scripts/python -m tarot_lab.migrate
# 모델이 없는 경우에만 다운로드
.venv/Scripts/python -m mbti_lab.download_model
.venv/Scripts/python -m tools.seed_tarot_knowledge --dataset tarot-v1 --neo4j --chroma
```

마이그레이션은 `lumi.schema_migrations`로 적용 이력을 관리한다. 서비스 테이블은 `lumi`, 체크포인터 테이블은 `langgraph` 스키마에 생성한다. 기존 Neo4j 데이터는 지우지 않는다. Chroma는 임베디드 `PersistentClient`이며 별도 서버를 띄우지 않는다.

현재 지식 범위는 카드 78장, 의미 156개, 타로 해설 180개(모든 의미의 일반 해설 156개 + 탑·별·은둔자의 상황별 24개)다. Chroma 총량은 기존 600개 포함 **780개**다. 타로 `RagChunk`의 벡터는 Neo4j에 저장하지 않으며 정적 `graph.json`에도 넣지 않는다. 향후 타로 780개·수만 개 해설 목표는 별도 콘텐츠 작업이다.

## 서버와 화면

첫 터미널:

```powershell
.venv/Scripts/python -m uvicorn tarot_lab.api:app --host 127.0.0.1 --port 8017
```

두 번째 터미널:

```powershell
cd frontend
$env:VITE_TAROT_API_URL='http://127.0.0.1:8017'
npm run dev -- --port 5173 --strictPort
```

`http://127.0.0.1:5173/#tarot`에서 실행한다. CORS는 이 origin만 허용한다. `localhost` 대신 문서의 `127.0.0.1` 주소를 사용한다. 기본 MBTI 서버는 8016을 유지한다. 기존 `mbti_lab.verify_http`는 임시로 8017을 사용하므로, 이 검사를 할 때 타로 API는 잠시 종료한다.

`GET /api/health`의 `postgres`, `neo4j`, `chroma`, `embedding`, `llm`은 각각 `ok|missing|error`다. 모델 파일이 없어도 API는 시작하고 `embedding: missing`으로 표시한다. 이 경우 생성 요청은 `503 embedding_unavailable`다. 모델·환경 설정을 준비한 후 서버를 재시작한다. LLM의 `ok`는 설정·클라이언트 준비 상태이며 실제 서비스에 유료 검증 호출을 했다는 뜻은 아니다.

기본 정적 실행으로 돌아가려면 새 터미널에서 `VITE_TAROT_API_URL`을 설정하지 않고 `npm run dev` 또는 `npm run build`를 실행한다. GitHub Pages는 타로 서버와 세 DB를 호스팅하지 않는다.

## 뽑기·인증·재개 계약

- 서버가 중복 없는 3장, 방향, 과거/현재/미래 위치를 한 트랜잭션으로 확정한다. 뒤집기 화면은 공개 순서만 정한다.
- 생성은 `Idempotency-Key`(16~128자의 영문·숫자·`_`·`-`)를 받는다. 질문·유형·별자리와 `spread` 외의 카드 지정 필드는 422다.
- 32바이트 무작위 토큰을 첫 201 응답에 한 번 반환하고 DB에는 SHA-256만 저장한다. 읽기·SSE·재개와 생성 재확인에 `Authorization: Bearer`를 쓴다. 토큰이 없거나 다른 세션 토큰이면 404다.
- 같은 토큰·키·입력은 같은 세션을 반환하고, 같은 토큰·키·다른 입력은 409다. **최초 응답이 유실되어 토큰을 아직 못 받은 요청**도 중복 뽑기를 만들지 않도록 bootstrap 키 해시를 별도로 유일하게 저장한다. 이때 동일 키를 토큰 없이 재요청하면 `409 session_token_required`다. 원문 토큰을 복원하거나 재노출하지 않는다. 새 뽑기는 사용자가 새 세션을 선택할 때만 한다.
- SSE는 fetch/ReadableStream이며 `Last-Event-ID` 헤더 이후의 저장된 이벤트만 읽는다. 토큰·질문·API 키를 URL에 넣지 않는다. 새로고침은 같은 세션·방향·카드를 복구한다.
- 실행 중 동일 세션의 재개 요청은 PostgreSQL advisory transaction lock으로 409다. 검수 실패는 최대 2회 재작성, 근거 부족은 생성 호출 없이 `needs_evidence`다. 생성 예외 뒤에는 저장된 검색 결과부터 재개한다.
- 프런트는 세션 ID·접근 토큰·키·질문 입력·마지막 이벤트 ID·공개한 카드 순서를 `sessionStorage`에 보관한다. 저장이 차단되면 접근 정보 유실 가능성을 알린다. 새 세션 버튼은 서버의 과거 이력을 삭제하지 않는다.

API는 `POST /api/readings`, `GET /api/readings/{id}`, `GET /api/readings/{id}/events`, `POST /api/readings/{id}/resume`, `GET /api/cards`, `GET /api/health`를 제공한다. 응답 스키마는 [schemas.py](../tarot_lab/schemas.py)가 기준이다.

## 검증

```powershell
.venv/Scripts/python -m unittest discover -s mbti_lab -p "test_*.py"
.venv/Scripts/python -m unittest discover -s lumi_core -p "test_*.py"
.venv/Scripts/python -m unittest discover -s tarot_lab -p "test_*.py"
.venv/Scripts/python -m mbti_lab.verify_http
cd frontend
npm test
npm run build
```

실제 DB·모델·지식이 준비됐을 때 저장소 루트에서:

```powershell
$env:LUMI_INTEGRATION='1'
.venv/Scripts/python -m unittest discover -s tarot_lab -p "test_*.py"
.venv/Scripts/python tools/verify_corpus_retrieval.py
.venv/Scripts/python tools/evaluate_tarot_retrieval.py
```

통합 테스트는 실제 PostgreSQL·Neo4j·Chroma·LiteRT를 사용하고 **작성·검수만 FakeLLM**으로 수행한다. 실제 LLM 키가 설정돼 있어도 이 테스트용 런타임은 키를 사용하지 않는다. 플래그가 없으면 실 DB 검사는 `LUMI_INTEGRATION not set`으로 건너뛴다. 테스트용 PG 세션은 자신이 만든 ID만 정리한다. Neo4j 시험은 명시적인 `tarot-v1` 지식만 재적재한다.

[30문항 검색 기록](TAROT_RETRIEVAL_CHECKS.json)은 질문 단독과 키워드 확장 검색의 카드·방향 커버리지를 기록한다. 모든 질문에서 세 방향을 회수했고 다른 카드/방향은 반환하지 않았다. 메타데이터 필터의 커버리지 점검이며 사람의 관련성 평가나 LLM 품질 점수가 아니다.

브라우저에서는 실제 세 저장소와 FakeLLM을 연결해 3장 순차 공개, 역방향 표시, 출처, FakeLLM 안내, 새로고침 후 같은 카드·완료 결과 복구를 확인했다. `prefers-reduced-motion`에서 전환을 끄는 CSS를 포함했으나 이번 검증에서 실제 모바일 기기의 성능은 측정하지 않았다.

검증 PC에는 Docker가 없어 공식 EDB PostgreSQL **17.12** 바이너리를 작업 폴더에 두고 127.0.0.1:5433의 별도 테스트 클러스터를 실행했다. compose 파일의 Docker 기동 자체는 실행하지 않았다. 배포용 구성은 위 compose의 암호 설정을 사용한다.

## 보관·정리와 운영 범위

로컬 실험은 자동 만료를 수행하지 않는다. 질문, 뽑기, 리포트, 이벤트, 체크포인트가 유지된다. 정리할 때는 실행을 멈추고 해당 세션의 `PostgresSaver.delete_thread(session_id)`를 호출한 뒤, 동일 세션 ID의 `lumi.reading_sessions` 행을 지운다. 외래 키로 draw·report·event가 함께 정리된다. 체크포인터와 서비스 행을 모두 정리해야 질문 상태가 남지 않는다. Chroma·Neo4j에는 개인 질문을 적재하지 않는다.

공개 운영용 인증·과금 제한·장기 보관 정책·운영 프로세스 복구는 별도 운영 작업이다. 현재 프로세스 재시작은 기록을 복구한 뒤 사용자 재개 요청으로 이어간다. 노드 오류를 빈 검색으로 숨기거나 LLM 미설정을 FakeLLM 성공으로 대체하지 않는다.

# 타로 모드 잔여 개발안 — 서버·3DB·LangGraph

2026-11-23 · **대상: 다음 구현자(Codex)** · 설계 원본은 [TAROT_3DB_LANGGRAPH_PLAN.md](TAROT_3DB_LANGGRAPH_PLAN.md), 원칙은 [CLAUDE_TAROT_IMPLEMENTATION.md](CLAUDE_TAROT_IMPLEMENTATION.md)

이 문서는 설계를 다시 쓰지 않는다. **이미 끝난 부분과 남은 부분을 나누고, 남은 작업을 바로 착수할 수 있는 단위로 정리한다.** 설계 원본의 고정 원칙 10개는 그대로 유효하며, 아래 내용이 원본과 어긋나면 원본이 기준이다.

---

## 1. 지금까지 구현된 것 (재구현 금지)

| 영역 | 상태 | 위치 |
| --- | --- | --- |
| 카드 이미지 78장 + 뒷면 | 완료. 마이너 합본 4장을 개별 56장으로 분리, 전부 WebP | `frontend/public/tarot/`, 생성기 `tools/build_tarot_assets.py` |
| 카드 카탈로그 | 완료. 78장 ID·아르카나·수트·랭크·원소·이미지 경로 | `frontend/public/tarot/deck.json` |
| React 카드 화면 | 완료. 셔플·부채꼴·3장 선택·중앙 이동·순차 뒤집기·정역방향·키보드·`prefers-reduced-motion` | `frontend/src/tarot/TarotReading.jsx` |
| 뽑기 클라이언트 | 완료. `POST /api/readings` 호출, `Idempotency-Key` 생성, 응답 검증 | `frontend/src/tarot/draw.js` |
| 세션 클라이언트 | 완료. 상태 조회·SSE 진행·재개·카드 불변성 검사·세션 기억 | `frontend/src/tarot/session.js`, `useReadingRun.js` |
| 진행·리포트 UI | 완료. 6단계 진행 표시, 검수 통과 리포트·출처, 오류·재연결·다시 이어가기 | `TarotReading.jsx`, `tarot.css` |
| 미리보기 모드 | 완료. 서버 미설정 시 브라우저 임의 뽑기 + 명시적 안내 | `draw.js: makeProvider` |
| 계약 모의 서버 | 완료. 4개 엔드포인트 인메모리 구현(시나리오 포함). **운영 아님** | `tools/mock_tarot_api.mjs` |
| 프런트 테스트 | 완료. 30개(`npm test`) | `src/tarot/*.test.js` |

**아직 없는 것: PostgreSQL, Neo4j 타로 데이터, Chroma, LangGraph, LLM, FastAPI 서버, 타로 해설 콘텐츠.** 이 문서의 나머지는 전부 그 범위다.

### 1.1 미리보기 모드의 경계

`VITE_TAROT_API`가 비어 있으면 카드는 브라우저가 뽑고 해설은 나오지 않는다. 화면에 "미리보기(연출용)"로 표시된다. 이 경로는 GitHub Pages 배포용이며 **서버 구현의 대체물이 아니다.** 서버가 붙으면 같은 화면이 서버 확정 뽑기로 전환된다.

---

## 2. 프런트가 이미 기대하는 계약 (서버가 맞춰야 할 고정 사양)

프런트가 먼저 구현됐으므로 **이 계약이 서버 구현의 입력**이다. 바꾸려면 프런트도 같이 바꾼다. 모의 서버 `tools/mock_tarot_api.mjs`가 이 계약의 실행 가능한 참조 구현이다.

### 2.1 `POST /api/readings`

요청: 헤더 `Idempotency-Key` 필수. 본문 `{mbti, zodiac_id, question, spread:"three_card_reflection"}`.

- 클라이언트는 카드 ID·방향을 **보내지 않는다.** 서버는 그런 필드가 오면 `400`으로 거절한다.
- 같은 키 + 같은 정규화 입력 → 같은 세션·같은 draw 반환(2xx).
- 같은 키 + 다른 입력 → `409`.
- 응답: `{session_id, status, draws[3], events_url, resumable, error_code}`.

`draws`의 각 원소는 `{card_id, orientation, position, ordinal}`이며 프런트가 다음을 검증하고 어기면 결과를 표시하지 않는다.

- `card_id`는 `deck.json`에 있는 78개 중 하나, **3장 중복 없음**
- `orientation` ∈ `upright|reversed`
- `position` ∈ `past|present|future`, 3개 모두 서로 다름
- `ordinal` 0·1·2, 정렬 후 순서와 일치

### 2.2 `GET /api/readings/{session_id}`

`{session_id, status, draws, resumable, error_code}` + `status == "completed"`일 때만 `{report, evidence[], model_id, prompt_version, completed_at}`.

- `status` 값: `draw_confirmed` | `running` | `completed` | `needs_evidence` | `validation_failed` | `failed`
- `evidence[]`: `{id|chunk_id, title|document_title, source_url}`. `evidence_ids: [...]` 형태도 받는다.
- 프런트는 **`completed`가 아니면 본문을 결과로 표시하지 않는다.** 검수 전 초안을 `report`에 담아 보내지 말 것.
- `404`(없음)·`401/403`(권한 없음)을 구분해서 반환한다.

### 2.3 `GET /api/readings/{session_id}/events` (SSE)

```text
id: 3
event: graph.completed
data: {"paths": 4}
```

이벤트 타입: `session.created`, `draw.confirmed`, `graph.completed`, `retrieval.completed`, `draft.validating`, `report.completed`, `report.needs_evidence`, `run.failed`.

구현 중 확정된 **중요한 3가지**:

1. **`id`는 세션 내 단조 증가 정수(sequence)다.** 프런트는 이 값으로 중복을 제거한다.
2. **재연결 시 `Last-Event-ID` 헤더와 `?last_event_id=N` 쿼리를 모두 지원해야 한다.** 브라우저 `EventSource`는 첫 연결에 헤더를 붙일 수 없어서 프런트가 쿼리로 보낸다. 둘 다 "그 번호 이후"만 재생하라는 뜻이다.
3. **재개(resume) 후에도 sequence를 초기화하지 않는다.** 프런트는 재개 시점의 마지막 번호 이하 이벤트를 무시하므로, 번호를 되돌리면 새 실행의 이벤트가 버려진다. 이전 실행의 `run.failed`가 재생돼도 새 실행을 끝내지 않도록 하는 장치다.

`report.completed`의 `data`에 검수 통과 리포트 본문을 담는다(`{report, evidence, model_id, prompt_version, completed_at}`). 비워 보내면 프런트가 `GET`으로 한 번 더 가져온다. `run.failed`·`report.needs_evidence`의 `data`에는 `{error_code, resumable}`을 담는다. 종료 이벤트 후 스트림을 닫는다.

### 2.4 `POST /api/readings/{session_id}/resume`

같은 카드·같은 판본으로 재실행. `{status, draws?}` 반환. 이미 완료된 세션은 새 뽑기 없이 기존 결과를 반환하고, 실행 중이면 `409`.

### 2.5 카드 ID 어휘

`deck.json`과 DB 카탈로그의 `card_id`가 **문자 단위로 일치**해야 한다.

- 메이저 22장: `major_00` ~ `major_21`
- 마이너 56장: `{wands|cups|swords|pentacles}_01` ~ `_14` (01=ace … 11=page, 12=knight, 13=queen, 14=king)
- 의미 ID: `card_id + ':' + orientation` (예: `major_16:reversed`)
- `deck.json`의 `mapping_version`(현재 `suit-element-practice-1`)은 수트-원소 실습 매핑의 판본이다. 메이저 원소는 의도적으로 비어 있다.

---

## 3. 남은 작업 (착수 순서)

각 작업은 **앞 작업이 끝나야** 검증 가능하다. 환경이 없어 건너뛴 검사는 통과로 보고하지 않는다.

### T1. 패키지 뼈대와 설정

`tarot_lab/` 패키지와 `requirements-tarot.txt`를 만든다. 구성은 설계 원본의 "권장 파일 구성"을 따른다. DB·LLM 클라이언트를 import 시점에 생성하지 않는다(테스트가 설정 없이 돌아야 한다).

- `config.py`: DSN·Neo4j·Chroma·LLM 설정을 환경변수에서 읽고 기본값은 로컬 전용. 비밀값을 기본값으로 넣지 않는다.
- `catalogue.py`: `frontend/public/tarot/deck.json`을 **단일 출처로 읽어** 78장을 로드한다. 카드 목록을 파이썬에 중복 정의하지 않는다.
- **완료 기준**: `python -c "from tarot_lab.catalogue import load_cards; assert len(load_cards())==78"`, 수트별 14장·메이저 22장 검사 통과.

### T2. PostgreSQL 스키마와 확정 뽑기 ← 가장 먼저 쓸모가 생기는 단위

설계 §4의 5개 테이블(`profiles`, `reading_sessions`, `reading_draws`, `reading_reports`, `reading_events`)을 명시적 SQL 마이그레이션으로 만든다. 체크포인터 테이블은 네임스페이스를 분리한다.

`create_or_get_session(input, idempotency_key, owner_scope)`:

- 세션 + draw 3개를 **한 트랜잭션**으로 확정. 일부만 저장된 세션을 정상 반환하지 않는다.
- 카드 선택은 서버 난수(`secrets`). 테스트는 주입 RNG로 재현.
- `UNIQUE(session_id, card_id)` / `(session_id, ordinal)` / `(session_id, position)`로 중복을 DB 레벨에서 막는다.
- `request_hash`는 `mbti|zodiac_id|question.strip()|spread`의 정규화 해시. 같은 키·다른 해시 → `409`.
- **완료 기준**: 재시도 불변성, 동시 요청에서 세션·draw 한 세트만 확정, 78장 중 중복 없는 3장, `409` 분기 테스트 통과.

### T3. 지식 fixture와 Neo4j·Chroma 어댑터

작은 fixture(탑·별·은둔자 3장 × 2방향)로 먼저 경로를 세우고 78장으로 확대한다.

- Neo4j: 설계 §3의 노드·관계. 읽기는 **고정 Cypher + 파라미터만**. 홉 2~3, 경로 ≤30, 키워드 ≤12. 근거 없으면 `insufficient_graph_context`.
- Chroma: 설계 §5의 메타데이터 계약. **카드·방향별로 필터를 걸어 따로 검색한 뒤 합친다.** 방향이 다른 글을 같은 카드의 근거로 대체하지 않는다. 일반 글은 별도 슬롯.
- 적재기 `tools/seed_tarot_knowledge.py`는 안정된 ID로 재실행 가능해야 한다.
- **완료 기준**: 세 카드의 올바른 방향 근거 회수, 잘못된 판본 거부, 근거 없음과 DB 장애 구분, 재적재 후 ID 동일.

### T4. LangGraph 파이프라인

노드: `load_confirmed_draws` → `retrieve_graph` → `retrieve_semantic` → `generate` → `validate` → `persist_report`. 입력 검증·세션 생성은 API 계층에서 이미 끝난 상태로 들어온다.

- 재작성은 `generate`로만 돌아가고 `rewrite_count < 2`(최초 포함 최대 3회). **재작성 루프에서 카드·방향·위치·확정 근거를 바꾸지 않는다.**
- 필수 코드 검사(결정적): 3장·방향·위치가 결과에 모두 포함, 인용 ID가 이번 검색 결과에 실재, 카드별 최소 근거와 방향 일치, 길이(한국어 공백 포함 1,200~2,000자). LLM 검수는 보조이며 필수 검사를 통과시키지 못한다.
- 근거 부족이면 분량을 채우지 말고 `needs_evidence`로 종료.
- 체크포인터 `thread_id = session_id`. 완료 저장과 상태 갱신은 PostgreSQL에서 원자적으로. 같은 세션 동시 실행은 잠금 또는 lease로 방지.
- **완료 기준**: fake LLM으로 정상·2회 재작성·근거 부족·통신 실패·체크포인트 재개·동시 재개 테스트 통과.

### T5. FastAPI와 SSE

§2의 계약을 그대로 구현한다. **모의 서버(`tools/mock_tarot_api.mjs`)와 같은 응답 형태를 내는지 대조하는 것이 가장 빠른 검증이다.**

- `reading_events`에 sequence를 저장하고 SSE `id`로 쓴다. 재개 후에도 증가 유지(§2.3).
- 세션 소유권 확인. 익명 로컬 MVP면 소유 범위·토큰 발급 방식을 문서에 명시하고 공개 배포 전에 인증을 끝낸다.
- API 키·DB 비밀번호·질문 원문을 URL에 넣지 않는다. CORS는 허용 출처를 명시적으로 설정한다.
- **완료 기준**: 4xx 분기, `409`, 소유하지 않은 세션 차단, 중복 이벤트 무해, 단절 후 카드 불변, 저장소 장애의 명시적 상태.

### T6. 해설 콘텐츠

통합 MVP 완료 조건은 **156개 의미 각각이 최소 1개의 해설·출처를 갖는 것**이다. 780개 청크는 그다음 목표다. 유사 문장을 조합 수만큼 복제하지 않는다. 출처 확인·중복 검사·샘플 검수를 통과한 자료만 적재한다.

### T7. 프런트 연결과 문서

- `frontend/.env` 또는 빌드 환경에 `VITE_TAROT_API`를 설정하면 서버 모드로 전환된다. 코드 변경은 필요 없다.
- GitHub Pages 배포는 미리보기 모드로 유지한다(HTTPS 페이지에서 HTTP 백엔드를 전제하지 않는다).
- `docs/TAROT_RUNBOOK.md`를 새로 쓴다: 실제 검증한 의존성 버전, 설정 예시(비밀값 제외), 포트, 마이그레이션·적재·실행·재개·정리 명령, 데이터 판본, 사용한 LLM·임베딩.

---

## 4. 알려진 데이터 공백

| 항목 | 내용 | 권장 처리 |
| --- | --- | --- |
| 마이너 한국어 이름 | `minor-arcana.json`에 `name_ko`가 없어 UI가 영문명을 쓴다. 카드 그림에는 한국어가 있으나 **합본마다 표기 방식이 다르다**(예: `완드 킹` vs `컵의 왕`) | 표기 규칙을 먼저 정한 뒤 56개를 그림과 일치하게 기입 |
| 마이너 크롭 비율 | 합본의 카드마다 원본 비율이 조금씩 달라 공통 2:3으로 정규화했다. 가로 배율이 카드별로 0.88~1.06배 달라진다 | 원본 카드별 이미지를 새로 생성하면 해소 |
| 메이저 원소·점성술 대응 | 유파별로 달라 비워 둠 | 출처·체계를 정한 항목만 `mapping_version`을 올려 추가 |
| 역방향 해설 | 없음 | T6에서 방향별로 작성. 역방향을 일괄 부정적으로 쓰지 않는다 |

---

## 5. 검증 명령

```bash
# 기존 회귀 (현재 통과)
python -m unittest discover -s mbti_lab -p "test_*.py"     # 7 tests
cd frontend && npm test                                     # 30 tests
npm run build

# 프런트를 계약에 대고 수동 확인
node tools/mock_tarot_api.mjs --port 8787
cd frontend && VITE_TAROT_API=http://127.0.0.1:8787 npm run dev
# 질문에 [needs_evidence] / [fail_once] / [slow]를 넣으면 해당 상태를 재현한다 (모의 서버 전용)
```

신규 서버 작업은 `tarot_lab/tests/`에 추가하고, 실제 DB·LLM이 필요한 통합 테스트는 별도 표시해 설정이 없으면 건너뛴 이유를 출력한다.

---

## 6. 보고 시 주의

- `89,856`은 한 카드가 한 위치에 놓이는 조건 조합 수다. 적재한 해설 수가 아니다.
- 콘텐츠 20~60배는 목표 산식이며 달성 실적이 아니다.
- 품질 향상률·"환각 없음"은 별도 평가 전에 주장하지 않는다.
- 건너뛴 검사를 통과로 적지 않는다. 최종 보고에 실제 구현 범위, 실행 명령, 통과한 검사, 생략한 검사와 이유, 알려진 제한, 변경 파일을 적는다.

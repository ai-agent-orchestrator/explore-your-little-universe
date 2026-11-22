# Lumi 타로 확장 — 리팩터링 개발안 (Claude → Codex)

2026-11-22 · Codex 전달용 실행 지시서 · 기준 커밋 `9564079` (`main`)

이 문서는 [CLAUDE_TAROT_IMPLEMENTATION.md](CLAUDE_TAROT_IMPLEMENTATION.md)(이하 **인계서**)와 [TAROT_3DB_LANGGRAPH_PLAN.md](TAROT_3DB_LANGGRAPH_PLAN.md)(이하 **설계서**)에 대한 Claude의 검토 결과이자 실행 계획이다.

- 인계서의 **고정 원칙 1~10은 전부 그대로 유지**한다. 이 문서는 원칙을 바꾸지 않는다.
- 바뀌는 것은 세 가지다: ① 타로 기능 전에 **R0 기반 정리 단계**를 추가한다. ② 인계서가 열어 둔 구현 선택지를 **확정**한다(§3). ③ 단계를 **PR 단위(R0~R6)**로 다시 나누고 PR마다 완료 기준을 둔다.
- 두 문서가 충돌하면 이 문서의 §3 결정이 우선이다. 그 밖에는 인계서를 따른다.

---

## 1. 코드 리뷰 결과 — 타로를 얹기 전에 정리할 것

현재 코드는 600개 코퍼스, 정적 스냅샷, Neo4j 시드 기능을 갖추고 동작한다. 다만 데이터 정의·시드 Cypher·접속 설정이 여러 실행 스크립트에 흩어져 있다. 이 상태로 `tarot_lab`이 `mbti_lab`의 내부 상수를 import하기 시작하면 결합이 더 깊어진다.

| # | 문제 | 근거 위치 | 타로 단계에서 생기는 위험 |
| --- | --- | --- | --- |
| D1 | 시드 Cypher를 실행 스크립트끼리 import한다 | `astrology.py`·`rag_seed.py`가 `from .server import SEED`; `rag_seed.py`가 `from .astrology import SIGNS, SEED` | 타로 시드가 `server.py`(HTTP 서버)를 import하게 됨. 서버 코드 수정이 시드를 깨뜨림 |
| D2 | `SharedTrait` 라벨이 **적재 순서에 의존**한다 | `server.SEED`는 `MbtiTrait`만 만들고, `astrology.SEED`의 `SET t:SharedTrait`가 실행돼야 라벨이 붙음. `generate_browser_import.py`는 `SharedTrait:MbtiTrait`를 한 번에 만듦 | `server --seed`만 실행한 DB에서는 타로 규칙 `-[:RELATES_TO]->(SharedTrait)`가 조용히 0건 매칭 |
| D3 | 지연 import로 순환 참조를 감춘다 | `data.result()` → `interpretations`; `interpretations` → `astrology`, `scenarios`; `scenarios.cards()` → `interpretations`, `everyday` | 타로 코퍼스가 `cards()`에 합류하면 순환이 하나 더 생김 |
| D4 | MBTI/별자리 행 빌더가 3곳에 중복된다 | `astrology.main`, `rag_seed.main`, `server.main(--seed)`의 `mbti_rows`/`rows` 리스트 컴프리헨션 | 원소(Element) 같은 필드를 추가할 때 한 곳만 고치는 실수 |
| D5 | Neo4j 접속 코드가 3벌이다 | `ohgi_graph.py`(식당 프로젝트에서 온 이름), `server.py`, `astrology.py`가 각자 `.env.mbti`를 읽음 | PostgreSQL·Chroma·LLM 설정이 더해지면 설정 소스가 5개 이상으로 늘어남 |
| D6 | 임베딩 전처리가 3곳에 하드코딩돼 있다 | `rag_seed.py` `card['title'] + '\n' + card['text']`, `embedding.js` `card.title+'\n'+card.text`, 프로필 문자열 `...:plain-v1` | Chroma 적재·질의에서 전처리가 다르면 벡터 공간이 섞임 (원칙 6 위반) |
| D7 | 임베더가 `neo4j_graphrag.Embedder`를 상속하고 모듈 최상단에서 import한다 | `mbti_lab/embedding.py` 1행대 | Chroma·FastAPI 경로에도 neo4j-graphrag 의존이 생김 |
| D8 | 청크 스키마가 dict 관례로만 존재한다 | `interpretations.py`·`everyday.py`·`scenarios.py`·`rag_seed.SEED`·`generate_browser_import.py`가 같은 키 목록을 각자 나열 | `card_id`·`orientation`·`content_hash` 추가 시 5곳을 고쳐야 함 |
| D9 | 프런트 `main.jsx`가 단일 컴포넌트·압축 서식이다 | `App` 하나가 상태·검색·전체 화면을 렌더 | 타로 모드를 넣으면 정적 모드 회귀 위험과 diff 노이즈가 큼 |
| D10 | 기본 `requirements.txt`에 `openai`가 들어 있다 | `test_kg_pipeline.py`의 스모크 테스트만 사용 | 의존성 경계가 흐려짐 (치명적이지는 않음. §3-K 참고) |

**R0 원칙: 동작 변경 없는 이동.** R0에서는 위 부채를 정리하되 `cards()` 결과, `graph.json`, `cypher/lumi_graph_only_seed.cypher`, HTTP 응답이 **바이트 단위로 동일**해야 한다.

---

## 2. 목표 구조

```text
lumi_core/                    # 신규. 모드와 무관한 공유 도메인·인프라 (DB 클라이언트는 import 시 생성 금지)
  versions.py                 # DATASET_VERSION, MAPPING_VERSION, EMBEDDING_PREPROCESSING='plain-v1'
  settings.py                 # .env.mbti(Neo4j) + .env.tarot(PG·LLM·Chroma) 단일 로더, 지연 평가
  catalog/
    traits.py                 # TRAITS, TYPES, SUGGESTIONS  (← data.py, scenarios.py에서 이동)
    zodiac.py                 # SIGNS + element  (← astrology.py에서 이동, element 필드 추가)
    tarot.py                  # 78장·156 의미·suit→element (R1에서 추가)
  corpus/
    chunk.py                  # Chunk 스키마(TypedDict) + embedding_text() + content_hash()
    lumi.py                   # cards() 조립 (← scenarios.cards), 순환 import 제거
  graph/
    client.py                 # get_driver/run/database (← ohgi_graph.py)
    seeds.py                  # MBTI/ZODIAC/RAG 시드 Cypher + trait_rows()/sign_rows() 빌더
  embedding/
    litert.py                 # LiteRT 엔진·프로필 (neo4j_graphrag 비의존)

mbti_lab/                     # 기존 경로 유지. 이동한 심볼은 re-export만 남김
  data.py, astrology.py, scenarios.py, embedding.py, rag_seed.py, server.py ...
ohgi_graph.py                 # lumi_core.graph.client re-export shim (삭제하지 않음)

tarot_lab/                    # 인계서의 권장 구성을 따르되 §3 결정 반영
  api.py, schemas.py, llm.py, config.py
  repositories/{postgres,neo4j,chroma}.py
  workflow/{state,nodes,graph,validators}.py
  migrations/0001_init.sql
  fixtures/meanings_v1.py     # 직접 작성한 156 의미 + 청크
  compose.yaml                # 127.0.0.1 바인딩 PostgreSQL만
  tests/
tools/seed_tarot_knowledge.py
frontend/src/
  App.jsx                     # 모드 전환 셸 (신규)
  static/StaticExplorer.jsx   # 기존 App 본문을 그대로 이동
  tarot/                      # React.lazy로 분리 로드
```

`mbti_lab`의 공개 실행 명령(`python -m mbti_lab.server`, `.astrology`, `.rag_seed`, `.verify_http`)과 테스트의 import 경로(`mbti_lab.scenarios.RAW_CARDS`, `mbti_lab.scenarios.cards` 등)는 **모두 그대로 동작**해야 한다. `RAW_CARDS`는 기존 ID·본문 보존 테스트가 참조하므로 `scenarios.py`에 둔다.

```mermaid
flowchart LR
  subgraph core[lumi_core]
    CAT[catalog] --> COR[corpus]
    COR --> SEED[graph.seeds]
    EMB[embedding.litert]
  end
  MBTI[mbti_lab · 호환 shim + CLI] --> core
  TAROT[tarot_lab] --> core
  TOOLS[tools/*] --> core
  FE[frontend/static] -. graph.json .- MBTI
  FE2[frontend/tarot] -- HTTP/SSE --> TAROT
```

의존 방향은 `mbti_lab → lumi_core`, `tarot_lab → lumi_core`만 허용한다. `tarot_lab`은 `mbti_lab`을 import하지 않는다. `lumi_core`는 두 랩을 import하지 않는다. R0에서 이 규칙을 검사하는 테스트를 추가한다(§4 R0).

---

## 3. 확정 결정 (인계서 대비)

| ID | 주제 | 인계서 상태 | **확정** |
| --- | --- | --- | --- |
| A | 단계 순서 | 1단계 PG부터 | **R0 정리 → R1 카탈로그·스키마 → R2 PG 뽑기 → R3 지식 적재·검색 → R4 LangGraph → R5 API → R6 화면** |
| B | 공유 코드 위치 | "같은 책임 모듈이 있으면 통합" | `lumi_core` 신설. `tarot_lab → mbti_lab` import 금지 |
| C | 카드 ID | 미정 | `major-00-fool` … `major-21-world`, `{wands,cups,swords,pentacles}-{01..14}-{ace,two,…,page,knight,queen,king}`. `meaning_id = f"{card_id}:{orientation}"` |
| D | 원소 대응 | 마이너만 버전 붙여 사용 | 확정: suit→element(`wands/fire, cups/water, swords/air, pentacles/earth`), 별자리→고전 4원소. `mapping_version='element-classical-v1'`. **메이저 22장의 `element`는 null**로 두고 `Archetype`·`InterpretationRule` 경로로만 연결 |
| E | Chroma 실행 방식 | 미정 | `chromadb.PersistentClient(path=settings.chroma_path)` 임베디드 모드. 경로 기본값 `data/chroma/`(gitignore 추가). 별도 Chroma 서버는 1차 범위 밖 |
| F | Chroma 임베딩 | "다른 모델 섞지 말 것" | **Chroma 기본 임베딩 함수를 절대 쓰지 않는다.** 컬렉션 생성 시 `embedding_function=None`, 적재는 `embeddings=`, 질의는 `query_embeddings=`로 직접 전달. 벡터는 `lumi_core.embedding.litert`(기존 LiteRT, 768차원, normalize)로 계산. 컬렉션 이름 `lumi_{DATASET_VERSION}_{profile_sha8}`, 컬렉션 metadata에 `embedding_profile` 저장 후 기동 시 비교 |
| G | Chroma 거리 | "cosine 또는 거리 정의 반환" | cosine 공간으로 생성. 설정 키는 **고정한 chromadb 버전 문서로 확인**(구버전 `metadata={"hnsw:space":"cosine"}` / 신버전 `configuration`). 응답에는 `distance`와 `similarity = 1 - distance`를 모두 담음 |
| H | Chroma 메타데이터 null | 미정 | Chroma 메타데이터는 None 값을 허용하지 않는다. 비어 있는 필드는 `''`로 저장. 기존 600개 청크는 `card_id=''`, `orientation=''` |
| I | PostgreSQL 기동 | 미정 | `tarot_lab/compose.yaml`에 PostgreSQL만 정의하고 `127.0.0.1:5433:5432`로 바인딩(로컬 기본 5432와 충돌 방지). Neo4j는 기존 Desktop의 `mbti-zodiac` 재사용 |
| J | 체크포인터 | PostgreSQL | `langgraph-checkpoint-postgres`의 saver를 사용. 서비스 테이블은 `lumi` 스키마, 체크포인터 테이블은 `langgraph` 스키마(연결의 `search_path`로 분리). 정확한 클래스명·`setup()` 호출 방식은 고정 버전 문서로 확인 |
| K | LLM 어댑터 | "설정 기반 어댑터·fake" | 이미 의존성에 있는 `openai` SDK로 **OpenAI 호환 엔드포인트** 어댑터 하나만 작성(`LUMI_LLM_BASE_URL`, `LUMI_LLM_MODEL`, `LUMI_LLM_API_KEY`). 미설정이면 `llm_not_configured` 오류. 테스트는 `FakeLLM`만 사용 |
| L | 세션 소유권 | "토큰 발급 방식 명시" | 세션 생성 시 32바이트 랜덤 `session_token` 발급, DB에는 SHA-256 해시만 저장. 클라이언트는 `Authorization: Bearer`로 전송 |
| M | SSE 클라이언트 | `Last-Event-ID` | 브라우저 `EventSource`는 헤더를 보낼 수 없어 L과 충돌한다. **`fetch` + `ReadableStream` 기반 SSE 리더**를 프런트에 구현(토큰을 URL에 넣지 않기 위함). 재연결 시 `Last-Event-ID` 헤더를 직접 전송 |
| N | 포트 | 미정 | 기존 `mbti_lab.server` 8016 유지, 타로 API **8017**, Vite 5173. CORS는 `http://127.0.0.1:5173`만 허용 |
| O | 동시 실행 방지 | "DB 잠금 또는 lease" | 그래프 실행 시작 시 `pg_try_advisory_xact_lock(hashtextextended(session_id::text, 0))` 획득 실패면 `409 run_in_progress` |
| P | 서버 측 질의 임베딩 | 미정 | FastAPI lifespan에서 LiteRT CPU 엔진을 **한 번만** 생성하고 lock으로 직렬화(기존 `LiteRTEmbeddings`와 동일 방식). 모델 파일이 없으면 기동 실패가 아니라 `/api/health`에 `embedding: missing` 표시, 리딩 요청은 `503 embedding_unavailable` |
| Q | 테스트 러너 | unittest | 기존대로 `unittest` 유지. 타로 테스트는 `tarot_lab/tests/test_*.py`. 실 DB 통합 테스트는 `LUMI_INTEGRATION=1`일 때만 실행, 아니면 `skipTest('LUMI_INTEGRATION not set')` |
| R | 정적 스냅샷 | 언급 없음 | 타로 청크는 **`graph.json`에 넣지 않는다.** 정적 번들 크기·GitHub Pages 동작을 그대로 유지. `cards()`(600개)와 `tarot_chunks()`는 별도 함수 |
| S | 프런트 분리 | "별도 진입" | `VITE_TAROT_API_URL`이 빌드 시 비어 있으면 타로 탭을 렌더하지 않는다. 타로 코드는 `React.lazy`로 분리해 정적 모드 초기 번들에 포함하지 않는다 |

---

## 4. PR 단위 실행 계획

각 PR은 독립적으로 리뷰·되돌리기 가능해야 한다. PR마다 "기존 회귀 검증"(§6)을 실행하고 결과를 PR 설명에 적는다. 작업 브랜치 예시: `refactor/r0-lumi-core`, `feat/tarot-r1-catalog` …

### R0 — `lumi_core` 추출 (동작 변경 없음)

1. **골든 파일 기록 (첫 커밋)**: 리팩터링 전에 다음을 `lumi_core/tests/golden/`에 저장한다.
   - `sha256(json.dumps(cards(), ensure_ascii=False, sort_keys=True))`
   - `tools/generate_browser_import.py` 실행 결과(`cypher/lumi_graph_only_seed.cypher`)의 sha256
   - `mbti_lab.data.result(code)` 16개 유형 응답의 sha256
2. 이동: `TRAITS/TYPES/SUGGESTIONS` → `catalog/traits.py`, `SIGNS` → `catalog/zodiac.py`, 시드 Cypher·행 빌더 → `graph/seeds.py`, `ohgi_graph` → `graph/client.py`, `cards()` 조립 → `corpus/lumi.py`. 기존 모듈에는 `from lumi_core... import X` re-export만 남긴다.
3. `graph/seeds.py`의 MBTI 시드를 `MERGE (t:MbtiTrait {key: row.key}) SET t:SharedTrait`로 바꿔 D2 순서 의존을 제거한다. 최종 DB 상태는 기존 `rag_seed` 실행 결과와 같다.
4. `corpus/chunk.py`:
   ```python
   class Chunk(TypedDict):
       id: str; title: str; text: str; category: str
       traits: list[str]; tips: list[str]
       kind: str; subject_kind: str; subject: str; facet: str
       document_id: str; document_title: str; source: str
       source_url: str; reviewed_on: str; editorial_note: str
       # R1에서 NotRequired로 추가: card_id, orientation, position, topic, locale,
       # dataset_version, content_hash

   def embedding_text(chunk) -> str:      # plain-v1, 유일한 정의
       return chunk['title'] + '\n' + chunk['text']

   def content_hash(chunk) -> str:        # sha256(embedding_text) 앞 16자
       ...
   ```
   `rag_seed.py`는 `embedding_text()`를 호출하도록 바꾼다. `frontend/src/embedding.js`의 같은 식에는 `// must match lumi_core.corpus.chunk.embedding_text (plain-v1)` 주석만 추가한다.
5. `embedding/litert.py`로 엔진·`sha256`·`validate_vector`·프로필 생성을 옮긴다. `mbti_lab/embedding.py`의 `LiteRTEmbeddings(Embedder)`는 이 엔진에 위임하는 얇은 래퍼로 남긴다(neo4j-graphrag 의존은 여기에만).
6. `settings.py`: `neo4j()`, `postgres()`, `chroma_path()`, `llm()`을 호출 시점에 평가하는 함수로 만든다. `project_database()` 가드는 유지한다.
7. 의존 방향 테스트 `lumi_core/tests/test_boundaries.py`: `lumi_core` 하위 파일의 AST를 읽어 `mbti_lab`·`tarot_lab` import가 없는지 확인한다(R1 이후에는 `tarot_lab`이 `mbti_lab`을 import하지 않는지도 확인).

**완료 기준**: 골든 sha256 3종 일치, 기존 Python 7개·프런트 9개 테스트 통과, `verify_http` 16유형 통과, `npm run build` 성공, 경계 테스트 통과. `graph.json`은 이 PR에서 변경 파일 목록에 없어야 한다.

### R1 — 타로 카탈로그와 스키마 확장

- `catalog/tarot.py`: 78장 `TarotCard(card_id, arcana, suit, rank, name_ko, name_en, element|None)`, `ORIENTATIONS=('upright','reversed')`, `POSITIONS=('past','present','future')`, `meanings()` → 156개.
- `catalog/zodiac.py`: `SIGNS`에 element 추가(양자리·사자자리·사수자리 fire / 황소자리·처녀자리·염소자리 earth / 쌍둥이자리·천칭자리·물병자리 air / 게자리·전갈자리·물고기자리 water). 기존 `SIGNS` 튜플 형태를 쓰는 코드가 깨지지 않도록 **새 상수 `SIGN_ELEMENTS: dict[str, str]`**로 추가하고 튜플은 그대로 둔다.
- `Chunk`에 타로 필드를 `NotRequired`로 추가하고 `tarot_chunk(...)` 빌더를 만든다.
- `tarot_lab/fixtures/meanings_v1.py`: 먼저 **탑·별·은둔자 × 2방향 × 5주제 = 30청크**만 직접 작성한다. 출처 필드는 `source_kind='authored'`, `source='Lumi 편집 · 직접 작성한 타로 성찰 문장 v1'`. 외부 해설서 문장을 옮기지 않는다.

**완료 기준**: 카드 78·의미 156·메이저 22·suit별 14 검증, ID 유일성, fixture 30청크 전부 `card_id`/`orientation`이 카탈로그에 존재, R0 골든 해시 불변(600개 `cards()`는 그대로).

### R2 — PostgreSQL 세션·확정 뽑기

- `migrations/0001_init.sql`: 설계서 §4 테이블을 `lumi` 스키마에 생성한다. 핵심 제약:
  ```sql
  CREATE TABLE lumi.reading_sessions (
    session_id uuid PRIMARY KEY,
    owner_token_hash bytea NOT NULL,
    idempotency_key text NOT NULL,
    request_hash bytea NOT NULL,
    mbti text NOT NULL, zodiac_id text NOT NULL, question text NOT NULL,
    spread text NOT NULL CHECK (spread = 'three_card_reflection'),
    dataset_version text NOT NULL, mapping_version text NOT NULL, embedding_profile text NOT NULL,
    status text NOT NULL, error_code text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (owner_token_hash, idempotency_key)
  );
  CREATE TABLE lumi.reading_draws (
    session_id uuid REFERENCES lumi.reading_sessions ON DELETE CASCADE,
    ordinal smallint CHECK (ordinal BETWEEN 0 AND 2),
    position text CHECK (position IN ('past','present','future')),
    card_id text NOT NULL,
    orientation text CHECK (orientation IN ('upright','reversed')),
    PRIMARY KEY (session_id, ordinal),
    UNIQUE (session_id, position), UNIQUE (session_id, card_id)
  );
  ```
  `reading_reports`, `reading_events(session_id, sequence, …, UNIQUE(session_id, sequence))`도 같은 파일에 만든다. 마이그레이션 실행기는 `schema_migrations` 테이블에 적용 기록을 남기는 50줄 이하 스크립트로 충분하다(ORM 도입 금지).
- `repositories/postgres.py`의 `create_or_get_session(input, idempotency_key, owner_token_hash, rng)`: `INSERT … ON CONFLICT (owner_token_hash, idempotency_key) DO NOTHING RETURNING` 후 충돌이면 기존 행을 읽어 `request_hash`를 비교한다(같으면 기존 세션, 다르면 `IdempotencyConflict`). 세션·draw 3행·`draw_confirmed` 이벤트를 **한 트랜잭션**에서 기록한다.
- RNG: 운영은 `secrets.SystemRandom()`, 테스트는 `random.Random(seed)` 주입. `rng.sample(CARDS, 3)` + 카드별 `rng.random() < 0.5`로 방향을 정한다.
- 익명 사용자도 세션마다 토큰을 갖는다. 같은 브라우저에서 재시도하려면 프런트가 토큰과 `Idempotency-Key`를 함께 보관해야 한다(R6).

**완료 기준**: 인계서 1단계 완료 기준 + 동시 요청 테스트(스레드 8개가 같은 키로 호출 → 세션 1개·draw 3행), 트랜잭션 중간 실패 주입 시 행 0개. 실 PG 테스트는 `LUMI_INTEGRATION=1`.

### R3 — 지식 적재와 두 검색 어댑터

- `tools/seed_tarot_knowledge.py --dataset tarot-v1 [--neo4j] [--chroma]`
  - Neo4j(`mbti-zodiac` DB, 모든 신규 노드에 `dataset_id='tarot-v1'`):
    ```text
    (:TarotCard {card_id})-[:HAS_MEANING]->(:TarotMeaning {meaning_id, orientation})
    (:TarotCard)-[:ASSOCIATED_WITH]->(:Element {id})      # 마이너만
    (:ZodiacSign)-[:ASSOCIATED_WITH]->(:Element)          # 12개, mapping_version 속성
    (:TarotMeaning)-[:SYMBOLIZES]->(:Archetype {id})
    (:TarotMeaning)-[:HAS_RULE]->(:InterpretationRule {id, effect, mapping_version, source_id})
          -[:RELATES_TO]->(:SharedTrait)
    (:InterpretationRule)-[:FROM_SOURCE]->(:InterpretationSource)
    (:TarotMeaning)-[:DESCRIBED_BY]->(:RagChunk)-[:FROM_DOCUMENT]->(:RagDocument)
    ```
    제약: `TarotCard.card_id`, `TarotMeaning.meaning_id`, `InterpretationRule.id`, `Element.id`, `Archetype.id` UNIQUE. 시드는 전부 `MERGE`로 재실행 가능하게 하고, 기존 라벨의 노드를 `DELETE`하지 않는다. 타로 `RagChunk`에는 `embedding` 속성을 저장하지 않는다(벡터는 Chroma만). 기존 `mindmap_chunk_embedding` 인덱스 결과에 타로 청크가 섞이지 않게 하기 위함이다.
  - Chroma: 600개 기존 청크 + 타로 청크를 같은 컬렉션에 `ids=chunk_id`, `documents=text`, `embeddings=LiteRT(embedding_text(c))`, `metadatas=`(§3-H 규칙)로 `upsert`한다. 기존 600개 벡터는 `graph.json`의 벡터를 그대로 재사용할 수 있다(같은 sha256·plain-v1일 때만, `rag_seed.py`의 캐시 규칙과 동일).
- `repositories/neo4j.py`: 고정 Cypher 3개만 노출한다.
  1. `meaning_paths(meaning_ids, mbti, zodiac_id, mapping_version, limit=30)` — 의미 → 규칙 → SharedTrait ← (MbtiType|ZodiacSign), 규칙의 출처 포함
  2. `element_paths(card_ids, zodiac_id, mapping_version)` — 카드 원소와 별자리 원소의 일치/불일치
  3. `meaning_keywords(meaning_ids)` — Archetype·규칙 키워드 최대 12개
  결과가 0건이면 `[]`, 드라이버 예외는 `GraphUnavailable`로 구분한다.
- `repositories/chroma.py`: `search_for_draw(query_vec, card_id, orientation, k=3)`(where `$and` 필터), `search_general(query_vec, k=3)`(where `card_id == ''`), 그리고 질문 단독 벡터 / 질문+키워드 벡터 두 번의 결과를 모두 반환한다.

**완료 기준**: 인계서 2단계 완료 기준 + 재적재 2회 후 노드·청크 수 불변, 기존 600개 Neo4j 벡터 검색 결과 불변(`verify_corpus_retrieval.py`), 역방향 질의에 정방향 청크가 0건, 컬렉션 `embedding_profile` 불일치 시 `ProfileMismatch`.

### R4 — LangGraph 파이프라인

- 노드는 인계서 그대로: `load_confirmed_draws → retrieve_graph → retrieve_semantic → generate → validate → persist_report`. 노드 함수는 **저장소·LLM을 인자로 주입받는 순수 함수**로 작성하고 `graph.py`에서 `functools.partial`로 연결한다.
- 상태: 인계서 `ReadingState`를 그대로 쓰되 리스트 필드는 노드가 **덮어쓰기**로 반환한다(reducer로 누적하지 않음). 재작성 루프에서 `chunks`·`graph_paths`가 중복 누적되지 않게 하기 위함이다.
- 조건부 엣지 `route_after_validate(state)`:
  - 필수 검사 통과 → `persist_report`
  - 근거 부족(`missing_evidence_for_card`) → `persist_needs_evidence` (재작성하지 않음)
  - 그 외 실패 & `rewrite_count < 2` → `generate`
  - 그 외 → `persist_failed(validation_failed)`
- `validators.py` 필수 검사(코드, LLM 비의존): 카드 섹션 3개에 `card_id`·`orientation`·`position` 모두 존재 / 인용 ID ⊆ 이번 실행의 `chunks ∪ graph_paths` ID / 카드별 해당 방향 청크 ≥ 1 / 본문 1,200~2,000자(공백 포함) / 역방향 섹션에 금지 표현 사전(`불길`, `최악`, `저주` 등 운영 중 확장) 미포함.
- `generate`는 LLM에 **JSON 구조 출력**(카드별 섹션 + `citations[]` + `summary` + `small_action`)을 요구하고, 검수 통과 후 서버가 마크다운으로 조립한다. 자유 텍스트에서 인용을 정규식으로 긁어내는 방식은 쓰지 않는다.
- 체크포인터 `thread_id = str(session_id)`. 실행 진입 시 `reading_reports`에 완료 행이 있으면 그래프를 돌리지 않고 반환한다.

**완료 기준**: 인계서 3단계 완료 기준(FakeLLM: 정상 / 2회 재작성 후 통과 / 근거 부족 / LLM 예외 / 체크포인트 재개 / 동시 재개 409).

### R5 — FastAPI

- `tarot_lab/api.py`, `uvicorn tarot_lab.api:app --host 127.0.0.1 --port 8017`.
- 엔드포인트는 설계서 §7 그대로. 응답 스키마는 `schemas.py`의 pydantic 모델이 단일 출처다.
- `POST /api/readings` → `201 {session_id, session_token, status, draws, events_url}` (토큰은 생성 응답에서만 1회 반환).
- 그래프 실행은 `POST` 응답 후 백그라운드 태스크로 시작한다. 이벤트는 `reading_events`에 먼저 쓰고 SSE는 DB를 읽어 전송한다(프로세스 재시작 후에도 `Last-Event-ID` 복구 가능).
- `GET /api/health` → `{postgres, neo4j, chroma, embedding, llm}` 각각 `ok|missing|error`.

**완료 기준**: 인계서 4단계 완료 기준 + 토큰 없는/다른 토큰 요청 404(존재 여부 노출 방지), 요청 본문의 `card_id`·`draws` 필드 422.

### R6 — React 타로 모드

1. **순수 이동 커밋**: 기존 `App`을 `static/StaticExplorer.jsx`로 그대로 옮기고 `App.jsx`가 렌더만 한다. 서식 변경 금지. 이 커밋 후 `npm test`·`npm run build` 통과, Pages 결과 동일.
2. **모드 셸 커밋**: `App.jsx`에 `정적 탐색 | 타로 실험(로컬 서버)` 탭. `import.meta.env.VITE_TAROT_API_URL`이 없으면 탭을 숨긴다. 모드는 URL hash(`#tarot`)로 유지한다.
3. **타로 화면**: `tarot/TarotMode.jsx`(lazy), `tarot/api.js`(fetch + SSE 리더), `tarot/Card.jsx`. 셔플·선택·순차 뒤집기 연출은 **서버 응답 이후** 시작한다. 사용자가 3장을 "고르는" UI는 공개 순서만 정하며 결과 카드를 바꾸지 않는다.
4. `session_token`·`Idempotency-Key`·`session_id`는 `sessionStorage`에 저장(try/catch). 새로고침 시 같은 세션을 이어 표시한다.
5. 카드 이미지가 없을 때의 텍스트 카드(이름·방향·위치)를 기본값으로 하고, `prefers-reduced-motion`이면 뒤집기 애니메이션을 끈다. 역방향은 카드 180° 회전 + 텍스트 라벨로 함께 표시한다.
6. `search.test.js` 옆에 `tarot/sse.test.js`(청크 경계에 걸친 이벤트 파싱, `id:` 추적)를 추가하고 `package.json`의 `test` 스크립트에 포함한다.

**완료 기준**: 인계서 5단계 완료 기준 + `VITE_TAROT_API_URL` 없이 빌드한 `dist`의 초기 JS에 타로 코드 미포함(빌드 산출물의 청크 분리 확인), GitHub Actions 배포 워크플로 수정 없음.

---

## 5. 콘텐츠 확장 순서

| 단계 | 내용 | 청크 수 | 시점 |
| --- | --- | ---: | --- |
| C1 | 탑·별·은둔자 × 2방향 × 5주제 | 30 | R1 (파이프라인 검증용) |
| C2 | 156 의미 × `general` 1개 | 156 | R3 완료 직후. **MVP 완료 조건** |
| C3 | 156 의미 × 5주제 | 780 | 인계서의 "첫 연결 시험" 목표 |
| C4 | 위치·관점 확장 | 14,040~35,100 | 평가 세트(30문항) 비교 후 결정 |

C2~C4 문장은 작성 후 `content_hash` 중복 검사와 "방향 반전 검사"(정방향 문장이 역방향 청크에 복사되지 않았는지 n-gram 유사도로 확인)를 통과해야 적재한다. 숫자 목표 달성을 위해 템플릿 치환으로 문장을 대량 생성하지 않는다.

---

## 6. 검증 명령

PR마다 기존 회귀 검증을 실행한다(Windows PowerShell 기준, 저장소 관례 유지).

```powershell
.venv/Scripts/python -m unittest discover -s mbti_lab -p "test_*.py"
.venv/Scripts/python -m unittest discover -s lumi_core -p "test_*.py"     # R0~
.venv/Scripts/python -m unittest discover -s tarot_lab -p "test_*.py"     # R1~
.venv/Scripts/python -m mbti_lab.verify_http
cd frontend; npm test; npm run build
```

실 DB 통합 검증(R2~):

```powershell
docker compose -f tarot_lab/compose.yaml up -d
$env:LUMI_INTEGRATION=1
.venv/Scripts/python -m tarot_lab.migrate
.venv/Scripts/python -m tools.seed_tarot_knowledge --dataset tarot-v1 --neo4j --chroma
.venv/Scripts/python -m unittest discover -s tarot_lab -p "test_*.py"
```

`requirements-tarot.txt`는 `-r requirements-rag.txt` 위에 `fastapi`, `uvicorn`, `pydantic`, `psycopg[binary,pool]`, `langgraph`, `langgraph-checkpoint-postgres`, `chromadb`를 추가한다. **버전은 Codex가 실제로 설치·테스트한 조합으로 `==` 고정**하고 RUNBOOK에 적는다. 이 문서는 버전 번호를 지정하지 않는다.

---

## 7. 하지 말 것

- R0에서 `cards()` 결과, `graph.json`, `cypher/lumi_graph_only_seed.cypher`의 내용을 바꾸는 것. 바뀌면 R0가 아니다.
- `mbti_lab` 기존 모듈 파일 삭제 또는 공개 심볼 이름 변경(호환 shim 유지).
- 타로 청크를 `graph.json`·Neo4j 벡터 인덱스에 넣는 것.
- Chroma 기본 임베딩 함수 사용, 또는 LiteRT 외 모델로 만든 벡터를 같은 컬렉션에 넣는 것.
- 클라이언트가 보낸 카드 ID·방향을 공개 API에서 받는 것.
- 토큰·질문·API 키를 URL 쿼리에 넣는 것.
- `docs/images/lumi.svg`와 "Hi, I'm Lumi." 그림 수정.
- `v1` 브랜치 재작성·강제 푸시, Pages 워크플로 수정.
- MBTI·별자리·타로 연결을 과학적 궁합·예측·인과로 표현하는 문구.

---

## 8. PR 보고 형식

각 PR 설명에 다음을 적는다.

```text
## 범위       R? — 한 줄 요약
## 변경 파일  (추가/이동/수정 구분)
## 검증       실행한 명령과 결과 (통과 수 / 실패 수)
## 생략       실행하지 못한 검증과 이유 (예: LUMI_INTEGRATION 미설정)
## 골든      R0 골든 해시 3종 일치 여부
## 다음 PR   다음 단계에서 이어받을 미결 사항
```

건너뛴 테스트를 통과로 보고하지 않는다. 실 DB·실 LLM 검증을 하지 않았다면 "fake만 검증"이라고 명시한다.

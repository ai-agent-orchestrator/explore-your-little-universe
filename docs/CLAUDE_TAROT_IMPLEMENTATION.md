# Claude 개발 인계: Lumi 타로 × PostgreSQL × Neo4j × Chroma × LangGraph

> 이 문서는 최초 설계·인계 시점의 기록입니다. 현재 R0~R6 구현과 실제 검증 범위는 [TAROT_RUNBOOK.md](TAROT_RUNBOOK.md)를 참고하세요.

2026-11-22 · 구현 요청서 · 이 파일 자체는 실행 코드가 아니다.

## 바로 전달할 작업 지시

이 저장소의 **현재 MBTI·별자리 기반 정적 GraphRAG Beta를 유지**하면서, 타로 78장 × 정역방향을 활용하는 별도 서버 실험 모드를 구현한다. [상세 설계](TAROT_3DB_LANGGRAPH_PLAN.md)를 기준으로 아래 순서대로 작동하는 작은 단위부터 완성한다. 문서의 목표를 이미 구현된 기능이나 측정된 성과로 표현하지 않는다.

먼저 `git status`, 현재 브랜치, 저장소의 `AGENTS.md`를 확인하고 사용자의 기존 변경을 보존한다. 최신 `main`을 읽은 뒤 작업한다. 기존 버전은 `v1` 브랜치로 보존한다는 사용자 의도를 존중하고 `v1`을 재작성하거나 강제 푸시하지 않는다. 새로운 기능은 사용 가능한 체크아웃의 적절한 작업 브랜치에서 개발하되, 사용자가 지정한 브랜치·커밋·배포 지시를 우선한다.

## 현재 구현과 반드시 보존할 것

| 항목 | 현재 상태·진입 파일 |
| --- | --- |
| 정적 React 앱 | `frontend/src/main.jsx`, `frontend/src/search.js` |
| 브라우저 임베딩 | `frontend/src/embedding.js`; 고정 LiteRT-LM 모델·768차원·SHA-256·plain-v1 |
| 해설 600개 | 기존 사례 60 + MBTI 해설 160 + 별자리 해설 120 + 추가 사례 260 |
| 데이터 원본 | `mbti_lab/scenarios.py`, `interpretations.py`, `everyday.py` |
| 실제 벡터·그래프 스냅샷 | `frontend/public/data/graph.json` |
| Neo4j 적재·내보내기 | `mbti_lab/rag_seed.py`; 기존 DB 이름 `mbti-zodiac` |
| 기본 로컬 웹앱 | `mbti_lab/server.py`; `--demo`로 DB 없이 화면 확인 |
| 공개 그래프 import | `tools/generate_browser_import.py`, `cypher/lumi_graph_only_seed.cypher` |
| 캐릭터 그림 | **`docs/images/lumi.svg`의 “Hi, I'm Lumi.”와 기존 외형을 그대로 유지** |
| 배포 | GitHub Pages 정적 앱. `main`의 `frontend/**` 변경 시 기존 Actions가 검사·빌드·배포 |

이 인계의 기준 검증: Python 단위 테스트 7개, 프런트엔드 9개, 로컬 HTTP 16유형, 한국어 검색 smoke check 10문항, 프로덕션 빌드. 시작 시 최신 커밋 기준으로 다시 확인한다. `docs/CORPUS_RETRIEVAL_CHECKS.json`은 작은 주제 회수 점검이며 정확도 벤치마크가 아니다.

현재는 **타로 런타임, PostgreSQL, Chroma 온라인 검색, LangGraph, 생성 LLM, 서버 스트리밍이 없다.** 기존 정적 모드는 질문을 애플리케이션 서버에 보내거나 저장하지 않는다. 신규 서버 모드의 저장 동작을 이 설명에 섞지 않는다.

## 구현 결정을 위한 고정 원칙

1. `TarotCard` 78개와 `TarotMeaning` 156개를 분리한다. 공유 카드 노드의 `is_reversed`를 변경하지 않는다. 카드 방향은 의미 노드와 세션의 draw 레코드에 저장한다.
2. 정역방향은 `upright|reversed`, 위치는 `past|present|future`, 카드 순서는 0~2로 통일한다. 메이저 22개 + 4 suit × 14개를 검증한다.
3. 서버가 중복 없이 3장을 확정하고 한 트랜잭션에 기록한다. 프런트의 셔플은 연출이다. 재요청·검수 재작성·실행 재개에서 다시 뽑지 않는다.
4. PostgreSQL은 세션 상태의 기준 저장소다. Neo4j와 Chroma에는 지식만 둔다. 세 DB에 질문 로그를 중복 저장하지 않는다. LangGraph 체크포인트에는 필요한 실행 상태가 저장되므로 보관·삭제 범위를 포함한다.
5. 기존 MBTI·별자리 공통 성향 매핑을 그대로 두고 새로운 상징 규칙은 판본·출처·직접 작성 여부를 기록한다. MBTI·별자리·타로를 과학적 궁합이나 심리적 인과로 표현하지 않는다.
6. DB별로 `dataset_version`·`mapping_version`·`embedding_profile`을 확인한다. 불일치는 명시적 오류다. 기존 임베딩과 다른 모델을 섞지 말고, 모델을 바꾸면 별도 Chroma 컬렉션을 만든다.
7. Neo4j 읽기는 고정 Cypher와 파라미터만 사용한다. 질문을 쿼리 코드에 이어 붙이거나 LLM이 만든 Cypher를 그대로 실행하지 않는다.
8. Chroma는 각 카드·방향별 필터를 적용해 검색한다. 질문 원문과 질문+키워드 검색을 분리해 결과를 비교한다. 반대 방향 글을 같은 카드의 근거로 대체하지 않는다.
9. 원문 근거 없이 분량을 채우지 않는다. 출처가 없으면 `needs_evidence`로 종료한다. 역방향을 일괄적으로 나쁜 결과로 취급하지 않는다.
10. 기존 GitHub Pages는 그대로 실행한다. 새 FastAPI 서비스는 별도 실행이며 GitHub Pages가 서버와 DB를 호스팅한다고 설명하지 않는다.

## 권장 파일 구성

아래는 새로 만들 파일의 제안이다. 기존 구조를 살펴보고 같은 책임의 모듈이 있으면 통합한다.

```text
tarot_lab/
  config.py                 # 별도 서버 모드 설정·판본·로컬 실행 기본값
  schemas.py                # API, draw, evidence, 상태 스키마
  catalogue.py              # 카드 78장·방향·실습 원소 매핑
  fixtures/                 # 직접 작성·출처를 기록한 작은 타로 코퍼스
  repositories/
    postgres.py             # 세션·뽑기·이벤트·리포트
    neo4j.py                # 타입·별자리·카드의 제한된 근거 경로
    chroma.py               # 카드·방향·판본별 의미 검색
  workflow/
    state.py
    nodes.py                # 단계를 독립적으로 테스트할 함수
    graph.py                # 분기·최대 2회 재작성·체크포인터
    validators.py           # 필수 코드 검사와 LLM 보조 검사 분리
  llm.py                    # 설정 기반 어댑터·테스트용 fake
  api.py                    # 세션 생성·조회·SSE·재개
  migrations/               # 명시적인 SQL 마이그레이션
  tests/
tools/
  seed_tarot_knowledge.py    # fixture→Neo4j·Chroma, 안정된 ID로 재실행
requirements-tarot.txt       # 실제 검증한 호환 버전 고정, 기존 requirements 분리
frontend/src/tarot/          # 기존 페이지에서 선택적으로 진입하는 새 모드
docs/TAROT_RUNBOOK.md        # 설치·적재·실행·검증·장애 재개
```

DB·모델·LLM 클라이언트는 import 시 생성하거나 호출하지 않는다. 테스트는 fake 저장소로 독립 실행할 수 있어야 한다. 실제 통합 테스트는 별도 표시하고 설정이 없을 때 건너뛴 이유를 출력한다. 테스트를 건너뛴 결과를 실제 DB 검증으로 보고하지 않는다.

## 1단계: 스키마·세션·뽑기

PostgreSQL에 `profiles`, `reading_sessions`, `reading_draws`, `reading_reports`, `reading_events`를 만든다. 상세 설계의 필수 열·유일성 제약을 구현한다. 스프레드 이름과 MBTI·별자리는 허용 목록으로 검증한다.

`create_or_get_session(input, idempotency_key, owner_scope)`는 다음을 보장한다.

- 같은 키·같은 정규화 입력: 같은 `session_id`와 draw 3개 반환.
- 같은 키·다른 입력: `409 Conflict`.
- 동시 요청: 유일성 제약과 트랜잭션으로 세션·draw 한 세트만 확정.
- 테스트에서는 주입한 RNG로 재현, 실제 실행에서는 서버 측 난수 사용.
- 성공하면 `draw_confirmed`, 실패하면 트랜잭션 전체 롤백. draw 일부만 저장된 세션을 정상으로 반환하지 않음.

완료 기준: 카드 78개·의미 156개, 카드 중복 방지, 3개 위치 유일성, 동시 중복 요청, 재시도 불변성 테스트 통과.

## 2단계: 지식 fixture와 DB 어댑터

먼저 탑·별·은둔자 같은 작은 fixture로 양방향·각 위치의 경로를 검증하고, 78장 전체 카탈로그로 확대한다. 그래프 관계가 없는 카드를 검색 성공으로 꾸미지 않는다. 통합 MVP가 완료되려면 156개 의미 모두 적어도 하나의 해설·출처를 가져야 한다. 780개 청크는 다음 콘텐츠 확장 목표다.

Neo4j는 `TarotCard → TarotMeaning → InterpretationRule → SharedTrait`와 출처 경로를 반환한다. 기존 `HAS_TRAIT`, `DESCRIBED_BY`, `FROM_DOCUMENT`를 재사용하고 무관한 데이터를 수정·삭제하지 않는다. 새 fixture에는 `dataset_id` 범위를 둔다.

Chroma 어댑터는 원문, cosine 또는 거리의 정의, 청크 ID, 메타데이터를 반환한다. 세 카드 각각의 정역방향을 필터링하고 일반 근거는 분리한다. 임베딩 모델의 입력 형식·정규화·차원을 문서화한다. 원문·ID·출처 URL·content hash·데이터 판본이 두 지식 저장소에서 대응해야 한다.

완료 기준: 세 카드의 올바른 방향 근거 회수, 잘못된 판본 거부, 실제 근거 없는 경우 빈 근거 상태, 재적재 안정된 ID, DB 장애와 정상 빈 결과 구분.

## 3단계: LangGraph 파이프라인

상태 스키마의 예시 필드:

```python
class ReadingState(TypedDict):
    session_id: str
    question: str
    mbti: str
    zodiac_id: str
    draws: list[Draw]
    dataset_version: str
    mapping_version: str
    embedding_profile: str
    graph_paths: list[GraphEvidence]
    keywords: list[str]
    chunks: list[ChunkEvidence]
    draft: str
    validation_errors: list[str]
    rewrite_count: int
    status: str
    error_code: str | None
```

위 코드는 타입 계약 개요다. 실제 구현에서는 필요한 import, 정의와 부분 상태 업데이트에 맞는 스키마를 완성한다.

노드는 `load_confirmed_draws`, `retrieve_graph`, `retrieve_semantic`, `generate`, `validate`, `persist_report`로 나눈다. 요청 검증·세션 생성은 API/서비스 계층에서 먼저 끝낸다. 조건부 엣지는 검수 통과 → 저장, 수정 가능하고 `rewrite_count < 2` → 재작성, 근거 부족·상한 초과 → `needs_evidence|validation_failed`다. 재작성은 `generate`로만 돌아가며 뽑기·검색을 반복하지 않는다.

체크포인터의 `thread_id=session_id`를 사용한다. 시작 시 기존 완료 결과가 있으면 반환한다. 완료 저장과 상태 갱신은 PostgreSQL에서 원자적으로 처리한다. 같은 세션의 동시 실행은 DB 잠금 또는 실행 lease로 방지한다. 외부 LLM이 설정되지 않았다면 실제 생성 성공을 가장하지 말고 설정 오류를 설명한다.

필수 검수 항목:

- 뽑힌 3장과 방향·위치가 모두 결과의 구조화된 카드 섹션에 포함되는가.
- 인용된 청크·경로 ID가 실제 이번 검색 결과에 있는가.
- 카드별 최소 근거가 있고, 해당 방향과 일치하는가.
- 목표 1,200~2,000자에 도달했는가. 근거 부족이면 재작성보다 종료를 우선한다.
- LLM 검수와 무관하게 필수 코드 검사가 실패하면 완료로 저장하지 않는가.

완료 기준: fake LLM으로 정상·2회 재작성·근거 부족·통신 실패·체크포인트 재개·동시 재개를 테스트하고, 설정된 실제 LLM으로 소수의 수동 검수 사례를 별도 기록.

## 4단계: API와 이벤트

```json
{
  "mbti": "INTJ",
  "zodiac_id": "aquarius",
  "question": "새 일을 시작할지 고민이야",
  "spread": "three_card_reflection"
}
```

`POST /api/readings`는 `Idempotency-Key` 헤더를 요구하고 `session_id`, `status`, 서버 확정 `draws`, `events_url`을 반환한다. 세션이 이미 있으면 동일 입력 여부를 확인한다. 클라이언트의 임의 카드 ID·방향은 허용 입력으로 받지 않는다. 고정 draw를 사용하는 평가 입력은 공개 API와 분리한 테스트 도구로만 제공한다.

`GET /api/readings/{id}`와 `GET /api/readings/{id}/events`는 세션 소유권을 확인한다. 익명 로컬 MVP라면 소유 범위·토큰 발급 방식을 명시하고, 공개 배포 전 인증을 완료한다. API 키·DB 비밀번호·원문 질문을 URL에 넣지 않는다.

SSE 이벤트에는 세션 내 증가하는 ID와 명확한 타입을 붙인다. 1차는 진행 상태만 스트리밍하고 최종 검수 통과 텍스트를 `report.completed`에서 보낸다. 연결 종료를 새 뽑기 요청으로 처리하지 않는다. `Last-Event-ID`로 재연결하거나 상태 조회로 복구한다. 재개 API는 저장된 카드·판본을 로드해 실행하고 이미 완료한 세션을 재생성하지 않는다.

완료 기준: 유효하지 않은 입력의 4xx, 키 충돌 409, 소유하지 않은 세션 차단, 중복 이벤트 무해 처리, 저장소 장애의 명시적 상태, 단절 후 카드 불변성.

## 5단계: React 카드 화면

현재 루미·유형·별자리 선택 화면은 유지하고 **타로 실험 모드**로 별도 진입한다. 서버가 설정되지 않았을 때 정적 검색은 그대로 동작한다. 셔플·3장 선택·순차 뒤집기·정역방향·위치·진행·출처·오류·다시 이어가기 상태를 구현한다.

서버가 확정한 3장만 표시한다. 뒤집기 횟수나 네트워크 재연결로 결과를 바꾸지 않는다. 키보드로 공개할 수 있고 `prefers-reduced-motion`에서는 애니메이션을 줄인다. 카드 그림은 직접 제작하거나 사용권을 확인한 자산만 쓴다. 그림이 없어도 카드명·방향·위치가 텍스트로 읽혀야 한다.

새 모드에는 질문·리포트·이력 저장 범위를 안내한다. 기존 정적 모드의 개인정보 설명과 혼동하지 않게 한다. 브라우저 번들에 DB 자격 증명과 LLM 키를 넣지 않는다. 로컬·공개 백엔드 URL을 설정으로 분리하고 HTTPS 호스트에서 HTTP 백엔드를 당연히 사용할 수 있다고 가정하지 않는다.

## 6단계: 검증·문서·완료 보고

기존 회귀 확인:

```powershell
.venv/Scripts/python -m unittest discover -s mbti_lab -p "test_*.py"
.venv/Scripts/python -m mbti_lab.verify_http
cd frontend
npm test
npm run build
```

실제 DB와 고정 모델이 준비된 환경에서만 `tools/verify_corpus_retrieval.py`, 신규 PostgreSQL·Neo4j·Chroma 통합 검증, 실제 LangGraph 재개 시험을 실행한다. 누락된 환경을 임의의 성공 fixture로 바꿔 보고하지 않는다. 작은 fixture가 통과하면 156개 카드 의미의 데이터 커버리지 검사로 확대한다.

`docs/TAROT_RUNBOOK.md`에는 의존성의 실제 검증 버전, 설정 예시(비밀값 제외), 실행 포트, 마이그레이션·지식 적재·재개·정리 명령, 데이터 판본과 사용한 LLM/임베딩 정보를 기록한다. 최소 30개의 고정 질문·draw 평가 세트를 만들고, 이후 벡터 단독 / 그래프 추가 / 검수 추가의 관련성·방향 일치·출처·지연·호출 비용을 비교한다.

`89,856`은 한 카드·위치 조건의 조합 수다. 실제 해설을 89,856개 적재했다고 쓰지 않는다. 콘텐츠 20~60배는 단계별 작성·검수 목표이며, 기존 600개 대비 첫 연결 시험 1,380개는 2.3배다. 품질 향상률은 별도 평가 전 주장하지 않는다.

최종 보고에는 실제 구현 범위, 실행 명령, 통과한 검사, 생략한 검사와 이유, 알려진 제한, 변경 파일을 적는다. 유료 모델 호출·운영 배포·외부 전송은 해당 작업 시점의 사용자 지시와 실행 환경 권한 범위 안에서 수행한다.

## 기술 참고

- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence) · [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)
- [LangGraph streaming](https://docs.langchain.com/oss/python/langgraph/streaming)
- [Chroma metadata filtering](https://docs.trychroma.com/docs/querying-collections/metadata-filtering)
- [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [Neo4j constraints](https://neo4j.com/docs/cypher-manual/current/schema/constraints/create-constraints/)
- [Joan Bunning 카드 목록](https://www.learntarot.com/cards.htm) — 카드 분류 참고, 원문·삽화 복제 허가를 의미하지 않음.

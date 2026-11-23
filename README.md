# Explore Your Little Universe

**한국어** | [English](README.en.md)

**Neo4j + PostgreSQL + Chroma의 DB 스키마를 설계하고 실습하는 프로젝트다.** MBTI·별자리(horoscope)·타로 리딩을 소재로, 관계는 그래프 DB에, 사용자·세션·뽑기 이력은 관계형 DB에, 해설 원문과 임베딩은 벡터 DB에 맞게 저장하고 조회한다.

<img src="docs/images/lumi.svg" alt="Lumi — 작은 별 친구" width="180">

## 1. 현재 공개 Beta — Serverless · Google LiteRT-LM

현재 공개 Beta는 MBTI·별자리 해설·사례 600개를 탐색하는 정적 React 앱이다. Neo4j에서 구축한 공개 스냅샷과 브라우저의 Google LiteRT-LM 임베딩 검색을 사용한다. Lumi는 작은 안내 캐릭터다.

**[설치 없이 Beta 열기](https://ai-agent-orchestrator.github.io/explore-your-little-universe/)** · [실행·빌드 안내](docs/STATIC_REACT_RAG.md) · [데이터 구성·출처](docs/INTERPRETATION_CORPUS.md) · [이전 버전 v1](https://github.com/ai-agent-orchestrator/explore-your-little-universe/tree/v1)

최신 Chrome·Edge에서 사용하며 첫 실제 검색에는 모델 다운로드가 필요하다. 아래 3DB 서버 모드는 이 정적 Beta와 구분되는 다음 단계 설계다.

## 2. 다음 단계 — 타로 + 3DB + LangGraph (1차 시험 설계)

**이 절의 서버 모드는 설계 단계다. 현재 공개 Beta에 타로 뽑기·PostgreSQL·Chroma·LangGraph·생성 LLM이 구현된 것은 아니다.** MBTI·별자리라는 기존 모델에 타로 **78장 × 정/역방향 = 156개 의미**를 결합하고, 관계·해설·세션의 책임을 나눈다.

| 구성 요소 | 담당 데이터와 역할 |
| --- | --- |
| **PostgreSQL** | 사용자 프로필 스냅샷, 질문, 세션·뽑기 이력, 3장 배열·방향·위치, 실행 상태·리포트. LangGraph 체크포인트로 중단 후 같은 세션을 재개한다. |
| **Neo4j** | MBTI·별자리·카드·원소·상징과 출처가 있는 편집 규칙. 2~3홉 관계를 조회해 해설에 쓸 키워드와 근거 경로를 반환한다. |
| **Chroma** | 정역방향·상황별 심층 해설 원문과 임베딩. 질문과 그래프 키워드로 검색하되 뽑힌 카드·방향·자료 판본을 필터로 지킨다. |
| **LangGraph** | 확정 뽑기 로드 → 관계 조회 → 의미 검색 → 초안 작성 → 검수 → 결과 저장의 상태 흐름과 제한된 재작성·재개를 제어한다. |
| **React + FastAPI** | 카드 섞기·3D 뒤집기와 세션 API·진행 이벤트를 연결한다. 카드 선택 결과는 서버가 확정하고 화면은 동일한 3장을 공개한다. |

예를 들어 **물병자리 + INTJ + 탑(Tower) 역방향**에 대해, 카드의 의미 → 편집 규칙 → 공통 성향과 별자리 → 원소 경로를 확인하고 관련 원문을 찾는다. 상징 해석은 성찰용 관점이며 실제 성격·궁합·미래를 검증한 예측으로 제시하지 않는다. 카드 원본과 정역방향 의미를 분리해 세션마다 카드 노드의 방향을 덮어쓰지 않는다.

### DB 스키마 실습 범위

| 저장소 | 스키마·적재 단위 | 실습할 내용 |
| --- | --- | --- |
| **PostgreSQL** | `profiles`, `reading_sessions`, `reading_draws`, `reading_reports`, `reading_events`와 체크포인터 전용 테이블 | MBTI·별자리 프로필 스냅샷, 질문, 카드 3장·방향·위치 저장. 키·제약·트랜잭션과 세션 재개 실습. |
| **Neo4j** | `MbtiType`, `ZodiacSign`, `SharedTrait`, `TarotCard`, `TarotMeaning`, `Element`, `Archetype`, `InterpretationRule`, 출처 노드 | 카드 78개와 정역방향 의미 156개를 분리하고, MBTI·별자리·상징을 연결해 근거 경로 조회. |
| **Chroma** | 해설 청크의 원문·임베딩과 `card_id`, `orientation`, `topic`, `dataset_version`, `source_url` 등 메타데이터 | MBTI·별자리·타로 해설 적재, 의미 검색, 카드·방향·판본 필터와 출처 추적 실습. |

아래 스키마는 **구현할 설계**다. [상세 설계의 Neo4j 모델·PostgreSQL 계약·Chroma 청크](docs/TAROT_3DB_LANGGRAPH_PLAN.md)에서 필드와 제약을 확인한다.

### 해설 분량과 조합을 확장하는 방법

`16 × 12 × 78 × 2 × 3 = 89,856`은 **한 카드가 한 스프레드 위치에 놓이는 조건 조합**이다. 실제 해설 89,856개 또는 서로 다른 3장 전체의 경우의 수를 뜻하지 않는다.

- 첫 연결 시험: 156개 의미 × 5개 주제 = 타로 청크 780개. 기존 600개와 합쳐 **1,380개(2.3배)**를 목표로 한다.
- 분량 확장: 156개 의미 × 3개 위치 × 5개 주제 × 6~15개 관점. 기존 자료 포함 **14,640~35,700개(현재의 24.4~59.5배)**가 작성·검수 목표다.
- 조합마다 같은 글을 복제하지 않고, 출처와 판본이 있는 청크와 관계 경로를 재사용한다. 콘텐츠 양과 답변 품질은 각각 평가한다.

### 1차 파이프라인과 화면

1. **입력·뽑기 확정:** MBTI·별자리·질문을 받고 서버가 중복 없이 카드 3장과 방향·위치를 확정한다. PostgreSQL에 한 트랜잭션으로 기록하고, 같은 요청을 다시 받아도 같은 세션을 반환한다.
2. **관계 조회:** Neo4j에서 선택한 카드·유형·별자리의 제한된 경로, 상징 키워드, 출처를 가져온다.
3. **의미 검색:** Chroma에서 카드별 방향을 지킨 원문과 질문에 맞는 문맥을 찾는다.
4. **작성·검수:** 작성자가 출처를 인용해 초안을 만들고, 코드 검사와 LLM 검수가 세 카드·정역방향·근거·분량을 확인한다. **최대 2회 재작성**하고 근거가 부족하면 보완 필요로 끝낸다.
5. **저장·표시:** 검수 통과 리포트를 PostgreSQL에 저장하고 화면에 전달한다. 첫 시험에서는 단계 진행을 스트리밍하고 검수 전 초안은 최종 결과로 표시하지 않는다.

카드 섞기·뒤집기는 React의 연출로 구현한다. 새 서버 모드는 별도 백엔드와 DB가 필요하고 질문·이력 저장 범위를 안내한다. 현재 정적 Beta는 계속 서버 없는 실행과 기기 내 검색을 제공한다.

**[1차 시험 상세 설계](docs/TAROT_3DB_LANGGRAPH_PLAN.md)** · **[Claude에게 넘길 구현 요청서](docs/CLAUDE_TAROT_IMPLEMENTATION.md)**

구현 순서는 **데이터 모델·확정 뽑기 → Neo4j·Chroma 검색 → LangGraph·검수·재개 → 카드 화면**이다. 인계 문서에는 권장 파일 구조, DB 제약, 상태·API 계약, 테스트와 완료 기준을 담았다.

# Neo4j 실습 — MBTI + 12별자리 그래프

MBTI와 12별자리를 공통 성향으로 연결하고 Neo4j에서 관계를 탐색하는 학습용 프로젝트다. 콘텐츠는 직접 작성한 재미용 예시이며 공식 성격 검사나 진단, 검증된 점성술 해석이 아니다. LLM이나 OpenAI API 없이 실행할 수 있다.

- [12별자리 + MBTI 그래프](docs/ASTROLOGY_LAB.md): 별자리 12개를 공통 성향으로 연결하고 Neo4j Browser에서 확인한다.
- [MBTI Graph Lab — 마음의 지도](mbti_lab/README.md): MBTI 선택 → 성향·제안 그래프를 보여주는 로컬 웹앱. Neo4j 적재·조회 및 DB 없는 화면 미리보기 지원.
- [이전 3DB 실험안 — SQLite 기반](docs/THREE_DB_COLLAB_PLAN.md): 과거 참고안. 최종 PostgreSQL·Neo4j·Chroma 설계는 [타로 3DB 설계](docs/TAROT_3DB_LANGGRAPH_PLAN.md)를 따른다.

## 실행

Python 3.12와 로컬 Neo4j를 준비하고 전용 데이터베이스 `mbti-zodiac`를 생성한다. DB 생성과 기존 데이터 분리는 [데이터베이스 분리 안내](docs/DATABASE_SEPARATION.md)를 참고한다.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
notepad .env.mbti
# .env.mbti에 Neo4j URI, 사용자 이름, 비밀번호 설정. DB는 mbti-zodiac 고정
.venv/Scripts/python -m mbti_lab.astrology
.venv/Scripts/python -m mbti_lab.server
```

웹앱: http://127.0.0.1:8016

로컬에서만 사용하는 `.env.mbti`에 다음 항목을 입력한다. 비밀번호는 본인 Neo4j 비밀번호로 설정한다. `.env` 계열 파일은 저장소에 포함하지 않는다.

```text
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=본인_비밀번호
NEO4J_DATABASE=mbti-zodiac
```

별자리 적재 명령은 MBTI 데이터도 함께 준비한다. 순차 재실행은 같은 노드와 관계를 재사용한다. 비밀번호가 들어 있는 `.env.mbti`는 Git에서 제외된다.

Neo4j 없이 화면만 미리 보려면:

```powershell
.venv/Scripts/python -m mbti_lab.server --demo
```

## Neo4j Browser에서 그래프 확인

`mbti-zodiac` DB를 선택한 뒤 실행하고 Graph 보기로 전환한다.

```cypher
MATCH p = (:MbtiType {code:'INTJ'})-[:HAS_TRAIT]->(:SharedTrait)
          <-[:HAS_TRAIT]-(:ZodiacSign {name:'물병자리'})
RETURN p;
```

기존 로컬 웹앱은 MBTI 선택 화면을 제공한다. 정적 React Beta는 MBTI·별자리·해설 주제를 함께 선택하며, Neo4j Browser에서도 관계를 탐색할 수 있다. GitHub는 코드와 예시 데이터 정의를 보관하며 웹앱 서버나 Neo4j를 자동 실행하지 않는다.

## 검증

```powershell
.venv/Scripts/python -m unittest discover -s mbti_lab -p "test_*.py"
.venv/Scripts/python -m mbti_lab.verify_http
```

# 12별자리 + MBTI 초간단 그래프

별자리 12개가 각각 두 가지 공통 성향 노드로 연결된다. 기존 MBTI와 같은 노드를 공유하므로 `MBTI → 공통 성향 ← 별자리` 경로를 탐색할 수 있다. 공통 성향에는 `MbtiTrait`와 `SharedTrait` 라벨이 함께 붙는다. 기존 MBTI 웹앱은 그대로 동작한다.

이 매핑은 그래프 실습용으로 직접 정한 가상 조합이다. 실제 점성술 체계를 재현하거나 성격·궁합을 검증한 결과가 아니다. 생일, 천체 계산, LLM은 사용하지 않는다. 별자리 이름으로 직접 조회한다.

## 저장

`.env.mbti`의 `NEO4J_DATABASE=mbti-zodiac` 접속 설정을 사용한다. 식당 DB와 분리된 전용 DB를 먼저 준비하고 저장소 루트에서 실행한다. [DB 분리 절차](DATABASE_SEPARATION.md)

```powershell
.venv/Scripts/python -m mbti_lab.astrology
```

MBTI 데이터도 함께 준비하므로 독립 실행이 가능하다. 순차 재실행은 MERGE로 같은 노드와 관계를 재사용한다. 다른 식당 데이터는 삭제하지 않는다. 매핑을 바꿔 예전 관계를 없애려면 별도 정리가 필요하며, 이 명령은 관계를 자동 삭제하지 않는다.

## Browser에서 Graph 보기

Browser에서 `:use mbti-zodiac`를 실행한다. 다음 쿼리는 각각 따로 실행한다.

전체 별자리:

```cypher
MATCH p = (:ZodiacSign)-[:HAS_TRAIT]->(:SharedTrait)
RETURN p;
```

INTJ와 물병자리의 공통 성향:

```cypher
MATCH p = (:MbtiType {code:'INTJ'})-[:HAS_TRAIT]->(:SharedTrait)
          <-[:HAS_TRAIT]-(:ZodiacSign {name:'물병자리'})
RETURN p;
```

예시에서는 `이유 살피기`와 `가능성 탐색`을 공유한다. 이것은 매핑의 결과이며 궁합 점수가 아니다.

성향에서 일상 제안과 두 체계의 출처까지 함께 탐색:

```cypher
MATCH p = (:MbtiType {code:'INTJ'})-[:HAS_TRAIT]->(t:SharedTrait)
          <-[:HAS_TRAIT]-(z:ZodiacSign {name:'물병자리'})
MATCH q = (t)-[:SUGGESTS]->(:MbtiInsight)-[:FROM_SOURCE]->(:MbtiSource)
MATCH r = (z)-[:FROM_SOURCE]->(:AstrologySource)
RETURN p, q, r;
```

## 별자리 해설과 벡터 검색 확장

별자리 12개에 각각 10개 주제의 해설 120개를 추가했다. Astrology.com의 대중적인 소개를 짧게 재서술하고 일상 적용 예시를 직접 작성했다. 참고 URL과 작성 구분을 각 해설에 기록했다. 기존의 두 성향 매핑은 실습용 연결로 유지한다.

`.venv/Scripts/python -m mbti_lab.rag_seed`를 실행하면 MBTI 해설·일상 사례와 함께 총 600개 글 및 벡터를 적재한다. `astrology` 명령만으로는 기본 별자리 그래프만 준비한다.

```cypher
MATCH p = (:ZodiacSign {id:'aquarius'})-[:DESCRIBED_BY]->(c:RagChunk)
MATCH q = (c)-[:FROM_DOCUMENT]->(:RagDocument)
RETURN p, q;
```

기존 로컬 MBTI 웹앱의 선택 화면은 MBTI만 제공한다. 정적 React 앱에서는 MBTI·별자리와 해설 주제를 함께 선택할 수 있다. [600개 데이터 구성·출처·검증](INTERPRETATION_CORPUS.md)

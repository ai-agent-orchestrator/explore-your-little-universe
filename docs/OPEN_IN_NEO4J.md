# 각자의 Neo4j Browser에서 루미 그래프 열기

[한국어 README](../README.md) · [English README](../README.en.md)

## 1. 자기 Neo4j를 시작하고 학습용 DB 선택

Neo4j Desktop의 로컬 인스턴스(Neo4j 5.23 이상)를 시작한다. Browser에서 본인의 사용자 이름과 비밀번호로 로그인하고 학습용 DB를 선택한다. 이 문서에는 접속 비밀번호가 없으며 다른 사람의 DB에 연결하지 않는다.

여러 DB를 만들 수 있으면 `mbti-zodiac`를 권장한다. Community 단일 DB 환경에서는 본인의 별도 학습용 인스턴스의 기본 `neo4j` DB도 사용할 수 있다. 중요한 데이터가 없는 학습용 DB에서 시작한다.

## 2. 최초 한 번, 예시 그래프 넣기

[실습 데이터 Cypher 파일](../cypher/lumi_graph_only_seed.cypher)을 열고 **Raw**를 눌러 전체 내용을 복사한다. Neo4j Browser 편집기에 전체를 붙여넣고 **Run**을 누른다. 파일 전체가 하나의 쿼리이므로 부분 선택 없이 실행한다.

MBTI 16개, 별자리 12개, 공통 성향 8개, 해설·사례 600개, 문서 묶음 64개, 행동 제안 24개를 만든다. 안정된 ID로 `MERGE`하므로 순차 재실행은 같은 노드를 재사용한다. 삭제 쿼리는 없다.

이 파일에는 임베딩 벡터가 없고, 그래프 보기만 재현한다. Python·Ollama·LiteRT·API 키·APOC 설치가 필요 없다. 벡터 검색까지 재구축하려면 [React 브랜치의 전체 구축 안내](STATIC_REACT_RAG.md)를 따른다.

## 3. 링크를 눌러 전체 그래프 쿼리 열기

### [내 Neo4j Browser에서 전체 그래프 쿼리 열기](http://localhost:7474/browser/?cmd=edit&arg=MATCH%20p%20%3D%20%28a%29-%5Br%5D-%3E%28b%29%0AWHERE%20type%28r%29%20IN%20%5B%27HAS_TRAIT%27%2C%27FROM_CHUNK%27%2C%27FROM_DOCUMENT%27%2C%27SUGGESTS%27%2C%27DESCRIBED_BY%27%5D%0A%20%20AND%20any%28label%20IN%20labels%28a%29%20WHERE%20label%20IN%20%5B%27MbtiType%27%2C%27ZodiacSign%27%2C%27SharedTrait%27%2C%27RagChunk%27%2C%27RagTip%27%5D%29%0A%20%20AND%20any%28label%20IN%20labels%28b%29%20WHERE%20label%20IN%20%5B%27SharedTrait%27%2C%27RagChunk%27%2C%27RagTip%27%2C%27RagDocument%27%5D%29%0ARETURN%20p%0ALIMIT%20500%3B)

링크는 **누른 사람 본인의 `localhost:7474`**를 연다. 쿼리를 편집기에 미리 넣을 뿐 자동 실행하거나 데이터를 전송하지 않는다. 학습용 DB를 선택했는지 확인하고 **Run → Graph**를 누른다.

HTTP 포트가 7474가 아니라면 주소의 포트를 본인 것으로 바꾼다. Neo4j Desktop 내부 Query만 사용하는 경우에는 아래 쿼리를 직접 복사한다. 웹브라우저가 로컬 주소 열기를 제한하면 새 탭에서 자신의 Browser를 직접 연 뒤 붙여넣는다. 이 링크는 공유 호스팅된 Neo4j나 저자의 로컬 DB에 접속하는 링크가 아니다.

```cypher
MATCH p = (a)-[r]->(b)
WHERE type(r) IN ['HAS_TRAIT','FROM_CHUNK','FROM_DOCUMENT','SUGGESTS','DESCRIBED_BY']
  AND any(label IN labels(a) WHERE label IN ['MbtiType','ZodiacSign','SharedTrait','RagChunk','RagTip'])
  AND any(label IN labels(b) WHERE label IN ['SharedTrait','RagChunk','RagTip','RagDocument'])
RETURN p LIMIT 500;
```

## 작은 그래프만 나오는 이유

React의 ‘학습용 근거’ 쿼리는 `scenario-01`, `scenario-04`, `plan` 같은 ID를 지정해 한 제안의 출처만 검증한다. 전체 데이터가 적다는 뜻은 아니다. 위의 전체 보기에는 특정 ID 제한이 없다. 노드가 많아 복잡하면 MBTI·별자리를 지정한 부분 보기로 돌아간다.

```cypher
MATCH p = (:MbtiType {code:'INTJ'})-[:HAS_TRAIT]->(t:SharedTrait)
          <-[:HAS_TRAIT]-(:ZodiacSign {name:'물병자리'})
OPTIONAL MATCH q = (t)-[:FROM_CHUNK]->(:RagChunk)-[:FROM_DOCUMENT]->(:RagDocument)
RETURN p, q LIMIT 50;
```

## English quick start

Start your own local Neo4j instance, sign in with your credentials, and choose a learning database. Copy the entire [graph-only seed file](../cypher/lumi_graph_only_seed.cypher), run it once, then use the Browser link above and choose **Run → Graph**. It opens **your own localhost**, not someone else's database. The link only pre-fills the editor; it contains no password. Change port 7474 if needed.

The seed recreates the fictional graph without embeddings or external libraries. An exact-ID evidence query intentionally shows one narrow proof path; the full-graph query shows the wider network. The corpus combines short source-informed profile paraphrases and original fictional applications. Source URLs and editorial notes are included. Cross-system mappings are authored learning examples, not validated personality or clinical claims.

The deep link uses Neo4j's documented [`cmd=edit&arg=...` URL parameters](https://neo4j.com/docs/browser/operations/browser-url-parameters/).

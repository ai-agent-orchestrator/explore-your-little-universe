# 해설·사례 600개와 벡터·그래프 연결

2026-11-22 기준으로 검색 대상 글을 60개에서 **600개(10배)**로 확장했다.

| 구성 | 수량 | 작성 방식 |
| --- | ---: | --- |
| 기존 일상 사례 | 60 | 기존 ID·제목·본문 유지 |
| 16유형 해설 | 160 | 유형당 10개 주제 |
| 12별자리 해설 | 120 | 별자리당 10개 주제 |
| 추가 일상 사례 | 260 | 26개 주제마다 서로 다른 상황 10개 |
| 합계 | 600 | 문서 묶음 64개, 공통 성향 8개, 행동 제안 24개 |

유형·별자리의 10개 주제는 기본 성향, 강점, 주의할 점, 대화, 친구와 관계, 협업, 배움, 휴식, 선택, 작은 성장이다. 일상 사례는 연락·모임·가까운 관계·가족·공동생활·회의·피드백·마감·공부·발표·창작·프로젝트·취미·여행·휴식·거절·계획 등으로 넓혔다. 새 사례에는 구체적인 고민과 작은 행동을 함께 적었다.

## 공개 자료와 직접 작성한 내용

[Myers & Briggs Foundation의 공식 선호·유형 안내](https://www.myersbriggs.org/my-mbti-personality-type/the-16-mbti-personality-types/)로 체계의 기본 구분을 확인했다. 대중적인 유형 소개는 [16Personalities](https://www.16personalities.com/personality-types)의 각 유형 소개를, 별자리는 [Astrology.com](https://www.astrology.com/zodiac-signs)의 각 별자리 소개를 참고했다.

외부 글을 통째로 복사하거나 번역하지 않았다. 각 프로필의 앞 세 주제는 공개 소개의 핵심을 짧게 한국어로 재서술했다. 나머지 일곱 주제는 해당 주제에서 착안해 직접 만든 일상 적용 예시이며, 참고 사이트에서 검증한 조언이라는 뜻이 아니다. 추가 일상 사례 260개도 직접 작성했다.

16Personalities의 NERIS 모델은 공식 MBTI와 다르다. 별자리 해설은 대중 점성술의 관습적 이미지이며 과학적 성격 예측이 아니다. 기존 별자리 → 공통 성향 매핑은 실습용으로 직접 정한 것을 유지한다. 해설의 행동 예시는 다른 선호의 관점을 연습할 수 있으므로, 해설에 연결된 성향 전부가 그 유형의 네 글자를 뜻하지는 않는다.

각 해설에 `source_url`, `reviewed_on`, `editorial_note`를 기록했다. 화면의 **출처와 연결 확인**, 검색 카드의 **원문·출처**, Gemini용 근거 프롬프트에서 출처를 따라갈 수 있다. 세부 출처 URL은 [해설 데이터](../mbti_lab/interpretations.py)의 유형별 규칙과 [공개 스냅샷](../frontend/public/data/graph.json)에 들어 있다.

## 실제 저장·검색 경로

```text
질문 → 같은 모델로 임베딩 → RagChunk 상위 3개
검색된 RagChunk ← FROM_CHUNK — SharedTrait — FROM_CHUNK → 다른 RagChunk
                                                  ↑ FROM_CHUNK
                                                  RagTip
MbtiType / ZodiacSign — DESCRIBED_BY → 해당 프로필 해설 10개
RagChunk — FROM_DOCUMENT → RagDocument (참고 URL·작성 구분)
```

600개 글 모두 같은 고정 LiteRT-LM 모델로 생성한 768차원 벡터를 갖는다. Neo4j의 `mindmap_chunk_embedding` 인덱스와 정적 앱의 `graph.json`에 반영했다. 브라우저에서는 공개 스냅샷을 사용하며 실행 중 DB에 접속하지 않는다.

그래프 확장의 후보 자격은 검색된 글과 실제 공통 성향 경로가 있는지로 정한다. 후보 정렬은 질문과 후보의 cosine 75%, 검색된 글과 후보의 최대 cosine 25%에 작은 연결 가중치를 더한다. 공통 성향은 +0.02, 선택한 유형 또는 별자리 성향은 +0.01, 해당 프로필의 직접 해설은 +0.015다. 질문 벡터가 없는 호출에서는 검색된 글과의 유사도를 쓴다. 이 수치는 실습용 순위 규칙이며 검증된 성격 점수가 아니다. 원래 벡터 상위 3개는 선택을 바꿔도 바뀌지 않는다.

## 다시 구축하기

저장소 루트에서 실행한다. `.env.mbti`는 기존 전용 `mbti-zodiac` DB 설정을 사용한다.

```powershell
.venv/Scripts/python -m mbti_lab.rag_seed
.venv/Scripts/python tools/generate_browser_import.py
.venv/Scripts/python tools/verify_browser_import.py
.venv/Scripts/python tools/verify_corpus_retrieval.py
```

본문·제목과 모델 정보가 같은 기존 벡터는 재사용한다. DB 없이 벡터와 스냅샷만 생성하려면 `rag_seed --export-only`를 사용한다. 이 경우 스냅샷 출처에 DB 검증을 하지 않았다고 표시한다. `lumi_graph_only_seed.cypher`는 600개 글과 출처·연결을 담지만 벡터는 포함하지 않는다.

```cypher
MATCH p = (:MbtiType {code:'INTJ'})-[:DESCRIBED_BY]->(c:RagChunk)
MATCH q = (c)-[:FROM_DOCUMENT]->(:RagDocument)
RETURN p, q;
```

```cypher
MATCH p = (:ZodiacSign {id:'aquarius'})-[:DESCRIBED_BY]->(c:RagChunk)
OPTIONAL MATCH q = (:SharedTrait)-[:FROM_CHUNK]->(c)
RETURN p, q;
```

## 검증한 범위

- Python 테스트 7개, 프런트엔드 테스트 9개, 프로덕션 빌드 통과. 로컬 미리보기 HTTP에서 16유형 모두 해설 10개를 반환하는지도 확인했다.
- 실제 Neo4j에서 `RagChunk` 600개, 벡터 600개, `DESCRIBED_BY` 280개 확인.
- 실제 Neo4j 공식 `VectorRetriever`로 여행 질문 검색 확인.
- 별도 임시 라벨에 Cypher 전체 파일을 두 번 적재해 노드 수·직접 연결 수·중복 없는 재실행 확인 후 롤백.
- [한국어 검색 점검 10개](CORPUS_RETRIEVAL_CHECKS.json): 모두 상위 3개 중 관련 주제 또는 프로필이 하나 이상 포함됨. 실제 검색 제목과 cosine을 기록했다. 정밀도 벤치마크나 모든 결과의 적합성 보장은 아니다.
- 브라우저에서 600개 표시, ENFP·쌍둥이자리·협업 해설 전환, 출처 펼치기, 저장된 질문의 벡터·그래프 결과 확인. 이번 변경 후 브라우저의 새 질문에 대한 WebGPU 추론과 모바일 기기 성능은 별도로 측정하지 않았다.

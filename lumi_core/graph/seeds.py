"""Shared seed contracts and row builders, independent of HTTP entrypoints."""
from lumi_core.catalog.traits import TRAITS, TYPES, SUGGESTIONS
from lumi_core.catalog.zodiac import SIGNS

MBTI_SEED = '''
UNWIND $rows AS row
MERGE (m:MbtiType {code: row.code})
MERGE (t:MbtiTrait {key: row.key})
SET t:SharedTrait
SET t.title = row.title, t.text = row.text
MERGE (i:MbtiInsight {key: row.key}) SET i.text = row.tip
MERGE (s:MbtiSource {id: 'mbti-lab-original-v1'})
SET s.title = 'MBTI Graph Lab 직접 작성한 재미용 예시', s.is_demo = true
MERGE (m)-[:HAS_TRAIT]->(t)
MERGE (t)-[:SUGGESTS]->(i)
MERGE (i)-[:FROM_SOURCE]->(s)
RETURN count(*) AS processed
'''

MBTI_QUERY = '''
MATCH (m:MbtiType {code: $code})-[:HAS_TRAIT]->(t:MbtiTrait)
MATCH (t)-[:SUGGESTS]->(i:MbtiInsight)-[:FROM_SOURCE]->(s:MbtiSource {id: 'mbti-lab-original-v1'})
RETURN t.key AS id, t.title AS title, t.text AS text, i.text AS tip, s.title AS source
'''

ZODIAC_SEED = '''
UNWIND $rows AS row
MERGE (z:ZodiacSign {id: row.id})
SET z.name = row.name, z.is_demo = true
MERGE (t:MbtiTrait {key: row.key})
SET t.title = row.title, t.text = row.text
SET t:SharedTrait
MERGE (z)-[:HAS_TRAIT]->(t)
MERGE (s:AstrologySource {id: 'astrology-toy-v1'})
SET s.title = '12별자리 연결 실습용 직접 작성한 가상 매핑', s.is_demo = true
MERGE (z)-[:FROM_SOURCE]->(s)
RETURN count(*) AS processed
'''

RAG_SEED = '''
UNWIND $rows AS row
MERGE (d:RagDocument {id: row.document_id})
SET d.title = row.document_title, d.is_demo = true,
    d.source = row.source, d.source_url = row.source_url, d.reviewed_on = row.reviewed_on
MERGE (c:RagChunk {id: row.id})
SET c.title = row.title, c.text = row.text, c.category = row.category,
    c.embedding = row.embedding, c.embedding_profile = $profile,
    c.kind = row.kind, c.subject_kind = row.subject_kind, c.subject = row.subject,
    c.source_url = row.source_url, c.reviewed_on = row.reviewed_on,
    c.editorial_note = row.editorial_note, c.facet = row.facet
MERGE (c)-[:FROM_DOCUMENT]->(d)
WITH row, c
UNWIND row.traits AS key
MATCH (t:SharedTrait {key: key})
MERGE (t)-[:FROM_CHUNK]->(c)
'''

RAG_TIPS = '''
UNWIND $tips AS row
MERGE (i:RagTip {id: row.id}) SET i.text = row.text
WITH row, i
MATCH (t:SharedTrait {key: row.trait})
MERGE (t)-[:SUGGESTS]->(i)
'''

RAG_SUPPORTS = '''
UNWIND $rows AS row
MATCH (c:RagChunk {id: row.id})
UNWIND row.tips AS id
MATCH (i:RagTip {id: id})
MERGE (i)-[:FROM_CHUNK]->(c)
'''

RAG_PROFILES = '''
UNWIND $rows AS row
MATCH (c:RagChunk {id: row.id})
OPTIONAL MATCH (m:MbtiType {code: row.subject}) WHERE row.subject_kind = 'mbti'
FOREACH (_ IN CASE WHEN m IS NULL THEN [] ELSE [1] END | MERGE (m)-[:DESCRIBED_BY]->(c))
WITH row, c
OPTIONAL MATCH (z:ZodiacSign {id: row.subject}) WHERE row.subject_kind = 'zodiac'
FOREACH (_ IN CASE WHEN z IS NULL THEN [] ELSE [1] END | MERGE (z)-[:DESCRIBED_BY]->(c))
'''

def trait_rows():
    return [{'code': code, 'key': key, 'title': TRAITS[key][0],
             'text': TRAITS[key][1], 'tip': TRAITS[key][2]} for code in TYPES for key in code]

def sign_rows():
    return [{'id': sign, 'name': name, 'key': key, 'title': TRAITS[key][0],
             'text': TRAITS[key][1]} for sign,name,keys in SIGNS for key in keys]

def tip_rows():
    return [{'id':key,'trait':trait,'text':text} for key,trait,text in SUGGESTIONS]

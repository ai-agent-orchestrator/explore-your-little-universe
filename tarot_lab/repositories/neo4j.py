"""Three bounded, parameterized read-only Cypher templates."""
from lumi_core.versions import DATASET_VERSION, MAPPING_VERSION
from tarot_lab.errors import GraphUnavailable

MEANING_PATHS='''
UNWIND $meaning_ids AS meaning_id
MATCH (m:TarotMeaning {meaning_id:meaning_id,dataset_id:$dataset})-[:HAS_RULE]->(r:InterpretationRule {mapping_version:$mapping_version})
      -[:RELATES_TO]->(t:SharedTrait)
WHERE EXISTS { MATCH (:MbtiType {code:$mbti})-[:HAS_TRAIT]->(t) }
   OR EXISTS { MATCH (:ZodiacSign {id:$zodiac_id})-[:HAS_TRAIT]->(t) }
MATCH (r)-[:FROM_SOURCE]->(s:InterpretationSource {dataset_id:$dataset})
RETURN DISTINCT r.id AS id, m.meaning_id AS meaning_id, m.card_id AS card_id,
       m.orientation AS orientation,t.key AS trait,r.effect AS effect,
       r.keyword AS keyword,s.id AS source_id,s.title AS source,
       [m.meaning_id,r.id,t.key,s.id] AS node_ids
ORDER BY id LIMIT $limit
'''
ELEMENT_PATHS='''
UNWIND $card_ids AS card_id
MATCH (c:TarotCard {card_id:card_id,dataset_id:$dataset})
      -[:ASSOCIATED_WITH {mapping_version:$mapping_version}]->(e:Element)
MATCH (z:ZodiacSign {id:$zodiac_id})-[:ASSOCIATED_WITH {mapping_version:$mapping_version}]->(ze:Element)
RETURN c.card_id AS card_id,e.id AS card_element,ze.id AS zodiac_element,
       e.id=ze.id AS matches, 'classical-elements-editorial-v1' AS source_id
ORDER BY card_id LIMIT 3
'''
MEANING_KEYWORDS='''
UNWIND $meaning_ids AS meaning_id
MATCH (m:TarotMeaning {meaning_id:meaning_id,dataset_id:$dataset})-[:SYMBOLIZES]->(a:Archetype {dataset_id:$dataset})
RETURN DISTINCT a.keyword AS keyword ORDER BY keyword LIMIT 12
'''

class Neo4jRepository:
    def __init__(self,driver,database='mbti-zodiac',dataset=DATASET_VERSION):
        from lumi_core.settings import project_database
        self.driver=driver; self.database=project_database(database); self.dataset=dataset

    def _read(self,query,**params):
        try:
            with self.driver.session(database=self.database,default_access_mode='READ') as session:
                return session.execute_read(lambda tx:[record.data() for record in tx.run(query,dataset=self.dataset,**params)])
        except Exception as exc: raise GraphUnavailable() from exc

    def ping(self):
        if not self.meaning_keywords(['major-16-tower:upright']): raise GraphUnavailable('Missing tarot dataset')

    def meaning_paths(self,meaning_ids,mbti,zodiac_id,mapping_version=MAPPING_VERSION,limit=30):
        return self._read(MEANING_PATHS,meaning_ids=meaning_ids[:3],mbti=mbti,zodiac_id=zodiac_id,
                          mapping_version=mapping_version,limit=min(limit,30))

    def element_paths(self,card_ids,zodiac_id,mapping_version=MAPPING_VERSION):
        return self._read(ELEMENT_PATHS,card_ids=card_ids[:3],zodiac_id=zodiac_id,mapping_version=mapping_version)

    def meaning_keywords(self,meaning_ids):
        return [row['keyword'] for row in self._read(MEANING_KEYWORDS,meaning_ids=meaning_ids[:3])]

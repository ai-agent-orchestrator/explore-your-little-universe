"""Seed optional tarot knowledge without modifying the static snapshot."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lumi_core.catalog.tarot import CARDS, meanings
from lumi_core.catalog.zodiac import SIGN_ELEMENTS
from lumi_core.corpus.lumi import cards
from lumi_core.corpus.chunk import embedding_text
from lumi_core.embedding.litert import LiteRTEmbeddings, DIMENSIONS
from lumi_core.graph.client import get_driver, database, run
from lumi_core.graph.seeds import MBTI_SEED, ZODIAC_SEED, trait_rows, sign_rows
from lumi_core.settings import ROOT, chroma_path
from lumi_core.versions import DATASET_VERSION, MAPPING_VERSION
from tarot_lab.fixtures.meanings_v1 import tarot_chunks, validate_chunks
from tarot_lab.repositories.chroma import ChromaRepository

CARDS_SEED='''UNWIND $cards AS row
MERGE (c:TarotCard {card_id:row.card_id}) SET c += row, c.dataset_id=$dataset
WITH c,row WHERE row.element IS NOT NULL
MERGE (e:Element {id:row.element}) SET e.dataset_id=$dataset
MERGE (c)-[r:ASSOCIATED_WITH]->(e) SET r.mapping_version=$mapping'''
SIGNS_SEED='''UNWIND $signs AS row
MATCH (z:ZodiacSign {id:row.id}) MERGE (e:Element {id:row.element}) SET e.dataset_id=$dataset
MERGE (z)-[r:ASSOCIATED_WITH]->(e) SET r.mapping_version=$mapping'''
MEANINGS_SEED='''UNWIND $meanings AS row
MATCH (c:TarotCard {card_id:row.card_id})
MERGE (m:TarotMeaning {meaning_id:row.meaning_id}) SET m += row,m.dataset_id=$dataset
MERGE (c)-[:HAS_MEANING]->(m)'''
CHUNKS_SEED='''UNWIND $rows AS row
MATCH (m:TarotMeaning {meaning_id:row.card_id+':'+row.orientation})
MERGE (c:RagChunk:TarotChunk {id:row.id})
SET c.title=row.title,c.text=row.text,c.card_id=row.card_id,c.orientation=row.orientation,
    c.dataset_id=$dataset,c.content_hash=row.content_hash,c.embedding=null
MERGE (d:RagDocument {id:row.document_id})
SET d.title=row.document_title,d.source=row.source,d.source_kind='authored',d.dataset_id=$dataset
MERGE (c)-[:FROM_DOCUMENT]->(d) MERGE (m)-[:DESCRIBED_BY]->(c)
MERGE (a:Archetype {id:'tarot-archetype-'+row.card_id}) SET a.keyword=row.keyword,a.dataset_id=$dataset
MERGE (m)-[:SYMBOLIZES]->(a)
MERGE (s:InterpretationSource {id:'tarot-authored-v1'}) SET s.title=row.source,s.dataset_id=$dataset
WITH row,m,s UNWIND row.traits AS trait
MATCH (t:SharedTrait {key:trait})
MERGE (r:InterpretationRule {id:row.card_id+':'+row.orientation+':'+trait})
SET r.effect=CASE row.orientation WHEN 'upright' THEN 'amplifies' ELSE 'balances' END,
    r.mapping_version=$mapping,r.dataset_id=$dataset,r.source_id=s.id,r.keyword=row.keyword,
    r.editorial_note='Lumi가 직접 정한 상징적 성찰 연결; 경험적으로 검증한 인과가 아님'
MERGE (m)-[:HAS_RULE]->(r) MERGE (r)-[:RELATES_TO]->(t) MERGE (r)-[:FROM_SOURCE]->(s)'''

def seed_graph(rows):
    with get_driver() as driver:
        for label,key in [('TarotCard','card_id'),('TarotMeaning','meaning_id'),('InterpretationRule','id'),('Element','id'),('Archetype','id')]:
            run(driver,f'CREATE CONSTRAINT tarot_{label.lower()} IF NOT EXISTS FOR (n:{label}) REQUIRE n.{key} IS UNIQUE')
        def seed(tx):
            tx.run(MBTI_SEED,rows=trait_rows()).consume()
            tx.run(ZODIAC_SEED,rows=sign_rows()).consume()
            common={'dataset':DATASET_VERSION,'mapping':MAPPING_VERSION}
            tx.run(CARDS_SEED,cards=[asdict(c) for c in CARDS],**common).consume()
            tx.run(SIGNS_SEED,signs=[{'id':id,'element':e} for id,e in SIGN_ELEMENTS.items()],**common).consume()
            tx.run(MEANINGS_SEED,meanings=meanings(),**common).consume()
            tx.run(CHUNKS_SEED,rows=rows,**common).consume()
        with driver.session(database=database()) as session: session.execute_write(seed)

def seed_chroma(rows):
    embedder=LiteRTEmbeddings()
    try:
        snapshot=json.loads((ROOT/'frontend/public/data/graph.json').read_text(encoding='utf-8'))
        meta=snapshot['model']
        compatible=(meta['sha256']==embedder.fingerprint and meta['dimensions']==DIMENSIONS
                    and meta['preprocessing']=='plain-v1' and meta['normalize'] is True)
        cache={r['id']:r for r in snapshot['chunks']} if compatible else {}
        all_rows=cards()+rows; vectors=[]
        for index,row in enumerate(all_rows,1):
            cached=cache.get(row['id'])
            vectors.append(cached['embedding'] if cached and embedding_text(cached)==embedding_text(row)
                           else embedder.embed_query(embedding_text(row)))
            if index%100==0: print(f'Tarot knowledge embedding {index}/{len(all_rows)}',flush=True)
        repository=ChromaRepository(chroma_path(),embedder.profile,create=True)
        repository.upsert(all_rows,vectors)
        print(f'Chroma: {repository.collection.count()} chunks; {repository.collection.name}')
        repository.close()
    finally: embedder.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',default=DATASET_VERSION,choices=[DATASET_VERSION])
    parser.add_argument('--neo4j',action='store_true'); parser.add_argument('--chroma',action='store_true')
    args=parser.parse_args()
    if not(args.neo4j or args.chroma): parser.error('Select --neo4j and/or --chroma')
    rows=tarot_chunks(); validate_chunks(rows)
    if args.neo4j: seed_graph(rows); print(f'Neo4j: 78 cards, 156 meanings, {len(rows)} authored chunks')
    if args.chroma: seed_chroma(rows)

if __name__=='__main__': main()

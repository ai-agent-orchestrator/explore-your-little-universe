"""Seed Neo4j and export a public static graph snapshot; no runtime DB access."""
import argparse
import json
import time
from pathlib import Path
from ohgi_graph import get_driver, run, database
from .embedding import LiteRTEmbeddings, MODEL_REPO, MODEL_REVISION, MODEL_FILE, DIMENSIONS
from .scenarios import cards, SUGGESTIONS
from .data import TYPES, TRAITS
from .astrology import SIGNS, SEED as ASTRO_SEED
from .server import SEED as MBTI_SEED

ROOT = Path(__file__).resolve().parent.parent
INDEX = 'mindmap_chunk_embedding'
PROBE = '친구가 갑자기 여행을 가자고 해서 부담스러워'
SEED = '''
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
TIPS = '''
UNWIND $tips AS row
MERGE (i:RagTip {id: row.id}) SET i.text = row.text
WITH row, i
MATCH (t:SharedTrait {key: row.trait})
MERGE (t)-[:SUGGESTS]->(i)
'''
SUPPORTS = '''
UNWIND $rows AS row
MATCH (c:RagChunk {id: row.id})
UNWIND row.tips AS id
MATCH (i:RagTip {id: id})
MERGE (i)-[:FROM_CHUNK]->(c)
'''
PROFILES = '''
UNWIND $rows AS row
MATCH (c:RagChunk {id: row.id})
OPTIONAL MATCH (m:MbtiType {code: row.subject}) WHERE row.subject_kind = 'mbti'
FOREACH (_ IN CASE WHEN m IS NULL THEN [] ELSE [1] END | MERGE (m)-[:DESCRIBED_BY]->(c))
WITH row, c
OPTIONAL MATCH (z:ZodiacSign {id: row.subject}) WHERE row.subject_kind = 'zodiac'
FOREACH (_ IN CASE WHEN z IS NULL THEN [] ELSE [1] END | MERGE (z)-[:DESCRIBED_BY]->(c))
'''


def snapshot(rows, embedder, probe_vector, source):
    """The same authored graph supports offline export and verified DB export."""
    return {
        'version': 2, 'source': source,
        'model': {'repo': MODEL_REPO, 'revision': MODEL_REVISION, 'file': MODEL_FILE,
                  'sha256': embedder.fingerprint, 'dimensions': DIMENSIONS,
                  'preprocessing': 'plain-v1', 'normalize': True},
        'probe': {'text': PROBE, 'embedding': probe_vector},
        'chunks': rows,
        'traits': [{'id': key, 'title': values[0]} for key, values in TRAITS.items()],
        'suggestions': [{'id': key, 'trait': trait, 'text': text}
                        for key, trait, text in SUGGESTIONS],
        'types': [{'code': code, 'traits': list(code)} for code in TYPES],
        'signs': [{'id': key, 'name': name, 'traits': list(traits)} for key, name, traits in SIGNS],
    }


def write_snapshot(payload):
    assert len(payload['chunks']) == len(cards())
    assert all(len(row['embedding']) == DIMENSIONS for row in payload['chunks'])
    output = ROOT / 'frontend' / 'public' / 'data' / 'graph.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'Exported {len(payload["chunks"])} learning cards to frontend/public/data/graph.json')


def export(driver, embedder, probe_vector):
    chunks = run(driver, '''MATCH (c:RagChunk)-[:FROM_DOCUMENT]->(d:RagDocument)
        WHERE c.id IN $ids
        OPTIONAL MATCH (t:SharedTrait)-[:FROM_CHUNK]->(c)
        WITH c, d, collect(DISTINCT t.key) AS traits
        OPTIONAL MATCH (i:RagTip)-[:FROM_CHUNK]->(c)
        RETURN c.id AS id, c.title AS title, c.text AS text, c.category AS category,
               c.embedding AS embedding, traits, collect(DISTINCT i.id) AS tips,
               d.id AS document_id, d.title AS document_title, d.source AS source,
               c.kind AS kind, c.subject_kind AS subject_kind, c.subject AS subject,
               c.facet AS facet, c.source_url AS source_url, c.reviewed_on AS reviewed_on,
               c.editorial_note AS editorial_note
        ORDER BY id''', ids=[c['id'] for c in cards()])
    assert len(chunks) == len(cards()) and all(len(c['embedding']) == DIMENSIONS for c in chunks)
    # Only this explicitly allowlisted fictional corpus is exported. Never export
    # arbitrary database nodes, connection information, or visitor questions.
    payload = snapshot(chunks, embedder, probe_vector, 'Neo4j mbti-zodiac editorial learning corpus v2')
    payload['types'] = run(driver, '''MATCH (m:MbtiType)-[:HAS_TRAIT]->(t:SharedTrait)
            WHERE m.code IN $codes RETURN m.code AS code, collect(DISTINCT t.key) AS traits
            ORDER BY code''', codes=TYPES)
    payload['signs'] = run(driver, '''MATCH (z:ZodiacSign)-[:HAS_TRAIT]->(t:SharedTrait)
            WHERE z.id IN $ids RETURN z.id AS id, z.name AS name,
            collect(DISTINCT t.key) AS traits ORDER BY id''', ids=[s[0] for s in SIGNS])
    assert len(payload['types']) == 16 and len(payload['signs']) == 12
    write_snapshot(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-only', action='store_true', help='Embed and export authored graph without Neo4j')
    args = parser.parse_args()
    started = time.perf_counter()
    embedder = LiteRTEmbeddings()
    try:
        rows = cards()
        existing = ROOT / 'frontend/public/data/graph.json'
        cache = json.loads(existing.read_text(encoding='utf-8')) if existing.is_file() else {}
        compatible = all(cache.get('model', {}).get(key) == value for key, value in
                         [('sha256', embedder.fingerprint), ('dimensions', DIMENSIONS),
                          ('preprocessing', 'plain-v1'), ('normalize', True)])
        cached = {row['id']: row for row in cache.get('chunks', [])} if compatible else {}
        for i, card in enumerate(rows, 1):
            previous = cached.get(card['id'], {})
            if (previous.get('title'), previous.get('text')) == (card['title'], card['text']):
                card['embedding'] = previous['embedding']
            else:
                card['embedding'] = embedder.embed_query(card['title'] + '\n' + card['text'])
            if i % 25 == 0 or i == len(rows):
                print(f'Embedding {i}/{len(rows)}', flush=True)
        probe = embedder.embed_query(PROBE)
        if args.export_only:
            write_snapshot(snapshot(rows, embedder, probe, 'Authored graph export; Neo4j import not verified'))
            print(f'PASS: native embeddings and authored graph export ({time.perf_counter()-started:.1f}s)')
            return
        with get_driver() as driver:
            for name, label, key in [('mindmap_chunk_id', 'RagChunk', 'id'),
                                      ('mindmap_doc_id', 'RagDocument', 'id'),
                                      ('mindmap_tip_id', 'RagTip', 'id')]:
                run(driver, f'CREATE CONSTRAINT {name} IF NOT EXISTS FOR (n:{label}) REQUIRE n.{key} IS UNIQUE')
            mbti_rows = [{'code': code, 'key': key, 'title': TRAITS[key][0],
                          'text': TRAITS[key][1], 'tip': TRAITS[key][2]}
                         for code in TYPES for key in code]
            astro_rows = [{'id': sign, 'name': name, 'key': key, 'title': TRAITS[key][0],
                           'text': TRAITS[key][1]} for sign, name, keys in SIGNS for key in keys]
            tips = [{'id': key, 'trait': trait, 'text': text} for key, trait, text in SUGGESTIONS]
            def write(tx):
                tx.run(MBTI_SEED, rows=mbti_rows).consume()
                tx.run(ASTRO_SEED, rows=astro_rows).consume()
                tx.run(SEED, rows=rows, profile=embedder.profile).consume()
                tx.run(TIPS, tips=tips).consume()
                tx.run(SUPPORTS, rows=rows).consume()
                tx.run(PROFILES, rows=rows).consume()
            with driver.session(database=database()) as session:
                session.execute_write(write)
            run(driver, f'''CREATE VECTOR INDEX {INDEX} IF NOT EXISTS
                FOR (c:RagChunk) ON c.embedding
                OPTIONS {{indexConfig: {{`vector.dimensions`: {DIMENSIONS},
                                       `vector.similarity_function`: 'cosine'}}}}''')
            run(driver, 'CALL db.awaitIndex($name, 60)', name=INDEX)
            # Use the official retriever adapter for the native Neo4j comparison.
            from neo4j_graphrag.retrievers import VectorRetriever
            retriever = VectorRetriever(driver, INDEX, embedder=embedder,
                return_properties=['id', 'title', 'text'], neo4j_database=database())
            native = retriever.get_search_results(query_vector=probe, top_k=3)
            assert len(native.records) == 3
            print('Neo4j vector search:', [r.data() for r in native.records])
            export(driver, embedder, probe)
        print(f'PASS: seed, vector index, official retriever and export ({time.perf_counter()-started:.1f}s)')
    finally:
        embedder.close()


if __name__ == '__main__':
    main()

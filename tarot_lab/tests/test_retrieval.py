import os
import tempfile
import unittest
from unittest.mock import Mock
from lumi_core.embedding.litert import DIMENSIONS
from tarot_lab.repositories.chroma import ChromaRepository, collection_name, metadata
from tarot_lab.repositories.neo4j import Neo4jRepository
from tarot_lab.fixtures.meanings_v1 import fixture_chunks
from tarot_lab.errors import ProfileMismatch, GraphUnavailable

class RetrievalContractTests(unittest.TestCase):
    def test_metadata_never_contains_null_and_profile_names_differ(self):
        self.assertNotIn(None,metadata(fixture_chunks()[0]).values())
        self.assertNotEqual(collection_name('profile-a'),collection_name('profile-b'))

    def test_graph_errors_are_not_empty_results(self):
        driver=Mock(); driver.session.side_effect=RuntimeError('offline')
        with self.assertRaises(GraphUnavailable): Neo4jRepository(driver).meaning_keywords(['major-16-tower:upright'])

    def test_profile_mismatch_is_rejected(self):
        client=Mock(); client.get_collection.return_value.metadata={'embedding_profile':'wrong','dataset_version':'tarot-v1'}
        with self.assertRaises(ProfileMismatch): ChromaRepository('.', 'expected',client=client)

@unittest.skipUnless(os.getenv('LUMI_INTEGRATION')=='1','LUMI_INTEGRATION not set')
class ChromaTests(unittest.TestCase):
    def test_real_cosine_collection_upsert_and_orientation_filter(self):
        with tempfile.TemporaryDirectory() as path:
            repo=ChromaRepository(path,'unit-contract-768',create=True)
            rows=fixture_chunks()[:10]
            vector=[1.0]+[0.0]*(DIMENSIONS-1)
            repo.upsert(rows,[vector]*len(rows)); repo.upsert(rows,[vector]*len(rows))
            self.assertEqual(repo.collection.count(),10)
            found=repo.search_for_draw(vector,'major-09-hermit','reversed',3)
            self.assertTrue(found)
            self.assertTrue(all(c['orientation']=='reversed' for c in found))
            self.assertTrue(all(abs(c['similarity']-(1-c['distance']))<1e-10 for c in found))
            repo.close()

    def test_actual_neo4j_seed_is_repeatable_and_vectors_stay_separate(self):
        from tools.seed_tarot_knowledge import seed_graph
        from tarot_lab.fixtures.meanings_v1 import tarot_chunks
        from lumi_core.graph.client import get_driver,run,database
        rows=tarot_chunks()
        for _ in range(2): seed_graph(rows)
        with get_driver() as driver:
            counts=run(driver,"MATCH (c:TarotChunk {dataset_id:'tarot-v1'}) RETURN count(c) AS n,count(c.embedding) AS vectors")[0]
            self.assertEqual(counts,{'n':180,'vectors':0})
            self.assertEqual(run(driver,'MATCH (c:RagChunk) WHERE c.embedding IS NOT NULL RETURN count(c) AS n')[0]['n'],600)
            repo=Neo4jRepository(driver,database())
            paths=repo.meaning_paths(['major-16-tower:reversed'],'INTJ','aquarius')
            self.assertTrue(paths)
            self.assertTrue(all(p['orientation']=='reversed' and p['source_id'] for p in paths))

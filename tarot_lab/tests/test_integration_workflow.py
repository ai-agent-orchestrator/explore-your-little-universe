import os
import random
import unittest
from uuid import uuid4
from unittest.mock import Mock
from tarot_lab.tests.fakes import FakeLLM
from tarot_lab.tests.test_postgres import INPUT

@unittest.skipUnless(os.getenv('LUMI_INTEGRATION')=='1','LUMI_INTEGRATION not set')
class IntegratedWorkflowTests(unittest.TestCase):
    def test_real_three_stores_and_postgres_checkpoint_resume_with_fake_llm(self):
        from lumi_core.settings import postgres,chroma_path
        from lumi_core.graph.client import get_driver,database
        from lumi_core.embedding.litert import LiteRTEmbeddings
        from tarot_lab.repositories.postgres import PostgresRepository,token_hash
        from tarot_lab.repositories.neo4j import Neo4jRepository
        from tarot_lab.repositories.chroma import ChromaRepository
        from tarot_lab.workflow.graph import ReadingWorkflow,postgres_checkpointer
        embedder=LiteRTEmbeddings()
        repo=PostgresRepository(postgres(),embedder.profile);repo.open()
        vector=None;session_id=None
        try:
            vector=ChromaRepository(chroma_path(),embedder.profile)
            row,_=repo.create_or_get_session(INPUT,str(uuid4()),token_hash(str(uuid4())),random.Random(7))
            session_id=row['session_id'];draws=row['draws']
            with get_driver() as driver:
                graph=Neo4jRepository(driver,database())
                with postgres_checkpointer(postgres(),setup=True) as saver:
                    flow=ReadingWorkflow(repo,graph,vector,embedder,FakeLLM(fail_once=True),saver)
                    with self.assertRaises(RuntimeError): flow.run(session_id)
                graph.meaning_paths=Mock(side_effect=AssertionError('Saved retrieval must not run again'))
                with postgres_checkpointer(postgres()) as saver:
                    flow=ReadingWorkflow(repo,graph,vector,embedder,FakeLLM(),saver)
                    result=flow.run(session_id)
                    self.assertEqual(result['status'],'completed')
                    self.assertEqual(result['draws'],draws)
                    self.assertTrue(result['report']['sources'])
                    saver.delete_thread(session_id)
        finally:
            if session_id:
                with repo.pool.connection() as c: c.execute('DELETE FROM lumi.reading_sessions WHERE session_id=%s',(session_id,))
            if vector: vector.close()
            repo.close();embedder.close()

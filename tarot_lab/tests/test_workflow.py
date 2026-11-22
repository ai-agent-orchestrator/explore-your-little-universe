import random
import unittest
from langgraph.checkpoint.memory import InMemorySaver
from tarot_lab.workflow.graph import ReadingWorkflow
from tarot_lab.tests.fakes import MemoryRepository,FakeEmbedder,FakeGraph,FakeVector,FakeLLM
from tarot_lab.tests.test_postgres import INPUT
from tarot_lab.repositories.postgres import token_hash

class WorkflowTests(unittest.TestCase):
    def make(self,llm=None):
        self.repo=MemoryRepository()
        row,_=self.repo.create_or_get_session(INPUT,'test-key',token_hash('owner'),random.Random(5))
        self.id=row['session_id']; self.draws=row['draws']
        self.g=FakeGraph();self.v=FakeVector();self.llm=llm or FakeLLM()
        return ReadingWorkflow(self.repo,self.g,self.v,FakeEmbedder(),self.llm,InMemorySaver())

    def test_normal_and_repeated_completed_run(self):
        workflow=self.make()
        self.assertEqual(workflow.run(self.id)['status'],'completed')
        workflow.run(self.id)
        self.assertEqual(self.llm.calls,1)
        self.assertEqual(self.repo.get(self.id)['draws'],self.draws)

    def test_two_rewrites_then_pass(self):
        workflow=self.make(FakeLLM(invalid_attempts=2))
        self.assertEqual(workflow.run(self.id)['status'],'completed')
        self.assertEqual(self.llm.calls,3)
        self.assertEqual(self.g.calls,1)

    def test_rewrite_budget_exhausted(self):
        workflow=self.make(FakeLLM(invalid_attempts=10))
        self.assertEqual(workflow.run(self.id)['status'],'validation_failed')
        self.assertEqual(self.llm.calls,3)

    def test_missing_evidence_does_not_call_llm(self):
        workflow=self.make();self.v.missing=True
        self.assertEqual(workflow.run(self.id)['status'],'needs_evidence')
        self.assertEqual(self.llm.calls,0)

    def test_checkpoint_resume_preserves_retrieval_and_draws(self):
        workflow=self.make(FakeLLM(fail_once=True))
        with self.assertRaises(RuntimeError): workflow.run(self.id)
        self.assertEqual(self.repo.get(self.id)['status'],'failed')
        self.assertEqual(workflow.run(self.id)['status'],'completed')
        self.assertEqual(self.g.calls,1)
        self.assertEqual(self.repo.get(self.id)['draws'],self.draws)

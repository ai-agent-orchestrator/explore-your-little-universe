import unittest
from uuid import uuid4
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver
from tarot_lab.api import create_app
from tarot_lab.runtime import NotReady
from tarot_lab.workflow.graph import ReadingWorkflow
from tarot_lab.tests.fakes import MemoryRepository,FakeGraph,FakeVector,FakeEmbedder,FakeLLM
from tarot_lab.tests.test_postgres import INPUT

class FakeRuntime:
    def __init__(self):
        self.repo=MemoryRepository();self.llm=FakeLLM();self.missing=None
        self.workflow=ReadingWorkflow(self.repo,FakeGraph(),FakeVector(),FakeEmbedder(),self.llm,InMemorySaver())
    def open(self): pass
    def close(self): pass
    def health(self): return {key:'missing' if key==self.missing else 'ok' for key in ('postgres','neo4j','chroma','embedding','llm')}
    def ensure_ready(self):
        if self.missing: raise NotReady(self.missing)

class APITests(unittest.TestCase):
    def setUp(self):
        self.runtime=FakeRuntime();self.client=TestClient(create_app(self.runtime));self.client.__enter__()
    def tearDown(self): self.client.__exit__(None,None,None)
    def create(self):
        key=str(uuid4());response=self.client.post('/api/readings',json=INPUT,headers={'Idempotency-Key':key})
        self.assertEqual(response.status_code,201,response.text)
        return key,response.json()

    def test_health_creation_auth_idempotency_and_forbidden_draw_fields(self):
        self.assertEqual(self.client.get('/api/health').json()['embedding'],'ok')
        key,row=self.create();url='/api/readings/'+row['session_id']
        self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.get(url,headers={'Authorization':'Bearer '+'x'*43}).status_code,404)
        headers={'Authorization':'Bearer '+row['session_token'],'Idempotency-Key':key}
        view=self.client.get(url,headers=headers).json()
        self.assertEqual(view['status'],'completed');self.assertEqual(view['draws'],row['draws'])
        self.assertNotIn('session_token',view)
        again=self.client.post('/api/readings',json=INPUT,headers=headers)
        self.assertEqual(again.status_code,200);self.assertNotIn('session_token',again.json())
        self.assertEqual(self.client.post('/api/readings',json=INPUT|{'question':'다른 질문'},headers=headers).status_code,409)
        self.assertEqual(self.client.post('/api/readings',json=INPUT|{'draws':[]},headers=headers).status_code,422)
        self.assertEqual(self.runtime.llm.calls,1)

    def test_lost_bootstrap_response_does_not_draw_another_session(self):
        key,row=self.create()
        response=self.client.post('/api/readings',json=INPUT,headers={'Idempotency-Key':key})
        self.assertEqual(response.status_code,409)
        self.assertEqual(response.json()['error'],'session_token_required')
        self.assertEqual(len(self.runtime.repo.rows),1)

    def test_sse_replay_and_resume_completed(self):
        _,row=self.create();url='/api/readings/'+row['session_id']
        headers={'Authorization':'Bearer '+row['session_token'],'Last-Event-ID':'2'}
        response=self.client.get(url+'/events',headers=headers)
        self.assertEqual(response.status_code,200)
        self.assertNotIn('id: 1\n',response.text);self.assertIn('report.completed',response.text)
        self.assertNotIn(row['session_token'],response.text)
        self.assertEqual(self.client.post(url+'/resume',headers=headers).json()['status'],'completed')
        self.assertEqual(self.runtime.llm.calls,1)

    def test_resume_rejects_existing_run_lock(self):
        _,row=self.create();id=row['session_id'];self.runtime.repo.set_status(id,'failed')
        with self.runtime.repo.run_lock(id):
            response=self.client.post('/api/readings/'+id+'/resume',headers={'Authorization':'Bearer '+row['session_token']})
            self.assertEqual(response.status_code,409)

    def test_missing_embedding_and_cors(self):
        self.runtime.missing='embedding'
        self.assertEqual(self.client.get('/api/health').json()['embedding'],'missing')
        result=self.client.post('/api/readings',json=INPUT,headers={'Idempotency-Key':str(uuid4())})
        self.assertEqual(result.status_code,503);self.assertEqual(result.json()['error'],'embedding_unavailable')
        result=self.client.options('/api/readings',headers={'Origin':'http://127.0.0.1:5173','Access-Control-Request-Method':'POST'})
        self.assertEqual(result.headers.get('access-control-allow-origin'),'http://127.0.0.1:5173')
        result=self.client.options('/api/readings',headers={'Origin':'https://other.example','Access-Control-Request-Method':'POST'})
        self.assertNotIn('access-control-allow-origin',result.headers)

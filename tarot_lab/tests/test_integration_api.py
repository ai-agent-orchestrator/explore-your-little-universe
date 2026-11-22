import os
import unittest
from uuid import uuid4

@unittest.skipUnless(os.getenv('LUMI_INTEGRATION')=='1','LUMI_INTEGRATION not set')
class RealAPIIntegrationTests(unittest.TestCase):
    def test_real_stores_http_reading_and_sse_with_fake_llm(self):
        from fastapi.testclient import TestClient
        from tarot_lab.api import create_app
        from tarot_lab.tests.real_runtime import RealStoresFakeLLMRuntime
        from tarot_lab.tests.test_postgres import INPUT
        rt=RealStoresFakeLLMRuntime()
        with TestClient(create_app(rt)) as client:
            self.assertTrue(all(v=='ok' for v in client.get('/api/health').json().values()))
            response=client.post('/api/readings',json=INPUT,headers={'Idempotency-Key':str(uuid4())})
            self.assertEqual(response.status_code,201,response.text)
            created=response.json();id=created['session_id'];headers={'Authorization':'Bearer '+created['session_token']}
            try:
                result=client.get('/api/readings/'+id,headers=headers).json()
                self.assertEqual(result['status'],'completed',result)
                self.assertEqual(result['draws'],created['draws'])
                self.assertEqual(result['report']['model_id'],'fake-test-only')
                stream=client.get('/api/readings/'+id+'/events',headers=headers|{'Last-Event-ID':'2'})
                self.assertIn('report.completed',stream.text)
                self.assertNotIn('id: 1\n',stream.text)
                self.assertEqual(client.get('/api/readings/'+id).status_code,404)
                self.assertEqual(client.post('/api/readings/'+id+'/resume',headers=headers).status_code,200)
            finally:
                with rt.repo.pool.connection() as c: c.execute('DELETE FROM lumi.reading_sessions WHERE session_id=%s',(id,))

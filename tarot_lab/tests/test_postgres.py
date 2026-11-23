import os
import random
import unittest
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from tarot_lab.repositories.postgres import PostgresRepository, draw_cards, token_hash
from tarot_lab.errors import IdempotencyConflict, RunInProgress, NotFound

INPUT={'mbti':'INTJ','zodiac_id':'aquarius','question':'처음 해보는 일을 시작할까?','spread':'three_card_reflection'}

class DrawTests(unittest.TestCase):
    def test_draw_is_reproducible_unique_and_has_all_positions(self):
        draws=draw_cards(random.Random(31))
        self.assertEqual(draws,draw_cards(random.Random(31)))
        self.assertEqual(len({d['card_id'] for d in draws}),3)
        self.assertEqual([d['position'] for d in draws],['past','present','future'])

@unittest.skipUnless(os.getenv('LUMI_INTEGRATION')=='1','LUMI_INTEGRATION not set')
class PostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tarot_lab.migrate import migrate
        migrate()
        cls.repo=PostgresRepository(os.environ['LUMI_POSTGRES_DSN'],'integration-test-profile')
        cls.repo.open()
    @classmethod
    def tearDownClass(cls): cls.repo.close()

    def setUp(self):
        self.owner=token_hash(str(uuid4())); self.key=str(uuid4())
    def tearDown(self):
        with self.repo.pool.connection() as c:
            c.execute('DELETE FROM lumi.reading_sessions WHERE owner_token_hash=%s',(self.owner,))

    def test_concurrent_idempotency_and_auth(self):
        def create(_): return self.repo.create_or_get_session(INPUT,self.key,self.owner,random.Random(9))
        with ThreadPoolExecutor(max_workers=8) as workers: results=list(workers.map(create,range(8)))
        self.assertEqual(len({row['session_id'] for row,_ in results}),1)
        self.assertEqual(sum(created for _,created in results),1)
        self.assertTrue(all(row['draws']==results[0][0]['draws'] for row,_ in results))
        with self.assertRaises(IdempotencyConflict): self.repo.create_or_get_session(INPUT|{'question':'다른 질문'},self.key,self.owner)
        with self.assertRaises(NotFound): self.repo.authorize(results[0][0]['session_id'],'wrong-token')

    def test_partial_draw_failure_rolls_back(self):
        with self.assertRaises(RuntimeError):
            self.repo.create_or_get_session(INPUT,self.key,self.owner,fail_after_draw=1)
        with self.repo.pool.connection() as c:
            self.assertEqual(c.execute('SELECT count(*) AS n FROM lumi.reading_sessions WHERE owner_token_hash=%s',(self.owner,)).fetchone()['n'],0)

    def test_advisory_lock_rejects_concurrent_run_and_releases(self):
        row,_=self.repo.create_or_get_session(INPUT,self.key,self.owner)
        with self.repo.run_lock(row['session_id']):
            with self.assertRaises(RunInProgress):
                with self.repo.run_lock(row['session_id']): pass
        with self.repo.run_lock(row['session_id']): pass

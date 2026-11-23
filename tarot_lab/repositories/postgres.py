"""Transactional service state. Every public SQL statement is parameterized."""
from contextlib import contextmanager
import hashlib
import json
import secrets
from uuid import uuid4
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool
from lumi_core.catalog.tarot import CARDS, POSITIONS
from lumi_core.versions import DATASET_VERSION, MAPPING_VERSION
from tarot_lab.errors import IdempotencyConflict, NotFound, RunInProgress, LumiError

def token_hash(token):
    return hashlib.sha256(token.encode()).digest()

def request_hash(input):
    return hashlib.sha256(json.dumps(input,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).digest()

def draw_cards(rng=None):
    rng=rng or secrets.SystemRandom()
    return [{'card_id':c.card_id,'orientation':'reversed' if rng.random()<.5 else 'upright',
             'ordinal':i,'position':POSITIONS[i]} for i,c in enumerate(rng.sample(CARDS,3))]

class TokenRequired(LumiError):
    code='session_token_required'
    status_code=409

class PostgresRepository:
    def __init__(self,dsn,embedding_profile,*,pool=None):
        self.embedding_profile=embedding_profile
        self.pool=pool or ConnectionPool(dsn,min_size=1,max_size=12,open=False,
                                         kwargs={'row_factory':dict_row},timeout=5)

    def open(self): self.pool.open(wait=True,timeout=5)
    def close(self): self.pool.close()
    def ping(self):
        with self.pool.connection() as c: c.execute('SELECT 1')

    def _event(self,c,session_id,event_type,payload):
        c.execute('SELECT session_id FROM lumi.reading_sessions WHERE session_id=%s FOR UPDATE',(session_id,))
        sequence=c.execute('SELECT COALESCE(max(sequence),0)+1 AS n FROM lumi.reading_events WHERE session_id=%s',(session_id,)).fetchone()['n']
        c.execute('INSERT INTO lumi.reading_events VALUES (%s,%s,%s,%s,now())',
                  (session_id,sequence,event_type,Jsonb(payload)))

    def create_or_get_session(self,input,idempotency_key,owner_token_hash,rng=None,*,bootstrap=False,fail_after_draw=None):
        digest=request_hash(input); session_id=uuid4()
        bootstrap_hash=token_hash('bootstrap:'+idempotency_key) if bootstrap else None
        with self.pool.connection() as c:
            row=c.execute('''INSERT INTO lumi.reading_sessions
                (session_id,owner_token_hash,bootstrap_key_hash,idempotency_key,request_hash,mbti,zodiac_id,
                 question,spread,dataset_version,mapping_version,embedding_profile,status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'draw_confirmed')
                ON CONFLICT DO NOTHING RETURNING session_id''',
                (session_id,owner_token_hash,bootstrap_hash,idempotency_key,digest,input['mbti'],input['zodiac_id'],
                 input['question'],input['spread'],DATASET_VERSION,MAPPING_VERSION,self.embedding_profile)).fetchone()
            if not row:
                existing=c.execute('SELECT session_id,request_hash FROM lumi.reading_sessions WHERE owner_token_hash=%s AND idempotency_key=%s',
                                   (owner_token_hash,idempotency_key)).fetchone()
                if existing:
                    if bytes(existing['request_hash'])!=digest: raise IdempotencyConflict()
                    session_id=existing['session_id']; created=False
                else:
                    # A lost first response must never silently produce another draw.
                    raise TokenRequired()
            else:
                created=True
                for draw in draw_cards(rng):
                    c.execute('INSERT INTO lumi.reading_draws VALUES (%s,%s,%s,%s,%s)',
                              (session_id,draw['ordinal'],draw['position'],draw['card_id'],draw['orientation']))
                    if fail_after_draw==draw['ordinal']: raise RuntimeError('Injected transaction failure')
                self._event(c,session_id,'session.created',{})
                self._event(c,session_id,'draw.confirmed',{})
        return self.get(session_id),created

    def get(self,session_id):
        with self.pool.connection() as c:
            row=c.execute('''SELECT session_id,mbti,zodiac_id,question,spread,dataset_version,mapping_version,
                embedding_profile,status,error_code FROM lumi.reading_sessions WHERE session_id=%s''',(session_id,)).fetchone()
            if not row: raise NotFound()
            row['session_id']=str(row['session_id'])
            row['draws']=c.execute('SELECT card_id,orientation,position,ordinal FROM lumi.reading_draws WHERE session_id=%s ORDER BY ordinal',(session_id,)).fetchall()
            report=c.execute('SELECT report FROM lumi.reading_reports WHERE session_id=%s',(session_id,)).fetchone()
            row['report']=report['report'] if report else None
            return row

    def authorize(self,session_id,token):
        with self.pool.connection() as c:
            row=c.execute('SELECT owner_token_hash FROM lumi.reading_sessions WHERE session_id=%s',(session_id,)).fetchone()
        if not row or not secrets.compare_digest(bytes(row['owner_token_hash']),token_hash(token or '')):
            raise NotFound()

    def find_by_key(self,token,key):
        with self.pool.connection() as c:
            row=c.execute('SELECT session_id FROM lumi.reading_sessions WHERE owner_token_hash=%s AND idempotency_key=%s',
                          (token_hash(token),key)).fetchone()
        if not row: raise NotFound()
        return self.get(row['session_id'])

    @contextmanager
    def run_lock(self,session_id):
        # Hold this transaction only for its advisory lock. Service writes and
        # checkpointer writes use separate connections; no row lock is held here.
        with self.pool.connection() as c:
            acquired=c.execute('SELECT pg_try_advisory_xact_lock(hashtextextended(%s,0)) AS acquired',(str(session_id),)).fetchone()['acquired']
            if not acquired: raise RunInProgress()
            yield

    def event(self,session_id,event_type,payload=None):
        with self.pool.connection() as c: self._event(c,session_id,event_type,payload or {})

    def set_status(self,session_id,status,error_code=None):
        with self.pool.connection() as c:
            c.execute('UPDATE lumi.reading_sessions SET status=%s,error_code=%s WHERE session_id=%s',(status,error_code,session_id))
            if status in ('failed','needs_evidence','validation_failed'):
                self._event(c,session_id,'report.needs_evidence' if status=='needs_evidence' else 'run.failed',{'status':status,'error_code':error_code})

    def save_report(self,session_id,report,evidence_ids,validation,model_id):
        with self.pool.connection() as c:
            c.execute('SELECT session_id FROM lumi.reading_sessions WHERE session_id=%s FOR UPDATE',(session_id,))
            inserted=c.execute('''INSERT INTO lumi.reading_reports
                (session_id,report,evidence_ids,validation,model_id,prompt_version)
                VALUES (%s,%s,%s,%s,%s,'tarot-json-v1') ON CONFLICT DO NOTHING RETURNING session_id''',
                (session_id,Jsonb(report),Jsonb(evidence_ids),Jsonb(validation),model_id)).fetchone()
            c.execute("UPDATE lumi.reading_sessions SET status='completed',error_code=NULL WHERE session_id=%s",(session_id,))
            if inserted: self._event(c,session_id,'report.completed',{'status':'completed'})

    def events(self,session_id,after=0):
        with self.pool.connection() as c:
            return c.execute('SELECT sequence,event_type,payload FROM lumi.reading_events WHERE session_id=%s AND sequence>%s ORDER BY sequence LIMIT 100',
                             (session_id,after)).fetchall()

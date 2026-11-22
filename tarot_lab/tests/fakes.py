"""Explicit test doubles; never selected by production settings."""
import copy
from contextlib import contextmanager
import threading
from uuid import uuid4
from lumi_core.versions import DATASET_VERSION,MAPPING_VERSION
from tarot_lab.repositories.postgres import draw_cards,request_hash,token_hash,TokenRequired
from tarot_lab.errors import NotFound,RunInProgress,IdempotencyConflict
from tarot_lab.fixtures.meanings_v1 import tarot_chunks

class MemoryRepository:
    embedding_profile='test-profile'
    def __init__(self):
        self.rows={}; self.tokens={}; self.keys={}; self.bootstrap=set(); self.events_by_id={}; self.locks={}
    def create_or_get_session(self,input,key,owner,rng=None,*,bootstrap=False,**kwargs):
        if (owner,key) in self.keys:
            id=self.keys[owner,key]
            if self.rows[id]['request_hash']!=request_hash(input): raise IdempotencyConflict()
            return self.get(id),False
        if bootstrap and key in self.bootstrap: raise TokenRequired()
        id=str(uuid4())
        self.rows[id]=input|{'session_id':id,'request_hash':request_hash(input),'draws':draw_cards(rng),
            'dataset_version':DATASET_VERSION,'mapping_version':MAPPING_VERSION,'embedding_profile':self.embedding_profile,
            'status':'draw_confirmed','error_code':None,'report':None}
        self.keys[owner,key]=id; self.tokens[id]=owner; self.locks[id]=threading.Lock()
        if bootstrap: self.bootstrap.add(key)
        self.event(id,'session.created');self.event(id,'draw.confirmed')
        return self.get(id),True
    def get(self,id):
        if str(id) not in self.rows: raise NotFound()
        return copy.deepcopy(self.rows[str(id)])
    def authorize(self,id,token):
        if self.tokens.get(str(id))!=token_hash(token or ''): raise NotFound()
    def find_by_key(self,token,key):
        if (token_hash(token),key) not in self.keys: raise NotFound()
        return self.get(self.keys[token_hash(token),key])
    @contextmanager
    def run_lock(self,id):
        if not self.locks[str(id)].acquire(blocking=False): raise RunInProgress()
        try: yield
        finally: self.locks[str(id)].release()
    def event(self,id,event_type,payload=None):
        events=self.events_by_id.setdefault(str(id),[])
        events.append({'sequence':len(events)+1,'event_type':event_type,'payload':payload or {}})
    def events(self,id,after=0): return [e for e in self.events_by_id[str(id)] if e['sequence']>after]
    def set_status(self,id,status,error_code=None):
        self.rows[str(id)].update(status=status,error_code=error_code)
        if status in ('failed','needs_evidence','validation_failed'):
            self.event(id,'report.needs_evidence' if status=='needs_evidence' else 'run.failed',{'error_code':error_code})
    def save_report(self,id,report,evidence_ids,validation,model_id):
        self.rows[str(id)].update(report=report,status='completed',error_code=None)
        self.event(id,'report.completed')
    def ping(self): pass

class FakeEmbedder:
    profile='test-profile'
    def embed_query(self,text): return [1.0]+[0.0]*767
    def close(self): pass

class FakeGraph:
    calls=0
    def meaning_paths(self,*args):
        self.calls+=1
        return [{'id':'test-path','source_id':'authored-test','node_ids':['meaning','rule','trait']}]
    def element_paths(self,*args): return []
    def meaning_keywords(self,*args): return ['기준과 선택']

class FakeVector:
    missing=False
    def search_pair(self,plain,expanded,draws):
        rows=tarot_chunks()
        variant={'draws':[{'draw':d,'chunks':[] if self.missing else [c for c in rows if c['card_id']==d['card_id'] and c['orientation']==d['orientation']][:1]} for d in draws], 'general':[]}
        return {'question':variant,'expanded':copy.deepcopy(variant)}

class FakeLLM:
    model_id='fake-test-only'
    def __init__(self,invalid_attempts=0,fail_once=False):
        self.calls=0;self.invalid_attempts=invalid_attempts;self.fail_once=fail_once
    def generate(self,state):
        self.calls+=1
        if self.fail_once and self.calls==1: raise RuntimeError('Injected LLM interruption')
        sections=[]
        for d in state['draws']:
            chunk=next(c for c in state['chunks'] if c.get('card_id')==d['card_id'] and c.get('orientation')==d['orientation'])
            base=(chunk['text']+' 이 문장은 예측 결과가 아니라 질문을 살피는 테스트용 관점이다. 확인된 사실과 내 해석을 나누고, 바꿀 수 있는 작은 행동을 생각해본다. ')
            body=(base*5)[:400]
            sections.append({key:d[key] for key in ('card_id','orientation','position')}|{'body':body,'citations':[chunk['id']]})
        if self.calls<=self.invalid_attempts: sections[0]['citations']=['invented-citation']
        return {'sections':sections,'summary':'테스트용 FakeLLM으로 생성한 문장이다. 실제 모델 품질 검증이나 미래 예측이 아니다. 각 카드의 근거를 확인하고 내 상황에 맞는 질문을 골라본다.',
                'small_action':'오늘 확인할 사실 하나와 편한 사람에게 물어볼 질문 하나를 적어본다.'}
    def critique(self,state): return []
    def close(self): pass

"""uvicorn tarot_lab.api:app --host 127.0.0.1 --port 8017"""
import asyncio
from contextlib import asynccontextmanager
from dataclasses import asdict
import json
import logging
import re
import secrets
from typing import Annotated
from uuid import UUID
from fastapi import FastAPI, BackgroundTasks, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse,StreamingResponse
from starlette.concurrency import run_in_threadpool
from tarot_lab.errors import LumiError,NotFound
from tarot_lab.runtime import Runtime,NotReady
from tarot_lab.schemas import ReadingInput,ReadingResponse,ReadingView
from tarot_lab.repositories.postgres import token_hash
from lumi_core.catalog.tarot import CARDS

logger=logging.getLogger(__name__)
TERMINAL={'completed','failed','needs_evidence','validation_failed'}

def bearer(value):
    if not value: return ''
    if not re.fullmatch(r'Bearer [A-Za-z0-9_-]{32,128}',value): raise NotFound()
    return value[7:]

def create_app(runtime=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.runtime=runtime or Runtime()
        await run_in_threadpool(app.state.runtime.open)
        try: yield
        finally: await run_in_threadpool(app.state.runtime.close)

    app=FastAPI(title='Lumi Tarot Local Experiment',lifespan=lifespan)
    app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:5173'],
        allow_methods=['GET','POST'],allow_headers=['Authorization','Content-Type','Idempotency-Key','Last-Event-ID'])

    @app.exception_handler(LumiError)
    async def domain_error(request,exc): return JSONResponse({'error':exc.code},status_code=exc.status_code)

    # Database details (including connection information) never reach responses.
    import psycopg
    @app.exception_handler(psycopg.Error)
    async def postgres_error(request,exc): return JSONResponse({'error':'postgres_unavailable'},status_code=503)

    def resources(request): return request.app.state.runtime
    def repo_for(request):
        repo=resources(request).repo
        if repo is None: raise NotReady('postgres')
        return repo
    def authorized(request,id,authorization):
        repo=repo_for(request);repo.authorize(id,bearer(authorization));return repo
    def view(row):
        return ReadingView(**{key:row.get(key) for key in ReadingView.model_fields}).model_dump(mode='json')
    def schedule(rt,id,background):
        lease=rt.repo.run_lock(id)
        lease.__enter__()  # Acquire before accepting resume, including other processes.
        try:
            rt.repo.set_status(id,'running')
            def execute():
                try: rt.workflow.run(id,locked=True)
                except Exception as exc: logger.error('Reading execution failed (%s)',type(exc).__name__)
                finally: lease.__exit__(None,None,None)
            background.add_task(execute)
        except Exception:
            lease.__exit__(None,None,None);raise

    @app.get('/api/health')
    def health(request:Request): return resources(request).health()

    @app.get('/api/cards')
    def catalogue(): return [asdict(card) for card in CARDS]

    @app.post('/api/readings')
    def create(input:ReadingInput,request:Request,background:BackgroundTasks,
               idempotency_key:Annotated[str,Header(min_length=16,max_length=128,pattern=r'^[A-Za-z0-9_-]+$')],
               authorization:Annotated[str | None,Header()]=None):
        rt=resources(request);rt.ensure_ready()
        token=bearer(authorization)
        if token:
            existing=rt.repo.find_by_key(token,idempotency_key)
            row,created=rt.repo.create_or_get_session(input.model_dump(),idempotency_key,token_hash(token))
        else:
            token=secrets.token_urlsafe(32)
            row,created=rt.repo.create_or_get_session(input.model_dump(),idempotency_key,token_hash(token),bootstrap=True)
        if created: schedule(rt,row['session_id'],background)
        output=ReadingResponse(session_id=row['session_id'],session_token=token if created else None,
            status='running' if created else row['status'],draws=row['draws'],events_url=f"/api/readings/{row['session_id']}/events")
        return JSONResponse(output.model_dump(mode='json',exclude_none=True),status_code=201 if created else 200)

    @app.get('/api/readings/{id}',response_model=ReadingView)
    def get(id:UUID,request:Request,authorization:Annotated[str | None,Header()]=None):
        repo=authorized(request,id,authorization);return view(repo.get(id))

    @app.post('/api/readings/{id}/resume')
    def resume(id:UUID,request:Request,background:BackgroundTasks,
               authorization:Annotated[str | None,Header()]=None):
        repo=authorized(request,id,authorization);row=repo.get(id)
        if row['status']=='completed': return view(row)
        rt=resources(request);rt.ensure_ready();schedule(rt,str(id),background)
        return JSONResponse({'session_id':str(id),'status':'running'},status_code=202)

    @app.get('/api/readings/{id}/events')
    async def events(id:UUID,request:Request,authorization:Annotated[str | None,Header()]=None,
                     last_event_id:Annotated[int,Header(ge=0)]=0):
        repo=await run_in_threadpool(authorized,request,id,authorization)
        async def stream():
            cursor=last_event_id;heartbeats=0
            while not await request.is_disconnected():
                rows=await run_in_threadpool(repo.events,id,cursor)
                for event in rows:
                    cursor=event['sequence']
                    yield f"id: {cursor}\nevent: {event['event_type']}\ndata: {json.dumps(event['payload'],ensure_ascii=False)}\n\n"
                current=await run_in_threadpool(repo.get,id)
                if current['status'] in TERMINAL and len(rows)<100: break
                heartbeats+=1
                if heartbeats%20==0: yield ': heartbeat\n\n'
                await asyncio.sleep(.25)
        return StreamingResponse(stream(),media_type='text/event-stream',
            headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})

    return app

app=create_app()

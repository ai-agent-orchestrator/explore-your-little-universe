"""One engine and explicit resource lifecycle for the optional server mode."""
from contextlib import ExitStack
from tarot_lab.config import load_settings
from tarot_lab.errors import LumiError

class NotReady(LumiError):
    def __init__(self,component): self.code=component+'_unavailable'

class Runtime:
    def __init__(self,settings=None):
        self.settings=settings
        self.repo=self.graph_repository=self.vector_repository=self.embedder=self.llm=self.workflow=None
        self.status={key:'missing' for key in ('postgres','neo4j','chroma','embedding','llm')}
        self.stack=ExitStack()

    def open(self):
        from lumi_core.embedding.litert import LiteRTEmbeddings
        from lumi_core.graph.client import get_driver,database
        from tarot_lab.repositories.postgres import PostgresRepository
        from tarot_lab.repositories.neo4j import Neo4jRepository
        from tarot_lab.repositories.chroma import ChromaRepository
        from tarot_lab.llm import CompatibleLLM
        from tarot_lab.workflow.graph import ReadingWorkflow,postgres_checkpointer
        self.settings=self.settings or load_settings()
        if self.settings.model_path.is_file():
            try:
                self.embedder=LiteRTEmbeddings(self.settings.model_path)
                self.stack.callback(self.embedder.close);self.status['embedding']='ok'
            except Exception: self.status['embedding']='error'
        if self.settings.postgres_dsn:
            candidate=PostgresRepository(self.settings.postgres_dsn,self.embedder.profile if self.embedder else 'embedding-unavailable')
            try:
                candidate.open(); self.repo=candidate; self.stack.callback(candidate.close)
                candidate.ping(); self.status['postgres']='ok'
            except Exception:
                candidate.close(); self.repo=None; self.status['postgres']='error'
        try:
            driver=get_driver();self.stack.callback(driver.close)
            self.graph_repository=Neo4jRepository(driver,database())
            self.graph_repository.ping();self.status['neo4j']='ok'
        except ValueError: pass
        except Exception: self.status['neo4j']='error'
        if self.embedder:
            try:
                self.vector_repository=ChromaRepository(self.settings.chroma_path,self.embedder.profile)
                self.stack.callback(self.vector_repository.close)
                self.vector_repository.ping();self.status['chroma']='ok'
            except Exception: self.status['chroma']='error'
        if all(self.settings.llm.values()):
            self.llm=CompatibleLLM(self.settings.llm)
            self.stack.callback(self.llm.close); self.status['llm']='ok'
        if all(value=='ok' for value in self.status.values()):
            try:
                saver=self.stack.enter_context(postgres_checkpointer(self.settings.postgres_dsn))
                self.workflow=ReadingWorkflow(self.repo,self.graph_repository,self.vector_repository,self.embedder,self.llm,saver)
            except Exception: self.status['postgres']='error'

    def health(self):
        for key,service in [('postgres',self.repo),('neo4j',self.graph_repository),('chroma',self.vector_repository)]:
            if service:
                try: service.ping();self.status[key]='ok'
                except Exception: self.status[key]='error'
        return dict(self.status)

    def ensure_ready(self):
        from tarot_lab.errors import LLMNotConfigured
        health=self.health()
        if health['embedding']!='ok': raise NotReady('embedding')
        if health['llm']!='ok': raise LLMNotConfigured()
        for component in ('postgres','neo4j','chroma'):
            if health[component]!='ok': raise NotReady(component)
        if self.workflow is None: raise NotReady('workflow')

    def close(self): self.stack.close()

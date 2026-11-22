"""Explicit integration-test runtime: real stores and embeddings, fake LLM only."""
from dataclasses import replace
from tarot_lab.config import load_settings
from tarot_lab.runtime import Runtime
from tarot_lab.tests.fakes import FakeLLM
from tarot_lab.workflow.graph import ReadingWorkflow,postgres_checkpointer

class RealStoresFakeLLMRuntime(Runtime):
    def __init__(self):
        super().__init__(replace(load_settings(),llm={}))
    def open(self):
        super().open()
        if any(self.status[key]!='ok' for key in ('postgres','neo4j','chroma','embedding')):
            raise RuntimeError('Real integration stores must be prepared')
        self.llm=FakeLLM();self.stack.callback(self.llm.close);self.status['llm']='ok'
        saver=self.stack.enter_context(postgres_checkpointer(self.settings.postgres_dsn))
        self.workflow=ReadingWorkflow(self.repo,self.graph_repository,self.vector_repository,self.embedder,self.llm,saver)

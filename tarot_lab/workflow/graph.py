from contextlib import contextmanager
from functools import partial
from types import SimpleNamespace
from langgraph.graph import StateGraph, START, END
from .state import ReadingState
from . import nodes
from tarot_lab.errors import LumiError, RunInProgress

def route_after_validate(state):
    errors=state['validation_errors']
    if not errors: return 'persist_report'
    if 'missing_evidence_for_card' in errors: return 'persist_needs_evidence'
    return 'generate' if state['rewrite_count']<2 else 'persist_failed'

def build_graph(services,checkpointer):
    graph=StateGraph(ReadingState)
    names=('load_confirmed_draws','retrieve_graph','retrieve_semantic','generate','validate',
           'persist_report','persist_needs_evidence','persist_failed')
    for name in names: graph.add_node(name,partial(getattr(nodes,name),services=services))
    graph.add_edge(START,'load_confirmed_draws')
    for a,b in zip(names[:4],names[1:5]): graph.add_edge(a,b)
    graph.add_conditional_edges('validate',route_after_validate,
        {name:name for name in ('persist_report','persist_needs_evidence','generate','persist_failed')})
    for name in names[-3:]: graph.add_edge(name,END)
    return graph.compile(checkpointer=checkpointer)

@contextmanager
def postgres_checkpointer(dsn,*,setup=False):
    from psycopg.conninfo import make_conninfo
    from langgraph.checkpoint.postgres import PostgresSaver
    with PostgresSaver.from_conn_string(make_conninfo(dsn,options='-c search_path=langgraph')) as saver:
        if setup: saver.setup()
        yield saver

class ReadingWorkflow:
    def __init__(self,repo,graph_repository,vector_repository,embedder,llm,checkpointer):
        self.repo=repo
        self.services=SimpleNamespace(repo=repo,graph_repository=graph_repository,
            vector_repository=vector_repository,embedder=embedder,llm=llm)
        self.graph=build_graph(self.services,checkpointer)

    def run(self,session_id,*,locked=False):
        if not locked:
            with self.repo.run_lock(session_id): return self.run(session_id,locked=True)
        row=self.repo.get(session_id)
        if row['status']=='completed': return row
        self.repo.set_status(session_id,'running')
        config={'configurable':{'thread_id':str(session_id)},'recursion_limit':20}
        try:
            saved=self.graph.get_state(config)
            initial=None if saved.next else {'session_id':str(session_id),'rewrite_count':0,
                'graph_paths':[],'keywords':[],'chunks':[],'retrieval_comparison':{},'draft':{},
                'validation_errors':[],'status':'running'}
            self.graph.invoke(initial,config)
        except RunInProgress: raise
        except Exception as exc:
            code=exc.code if isinstance(exc,LumiError) else 'workflow_failed'
            self.repo.set_status(session_id,'failed',code)
            raise
        return self.repo.get(session_id)

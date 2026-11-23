from lumi_core.versions import DATASET_VERSION, MAPPING_VERSION
from tarot_lab.errors import ProfileMismatch
from .validators import validate_report,render_markdown

def load_confirmed_draws(state,*,services):
    row=services.repo.get(state['session_id'])
    if (row['dataset_version']!=DATASET_VERSION or row['mapping_version']!=MAPPING_VERSION
            or row['embedding_profile']!=services.embedder.profile): raise ProfileMismatch()
    return {key:row[key] for key in ('question','mbti','zodiac_id','draws','dataset_version','mapping_version','embedding_profile')}

def retrieve_graph(state,*,services):
    ids=[d['card_id']+':'+d['orientation'] for d in state['draws']]
    paths=services.graph_repository.meaning_paths(ids,state['mbti'],state['zodiac_id'],state['mapping_version'])
    elements=services.graph_repository.element_paths([d['card_id'] for d in state['draws']],state['zodiac_id'],state['mapping_version'])
    for element in elements:
        paths.append(element|{'id':f"element:{element['card_id']}:{state['zodiac_id']}",
                              'node_ids':[element['card_id'],element['card_element'],state['zodiac_id'],element['zodiac_element']]})
    keywords=services.graph_repository.meaning_keywords(ids)[:12]
    services.repo.event(state['session_id'],'graph.completed',{'paths':len(paths)})
    return {'graph_paths':paths[:30],'keywords':keywords}

def retrieve_semantic(state,*,services):
    plain=services.embedder.embed_query(state['question'])
    expanded=services.embedder.embed_query(state['question']+'\n'+' '.join(state['keywords'])) if state['keywords'] else plain
    comparison=services.vector_repository.search_pair(plain,expanded,state['draws'])
    unique={}
    for variant in comparison.values():
        for group in variant['draws']:
            for chunk in group['chunks']: unique[chunk['id']]=chunk
        for chunk in variant['general']: unique[chunk['id']]=chunk
    services.repo.event(state['session_id'],'retrieval.completed',{'chunks':len(unique)})
    return {'chunks':list(unique.values()),'retrieval_comparison':comparison}

def generate(state,*,services):
    # Never spend a generation call when a selected direction has no source.
    missing=any(not any(c.get('card_id')==d['card_id'] and c.get('orientation')==d['orientation']
                        for c in state['chunks']) for d in state['draws'])
    if missing: return {'draft':{},'validation_errors':['missing_evidence_for_card']}
    services.repo.event(state['session_id'],'draft.validating',{'attempt':state['rewrite_count']+1})
    draft=services.llm.generate(state)
    return {'draft':draft,'rewrite_count':state['rewrite_count']+(1 if state.get('validation_errors') else 0)}

def validate(state,*,services):
    errors=validate_report(state)
    if not errors: errors=services.llm.critique(state)
    return {'validation_errors':errors}

def persist_report(state,*,services):
    ids=sorted({id for s in state['draft']['sections'] for id in s['citations']})
    report=state['draft']|{'markdown':render_markdown(state['draft']),
                           'sources':[{key:c.get(key,'') for key in ('id','title','text','source','source_url','card_id','orientation')} for c in state['chunks']],
                           'graph_paths':state['graph_paths'],'model_id':services.llm.model_id}
    services.repo.save_report(state['session_id'],report,ids,{'errors':[],'rewrites':state['rewrite_count']},services.llm.model_id)
    return {'status':'completed','error_code':None}

def persist_needs_evidence(state,*,services):
    services.repo.set_status(state['session_id'],'needs_evidence','missing_evidence_for_card')
    return {'status':'needs_evidence','error_code':'missing_evidence_for_card'}

def persist_failed(state,*,services):
    services.repo.set_status(state['session_id'],'validation_failed','validation_failed')
    return {'status':'validation_failed','error_code':'validation_failed'}

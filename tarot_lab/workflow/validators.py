from pydantic import ValidationError
from lumi_core.catalog.tarot import BY_ID
from tarot_lab.schemas import DraftReport

def report_text(report):
    return '\n'.join([s['body'] for s in report['sections']]+[report['summary'],report['small_action']])

def validate_report(state):
    errors=[]
    chunks=state['chunks']
    for draw in state['draws']:
        if not any(c.get('card_id')==draw['card_id'] and c.get('orientation')==draw['orientation'] for c in chunks):
            errors.append('missing_evidence_for_card')
    if errors: return sorted(set(errors))
    try: report=DraftReport.model_validate(state['draft']).model_dump()
    except ValidationError: return ['invalid_report_schema']
    expected={(d['card_id'],d['orientation'],d['position']) for d in state['draws']}
    actual={(s['card_id'],s['orientation'],s['position']) for s in report['sections']}
    if actual!=expected or len(actual)!=3: errors.append('draw_mismatch')
    allowed={c['id'] for c in chunks}|{p['id'] for p in state['graph_paths']}
    for section in report['sections']:
        if not set(section['citations'])<=allowed: errors.append('unknown_citation')
        own={c['id'] for c in chunks if c.get('card_id')==section['card_id'] and c.get('orientation')==section['orientation']}
        if not own.intersection(section['citations']): errors.append('missing_citation_for_card')
        if section['orientation']=='reversed' and any(term in section['body'] for term in ('불길','최악','저주')):
            errors.append('reversed_fatalism')
    if not 1200<=len(report_text(report))<=2000: errors.append('report_length')
    return sorted(set(errors))

def render_markdown(report):
    sections=[]
    for section in report['sections']:
        card=BY_ID[section['card_id']]
        label='정방향' if section['orientation']=='upright' else '역방향'
        sections.append(f"### {section['position']} · {card.name_ko} ({label})\n\n{section['body']}\n\n근거: "+', '.join(section['citations']))
    return '\n\n'.join(sections+[report['summary'],'작은 행동: '+report['small_action']])

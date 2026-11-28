from lumi_core.catalog.traits import TYPES, TRAITS
from .interpretations import interpretation_cards

def result(code):
    if code not in TYPES:
        raise ValueError('Unknown type')
    traits = [{'id': letter, 'title': TRAITS[letter][0], 'text': TRAITS[letter][1],
               'tip': TRAITS[letter][2]} for letter in code]
    nodes = [{'id': code, 'label': code, 'kind': 'type'}]
    edges = []
    for trait in traits:
        nodes.extend([{'id': trait['id'], 'label': trait['title'], 'kind': 'trait'},
                      {'id': 'tip-' + trait['id'], 'label': trait['tip'], 'kind': 'tip'}])
        edges.extend([{'source': code, 'target': trait['id'], 'label': 'HAS_TRAIT'},
                      {'source': trait['id'], 'target': 'tip-' + trait['id'], 'label': 'SUGGESTS'}])
    interpretations = [card for card in interpretation_cards()
                       if card['subject_kind'] == 'mbti' and card['subject'] == code]
    return {'type': code, 'traits': traits, 'nodes': nodes, 'edges': edges,
            'interpretations': interpretations}

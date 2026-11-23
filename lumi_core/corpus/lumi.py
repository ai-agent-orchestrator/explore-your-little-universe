from lumi_core.catalog.traits import SUGGESTIONS
from .original import RAW_CARDS
from .interpretations import interpretation_cards
from .everyday import everyday_cards

def cards():
    suggestions = {key: (trait, text) for key, trait, text in SUGGESTIONS}
    original = [{'id': f'scenario-{i:02}', 'title': title, 'text': text,
             'traits': sorted({suggestions[key][0] for key in tips}), 'tips': tips,
             'category': ['약속', '연락', '일', '휴식', '여행', '선택', '나의 속도', '가족과 관계', '창작', '거리 두기'][(i-1)//6]}
            for i, (title, text, tips) in enumerate(RAW_CARDS, 1)]
    for card in original:
        card.update(kind='scenario', subject_kind='', subject='',
                    document_id='mindmap-' + card['category'],
                    document_title=card['category'] + ' 상황 모음',
                    source='마음의 지도 직접 작성한 가상 상황 카드 v1',
                    source_url='', reviewed_on='2026-11-22',
                    editorial_note='기존 직접 작성 가상 사례. ID와 본문을 유지함.')
    return original + interpretation_cards() + everyday_cards()

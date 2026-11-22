"""Original entertainment copy, not clinical interpretation or an MBTI assessment."""
from itertools import product

TRAITS = {
    'I': ('혼자 충전', '조용한 시간을 확보하면 생각을 정리하기 편할 수 있어요.', '오늘 나만을 위한 10분을 남겨보세요.'),
    'E': ('함께 충전', '누군가와 이야기하며 생각을 발견하는 편일 수 있어요.', '편한 사람에게 오늘의 작은 발견을 나눠보세요.'),
    'S': ('구체적인 관찰', '눈앞의 사실과 경험에서 실마리를 찾는 편일 수 있어요.', '오늘 좋았던 장면을 구체적으로 한 줄 적어보세요.'),
    'N': ('가능성 탐색', '서로 다른 아이디어를 연결하는 일을 즐길 수 있어요.', '떠오른 아이디어 하나를 작은 행동으로 바꿔보세요.'),
    'T': ('이유 살피기', '선택할 때 기준과 논리를 먼저 살펴볼 수 있어요.', '대화에서 이유와 함께 상대의 기분도 물어보세요.'),
    'F': ('마음 살피기', '선택이 사람에게 미칠 영향을 먼저 생각할 수 있어요.', '다른 사람의 바람과 내 바람을 하나씩 적어보세요.'),
    'J': ('계획의 편안함', '다음 순서가 정해져 있으면 편안할 수 있어요.', '오늘 할 일 세 가지와 쉴 시간을 함께 정해보세요.'),
    'P': ('유연한 선택', '상황에 따라 선택지를 열어두는 편일 수 있어요.', '가능성을 열어두되 작은 마감 하나를 정해보세요.'),
}
TYPES = [''.join(parts) for parts in product('IE', 'SN', 'TF', 'JP')]


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
    from .interpretations import interpretation_cards
    interpretations = [card for card in interpretation_cards()
                       if card['subject_kind'] == 'mbti' and card['subject'] == code]
    return {'type': code, 'traits': traits, 'nodes': nodes, 'edges': edges,
            'interpretations': interpretations}

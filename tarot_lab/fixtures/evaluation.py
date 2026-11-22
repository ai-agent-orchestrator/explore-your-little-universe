"""Fixed evaluation inputs only; not exposed as a public draw override."""
from lumi_core.catalog.traits import TYPES
from lumi_core.catalog.zodiac import SIGNS
QUESTIONS = [
 '새 일을 시작하고 싶은데 익숙한 방식을 바꾸기가 두려워.',
 '회의에서 다른 의견을 말하면 분위기를 해칠까 걱정돼.',
 '친구에게 혼자 쉬고 싶다고 어떻게 이야기할까?',
 '내가 준비한 계획이 갑자기 바뀌어서 당황스러워.',
 '열심히 해도 진전이 없는 것 같아 기대하기가 어려워.',
 '가까운 사람에게 도움을 요청하는 게 어색해.',
 '남이 추천한 목표가 내게도 맞는지 모르겠어.',
 '완벽하게 준비하다가 시작할 시점을 놓치는 것 같아.',
 '친구의 답장이 늦으면 자꾸 의미를 추측하게 돼.',
 '새 프로젝트에서 내가 맡을 범위를 정하고 싶어.',
 '모두의 부탁을 들어주다 내 시간이 사라졌어.',
 '공부를 다시 시작하려는데 무엇부터 해야 할까?',
 '새로운 사람을 만나고 싶지만 큰 모임은 부담스러워.',
 '잘 끝낸 일보다 작은 실수만 계속 떠올라.',
 '쉬는 날에도 해야 할 일을 계속 찾고 있어.',
 '예전과 달라진 친구와 어떤 이야기를 나눌까?',
 '갑자기 여행을 가자는 제안이 끌리면서도 불편해.',
 '내 생각을 정리하려면 혼자 있는 시간이 필요해.',
 '같은 고민을 반복하는데 다른 관점을 보고 싶어.',
 '창작물을 보여주려니 나 자신이 평가받는 기분이야.',
 '동료의 피드백과 내 취향을 어떻게 나누어 볼까?',
 '계획표가 어긋나면 하루를 포기하고 싶어져.',
 '내 방식만 고집하지 않으면서 기준을 지키고 싶어.',
 '오래 붙잡은 일을 마무리할 조건을 정하고 싶어.',
 '가족의 기대와 내가 바라는 생활이 다른 것 같아.',
 '서로 다른 연락 빈도를 편하게 조율하고 싶어.',
 '돈과 관련된 걱정을 혼자 계속 반복해서 생각해.',
 '내가 정말 원하는 경험이 무엇인지 돌아보고 싶어.',
 '실수한 뒤 다시 참여할 용기를 찾고 싶어.',
 '중요한 선택을 앞두고 사실과 추측을 구분하고 싶어.',
]

def evaluation_cases():
    ids=['major-16-tower','major-17-star','major-09-hermit']
    return [{'id':f'tarot-eval-{i+1:02}','question':question,'mbti':TYPES[i%16],
             'zodiac_id':SIGNS[i%12][0],'draws':[
                 {'card_id':card,'orientation':'reversed' if (i+j)%2 else 'upright',
                  'ordinal':j,'position':['past','present','future'][j]}
                 for j,card in enumerate(ids)]} for i,question in enumerate(QUESTIONS)]

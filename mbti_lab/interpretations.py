"""Short source-informed paraphrases plus original, fictional applications.

These are editorial learning cards, not copied articles or assessment results.
16Personalities uses its own NERIS model, distinct from the official MBTI.
The cross-system trait/tip mappings are authored for this graph lab.
"""

REVIEWED_ON = '2026-11-22'
FACETS = ['기본 성향', '강점', '주의할 점', '대화', '친구와 관계',
          '협업', '배움', '휴식', '선택', '작은 성장']

# Ten independently written facets per profile. Each line: text | supported tips.
MBTI_PROFILES = {
    'INTJ': '''
복잡한 일을 장기적인 그림으로 정리하는 모습으로 자주 소개된다.|meaning,priority
흩어진 정보를 연결해 개선 방향을 찾는 상황을 떠올려볼 수 있다.|idea,criteria
내 기준이 높아 초안을 보여주는 시점까지 늦어지는 날이 있다.|try,buffer
결론만 전하기보다 판단에 쓴 기준을 설명하면 의도를 나누기 쉽다.|reason,facts
함께 있는 시간만큼 혼자 생각할 시간도 관계 안에서 조율해볼 수 있다.|quiet,boundary
팀의 다음 단계를 설계할 때 동료가 중요하게 보는 조건도 물어보자.|plan,feeling
개념 사이의 원리를 이해한 뒤 실제 예제로 확인하는 공부를 시도해보자.|imagine,step
계속 개선할 일을 찾는 주말이라면 목표 없는 조용한 시간도 남겨보자.|quiet,flexible
오래 쓸 방법을 고르려다 작은 실험까지 미뤄지는지 살펴보자.|criteria,try
완성된 계획만 공유하기보다 현재의 가설을 한 사람에게 설명해보자.|share,sample
''',
    'INTP': '''
사물의 작동 원리와 논리적인 설명을 탐구하는 모습으로 알려져 있다.|reason,imagine
당연하게 받아들인 전제에 다른 질문을 붙이는 장면이 어울린다.|idea,criteria
궁금한 자료를 계속 찾다가 정작 첫 결과를 남기지 못하는 날이 있다.|priority,try
머릿속 추론을 다 설명하기 어렵다면 구체적인 예시 하나부터 꺼내보자.|facts,reason
말수가 적은 날에도 관심 있는 이야기는 짧은 메시지로 나눌 수 있다.|hello,small
다른 해결책을 검토할 때 팀이 정해야 할 시점을 함께 합의해보자.|imagine,plan
이론을 읽고 작은 실험으로 반례를 찾아보는 공부를 상상해볼 수 있다.|sample,facts
혼자 탐색하는 시간이 즐거워도 잠깐 멈출 시간을 정해볼 수 있다.|quiet,buffer
모든 가능성을 비교하려면 오늘 필요한 기준 두 개만 남겨보자.|criteria,flexible
완벽한 설명을 기다리기보다 작동하는 작은 예제를 먼저 만들어보자.|step,try
''',
    'ENTJ': '''
목표를 정하고 사람과 자원을 조직하는 모습으로 자주 소개된다.|priority,plan
방향이 흐릿한 모임에서 다음 행동을 정리하는 상황을 떠올려볼 수 있다.|reason,step
진행 속도를 높이다 동료의 준비 시간을 놓치는 순간을 살펴보자.|buffer,feeling
요청을 전할 때 원하는 결과와 가능한 범위를 함께 말해보자.|reason,boundary
좋은 해결책을 주기 전에 상대가 듣고 싶은 말인지 물어보자.|feeling,kind
역할을 나눌 때 각자의 선택권과 수정 가능한 일정도 남겨보자.|plan,flexible
배운 내용을 실제 프로젝트 목표에 연결하는 연습을 해볼 수 있다.|meaning,sample
휴식을 다음 성과의 도구로만 보지 않고 편한 사람과 가볍게 만나보자.|invite,buffer
효율이 비슷한 두 선택이라면 내가 원하는 경험도 기준에 넣어보자.|criteria,meaning
혼자 모든 결정을 맡기보다 작은 결정 하나를 동료에게 부탁해보자.|boundary,share
''',
    'ENTP': '''
새로운 관점과 논쟁을 즐기는 아이디어형으로 흔히 설명된다.|idea,share
기존 방식에 대안을 제시하며 대화의 선택지를 넓히는 장면이 어울린다.|imagine,reason
재미있는 토론이어도 상대에게는 반박이 길게 느껴질 수 있다.|feeling,pause
다른 의견을 내기 전에 상대의 핵심을 한 문장으로 확인해보자.|facts,feeling
즉흥적인 만남을 제안할 때 거절해도 괜찮다는 여지를 남겨보자.|invite,kind
새 기능을 늘리기 전에 이번 주에 끝낼 범위를 함께 정해보자.|priority,boundary
낯선 주제를 비교하고 연결하는 공부 뒤에는 짧은 결과를 남겨보자.|imagine,record
새 자극을 계속 찾는 주말에는 비워두는 시간도 실험해볼 수 있다.|buffer,sample
흥미로운 후보가 많다면 하나만 짧게 체험하고 비교해보자.|sample,criteria
새 제안을 꺼낸 뒤 실행할 첫 단계와 확인할 날짜를 붙여보자.|step,plan
''',
    'INFJ': '''
사람과 사건의 의미를 깊게 살피는 모습으로 자주 소개된다.|meaning,quiet
겉으로 드러난 말과 그 뒤의 바람을 함께 생각하는 장면을 떠올려보자.|feeling,imagine
상대의 마음을 짐작하는 것과 실제로 들은 말을 구분해볼 필요가 있다.|facts,feeling
오래 생각한 이야기를 꺼낼 때 지금 필요한 부탁부터 짧게 전해보자.|pause,boundary
깊은 대화를 좋아해도 모든 관계를 같은 깊이로 유지할 필요는 없다.|small,quiet
팀이 추구하는 가치에 공감하면서 내 역할의 한계도 말해보자.|meaning,boundary
공부의 이유를 찾았다면 오늘 읽을 분량을 구체적으로 나눠보자.|meaning,step
다른 사람 이야기를 많이 들은 날에는 조용한 회복 시간을 남겨보자.|quiet,buffer
이상적인 답을 기다리다가 내 선택이 멈춰 있는지 돌아보자.|criteria,try
배려를 받는 연습으로 편한 사람에게 작은 도움 하나를 요청해보자.|selfkind,share
''',
    'INFP': '''
개인의 가치와 진정성을 중요하게 여기는 모습으로 널리 소개된다.|meaning,selfkind
작은 경험을 이야기와 상상으로 확장하는 장면을 떠올려볼 수 있다.|imagine,record
내가 바라는 모습과 실제 하루의 차이가 커 보여 실망하는 날이 있다.|selfkind,facts
감정을 정확하게 표현하기 어렵다면 필요한 시간을 먼저 요청해보자.|pause,feeling
친한 사람에게 맞춰주다 내 바람을 놓치지 않았는지 살펴보자.|feeling,boundary
내가 동의하는 방향이라도 맡을 일은 작고 분명하게 정해보자.|meaning,step
흥미로운 주제를 스스로 고르되 오늘의 짧은 마감도 만들어보자.|idea,priority
남들이 좋다는 취미보다 실제로 편안했던 장면을 적어보자.|record,quiet
옳아 보이는 선택과 내가 지속할 수 있는 선택을 함께 비교해보자.|criteria,selfkind
머릿속 이야기를 완성하려 하기보다 첫 문장 하나만 남겨보자.|try,record
''',
    'ENFJ': '''
사람의 성장을 응원하고 공동의 방향을 이끄는 모습으로 소개된다.|share,meaning
서로 다른 의견 사이에서 참여할 자리를 만드는 장면을 떠올려보자.|invite,feeling
모두를 격려하다 내 일정과 피로를 뒤늦게 알아차릴 수 있다.|buffer,boundary
도움을 주고 싶을 때 상대가 원하는 도움부터 구체적으로 물어보자.|feeling,facts
가까운 사람이 힘들어해도 모든 해결을 내가 맡을 필요는 없다.|kind,boundary
팀의 분위기를 챙기는 일도 역할로 나누어 부탁해볼 수 있다.|share,step
배운 것을 설명하는 모임에서 내 이해도 함께 확인해보자.|share,facts
사람을 만나는 휴식과 혼자 쉬는 휴식 중 오늘 필요한 것을 골라보자.|invite,quiet
주변 기대를 만족시키는 기준 외에 내 바람도 한 가지 넣어보자.|criteria,meaning
다른 사람을 칭찬하듯 오늘 내가 해낸 일도 한 줄 기록해보자.|record,selfkind
''',
    'ENFP': '''
새로운 가능성과 사람 사이의 연결을 반기는 모습으로 흔히 소개된다.|idea,invite
한 사람의 이야기를 다른 관심사와 연결해 대화를 넓히는 장면이 어울린다.|share,imagine
하고 싶은 일을 많이 약속해 시작한 일을 끝내기 어려운 날이 있다.|priority,boundary
생각을 말하며 정리할 때 상대가 듣기 편한 핵심부터 골라보자.|share,reason
새 친구를 만나는 설렘과 오래된 관계를 챙기는 시간을 함께 남겨보자.|hello,plan
회의에서 나온 여러 제안 중 이번 주에 실험할 하나를 골라보자.|idea,try
흥미로운 공부라도 한 번에 다 배우기보다 짧은 체험부터 시작해보자.|sample,step
즐거운 약속이 이어진 뒤에는 비어 있는 저녁도 일정에 넣어보자.|buffer,quiet
지금 끌리는 경험과 실제로 쓸 수 있는 시간을 함께 비교해보자.|meaning,criteria
새 아이디어 하나에 오늘 할 행동과 끝낼 시점을 붙여보자.|step,priority
''',
    'ISTJ': '''
사실과 책임을 바탕으로 꾸준히 일을 처리하는 모습으로 소개된다.|facts,plan
약속한 절차를 지키고 빠진 부분을 확인하는 장면을 떠올려볼 수 있다.|record,step
익숙한 순서가 바뀌면 실제 위험보다 불편함이 먼저 느껴질 수 있다.|facts,buffer
정확하게 전달하려는 말에 상대의 상황을 묻는 한마디도 붙여보자.|reason,feeling
말로 표현하지 않아도 챙기고 있다면 고마운 마음을 짧게 전해보자.|hello,kind
맡은 일을 지키면서 추가 요청을 받을 범위도 미리 정해보자.|boundary,priority
예제와 반복 연습을 활용하되 배운 원리를 다른 문제에도 써보자.|step,imagine
할 일을 끝내야 쉰다는 기준에 쉴 시간도 함께 적어보자.|plan,buffer
검증된 방법과 새로운 방법을 작은 규모로 비교해볼 수 있다.|criteria,sample
변경할 수 없는 조건과 바꿔도 되는 순서를 구분해보자.|facts,flexible
''',
    'ISFJ': '''
주변 사람을 세심하게 챙기며 책임을 지키는 모습으로 알려져 있다.|feeling,record
상대가 전에 말한 작은 취향을 기억해 배려하는 장면이 어울린다.|facts,kind
부탁을 계속 받아주다가 내 시간이 사라지는 순간을 살펴보자.|boundary,buffer
서운함이 쌓이기 전에 내가 원하는 도움을 구체적으로 말해보자.|feeling,step
돌봄을 주고받는 관계에서 내 부탁도 같은 무게로 꺼내보자.|selfkind,share
팀의 보이지 않는 준비를 목록으로 남기고 역할을 나눠보자.|record,plan
익숙한 설명과 실제 예시를 연결해 한 단계씩 공부해볼 수 있다.|facts,step
다른 사람의 편안함만큼 내가 조용히 쉬는 시간도 확보해보자.|quiet,selfkind
남이 실망할까 걱정될 때 내 일정과 가능한 대안을 함께 말해보자.|kind,boundary
당연하게 해온 수고를 오늘 하나만 이름 붙여 기록해보자.|record,selfkind
''',
    'ESTJ': '''
명확한 기준과 실행 순서로 일을 정리하는 모습으로 자주 소개된다.|reason,plan
누가 무엇을 언제 할지 정해 모임의 진행을 돕는 장면이 어울린다.|priority,step
모두에게 같은 방법이 효율적인지 확인하지 못하는 날이 있다.|feeling,imagine
지시를 전할 때 이유와 질문할 시간을 함께 남겨보자.|reason,buffer
약속을 지키는 방식이 다른 친구와 가능한 기준부터 합의해보자.|boundary,feeling
진행 상황을 확인하면서 잘된 점도 구체적으로 나눠보자.|facts,share
배운 도구를 작은 실제 과제에 적용해 결과를 확인해보자.|sample,record
비어 있는 시간을 채울 일부터 찾는다면 휴식 약속도 정해보자.|plan,quiet
정해진 규칙과 현재 상황이 다를 때 예외의 조건을 적어보자.|criteria,flexible
직접 처리하는 편이 빨라도 작은 역할 하나는 나눠 맡겨보자.|step,boundary
''',
    'ESFJ': '''
함께하는 분위기와 사람 사이의 조화를 챙기는 모습으로 소개된다.|invite,feeling
모임에서 소외된 사람을 알아보고 말을 건네는 장면이 어울린다.|hello,small
반응이 적다고 내가 부족했다는 결론까지 서두르지 않아도 된다.|facts,selfkind
상대의 기분을 살핀 뒤 내 바람도 같은 문장 안에 담아보자.|feeling,boundary
정기적인 연락을 좋아해도 서로 편한 연락 빈도를 먼저 물어보자.|plan,feeling
팀을 챙기는 수고를 혼자 맡기보다 준비 일을 목록으로 나눠보자.|step,share
함께 복습하는 자리에서 이해가 안 된 부분을 질문해보자.|invite,facts
사람을 만나는 주말에도 아무 부탁 없는 시간을 남겨보자.|buffer,quiet
모두가 좋아할 답을 찾을 때 내가 원하는 조건도 하나 적어보자.|criteria,meaning
고마움을 기다리느라 지친 날에는 내 수고를 스스로 기록해보자.|record,selfkind
''',
    'ISTP': '''
상황을 관찰하고 손으로 시험하며 문제를 푸는 모습으로 소개된다.|facts,sample
설명이 길어질 때 직접 작동하는 부분을 확인하는 장면이 어울린다.|try,reason
혼자 해결하려다 필요한 정보를 동료와 나누지 못하는 날이 있다.|share,boundary
짧고 정확한 말 뒤에 내가 협조할 수 있는 범위도 덧붙여보자.|reason,kind
함께 무언가를 하는 시간이 편해도 상대의 마음을 직접 물어보자.|small,feeling
급한 문제를 고친 뒤 원인과 다음 확인 절차를 기록해보자.|record,plan
작은 도구를 직접 써보고 관찰한 결과를 비교하는 공부를 시도해보자.|sample,facts
혼자 몰입하는 취미에서도 멈출 시점을 가볍게 정해보자.|quiet,buffer
당장 작동하는 해결책과 나중에 손볼 부분을 나눠 선택해보자.|criteria,flexible
완성한 뒤에만 알리기보다 진행 상황을 한 줄씩 공유해보자.|record,share
''',
    'ISFP': '''
자기만의 감각과 가치를 일상에서 표현하는 모습으로 흔히 소개된다.|meaning,record
색과 소리처럼 구체적인 경험에서 좋아하는 것을 발견하는 장면이 어울린다.|facts,sample
갈등을 피하려고 침묵하다 내 취향까지 감추는 날이 있다.|feeling,boundary
정답 같은 설명보다 지금 어떤 점이 편하고 불편한지 말해보자.|facts,feeling
함께 있는 즐거움과 혼자 보내는 시간을 부드럽게 조율해보자.|quiet,kind
내 방식으로 작업할 여지를 요청하면서 전달할 날짜도 정해보자.|boundary,plan
설명을 오래 읽기보다 작은 결과물을 만들며 배워볼 수 있다.|sample,try
성과를 남기지 않아도 좋아하는 감각을 느끼는 산책을 해보자.|record,selfkind
남들이 좋아하는 선택보다 실제로 써본 느낌을 기준에 넣어보자.|criteria,facts
마음에 드는 장면 하나를 사진이나 짧은 문장으로 남겨보자.|record,step
''',
    'ESTP': '''
지금의 상황을 읽고 빠르게 행동하는 모습으로 자주 소개된다.|facts,try
현장에서 예상 밖의 문제에 대안을 찾는 장면을 떠올려볼 수 있다.|flexible,reason
일단 해보자는 속도에 필요한 확인까지 생략되지는 않는지 살펴보자.|facts,pause
곧바로 해결책을 내기 전에 상대의 설명을 끝까지 들어보자.|feeling,pause
재미있는 제안을 할 때 친구가 편하게 거절할 여지도 남겨보자.|invite,kind
실행으로 배운 것을 팀에 전하고 다음 약속은 짧게 기록해보자.|share,record
작은 실습을 먼저 한 뒤 왜 그렇게 됐는지 설명을 붙여보자.|sample,reason
활동적인 휴식이 좋더라도 다음 날 쉴 여유도 남겨보자.|buffer,plan
당장의 재미와 이미 한 약속을 함께 살펴 선택해보자.|criteria,facts
새 시도 전에 끝낼 조건과 확인할 기준을 하나씩 정해보자.|boundary,priority
''',
    'ESFP': '''
사람들과 현재의 경험을 즐기는 모습으로 널리 소개된다.|invite,share
일상의 작은 즐거움을 함께 나누며 분위기를 밝히는 장면이 어울린다.|hello,record
즐거운 요청을 거절하기 어려워 일정이 과해지는 날이 있다.|boundary,buffer
분위기를 살리는 말과 함께 내 상태도 솔직하게 전해보자.|feeling,kind
당장 만날 수 없을 때는 짧은 안부로도 관심을 나눌 수 있다.|hello,small
함께 움직이는 힘을 살리면서 맡은 일의 마지막 단계도 확인해보자.|step,record
사람과 함께 실습하는 시간을 짧게 잡고 한 가지를 익혀보자.|invite,sample
재미있는 계획 사이에 아무 일정 없는 저녁도 남겨보자.|buffer,quiet
지금 끌리는 경험을 고를 때 시간과 약속의 범위도 확인해보자.|criteria,boundary
큰 이벤트가 없는 날에도 좋았던 순간 하나를 기록해보자.|record,selfkind
''',
}

ZODIAC_PROFILES = {
    'aries': '''
대중 점성술에서 양자리는 불 원소와 활동궁의 시작하는 이미지로 다뤄진다.|idea,try
망설이는 모임에서 먼저 제안하는 용기를 떠올려볼 수 있다.|invite,share
빨리 시작하고 싶을수록 이미 한 약속과 준비물을 확인해보자.|facts,plan
직접적인 표현을 쓰더라도 상대의 기분을 묻는 여유를 남겨보자.|reason,feeling
새로운 만남을 이끌 때 상대의 속도에 맞춘 짧은 초대도 가능하다.|invite,small
아이디어를 제안한 사람이 모든 일을 맡지 않도록 역할을 나눠보자.|step,boundary
처음 해보는 실습에 도전하고 결과를 간단히 남겨보자.|sample,record
활동적인 주말 다음에는 쉬는 시간을 먼저 확보해보자.|buffer,quiet
흥미로운 선택을 바로 확정하기 전에 작은 체험부터 해보자.|sample,pause
시작한 일 하나를 끝내는 행동까지 오늘의 목표에 넣어보자.|priority,step
''',
    'taurus': '''
대중 점성술에서 황소자리는 흙 원소와 고정궁의 안정적인 이미지로 다뤄진다.|facts,plan
익숙한 일상을 꾸준히 가꾸는 장면을 떠올려볼 수 있다.|record,step
편한 방법을 지키고 싶을 때 바꿔도 되는 작은 부분을 찾아보자.|flexible,sample
천천히 생각하고 싶다면 답할 시점을 미리 말해보자.|pause,plan
말없이 챙기는 관심도 고마운 마음 한 줄로 표현해보자.|hello,kind
정해진 역할을 지키되 추가 부탁을 모두 떠맡지는 않아도 된다.|boundary,priority
반복 연습에 새로운 예제 하나를 섞어 공부해보자.|step,sample
좋아하는 음식과 음악처럼 구체적으로 편안했던 경험을 돌아보자.|facts,record
익숙함과 현재 필요를 각각 기준으로 적어 비교해보자.|criteria,facts
작은 변경 하나를 짧게 시험하고 내 느낌을 확인해보자.|sample,flexible
''',
    'gemini': '''
대중 점성술에서 쌍둥이자리는 공기 원소와 변통궁의 호기심으로 설명된다.|idea,share
서로 다른 화제를 연결해 대화를 넓히는 장면을 떠올려볼 수 있다.|imagine,hello
관심사가 빠르게 늘어날 때 끝낼 일 하나를 따로 골라보자.|priority,step
말이 많아지는 자리에서는 상대가 꺼낸 질문도 다시 확인해보자.|facts,feeling
가벼운 안부를 자주 나누더라도 상대가 편한 빈도를 물어보자.|hello,boundary
회의에서 나온 아이디어를 두세 개로 추리고 담당을 정해보자.|criteria,plan
짧은 자료를 비교해 읽은 뒤 공통점 하나를 기록해보자.|imagine,record
새 소식을 계속 확인하는 날에는 알림 없는 시간도 남겨보자.|quiet,buffer
새로운 후보를 찾는 시간과 하나를 고르는 시간을 나눠보자.|criteria,pause
관심을 말로 나눈 뒤 작은 실행 하나를 붙여보자.|share,try
''',
    'cancer': '''
대중 점성술에서 게자리는 물 원소와 활동궁의 돌봄 이미지로 다뤄진다.|feeling,quiet
익숙한 공간에서 서로 편안해질 준비를 하는 장면을 떠올려보자.|plan,kind
상대의 무심한 반응을 내 잘못으로 해석하기 전에 사실을 확인해보자.|facts,selfkind
서운한 마음을 알아주길 기다리기보다 필요한 말을 짧게 꺼내보자.|feeling,boundary
가까운 관계를 챙기는 만큼 나만의 시간도 부탁해볼 수 있다.|quiet,kind
모임을 준비할 때 보이지 않는 돌봄도 역할로 나눠보자.|step,share
편안한 장소를 정하고 오늘 배울 작은 분량부터 시작해보자.|plan,step
추억을 돌아보는 휴식과 지금의 편안함을 함께 살펴보자.|record,meaning
가족의 기대와 내가 원하는 경험을 나란히 적어보자.|criteria,meaning
다른 사람에게 주던 다정한 말을 나에게도 건네보자.|selfkind,record
''',
    'leo': '''
대중 점성술에서 사자자리는 불 원소와 고정궁의 표현력으로 설명된다.|share,invite
내가 좋아하는 것을 자신 있게 보여주는 장면을 떠올려볼 수 있다.|try,record
반응이 적은 날에도 내 시도의 가치를 전부 지우지 않아도 된다.|facts,selfkind
이야기의 중심에 섰다면 다른 사람의 경험을 묻는 차례도 만들어보자.|feeling,share
큰 이벤트 대신 작은 응원 한마디로 관심을 전해볼 수 있다.|hello,kind
함께 만든 성과를 소개할 때 동료가 기여한 부분도 기록해보자.|record,share
배운 것을 짧게 발표하되 모르는 부분은 질문해보자.|share,facts
즐거움을 만드는 역할을 잠깐 내려놓고 조용히 쉬어보자.|quiet,buffer
멋져 보이는 선택과 실제로 즐길 수 있는 선택을 비교해보자.|criteria,meaning
잘한 모습을 보여주려 하기보다 미완성 결과 하나를 나눠보자.|sample,selfkind
''',
    'virgo': '''
대중 점성술에서 처녀자리는 흙 원소와 변통궁의 세심함으로 설명된다.|facts,step
작은 오류를 발견해 생활을 편하게 만드는 장면을 떠올려볼 수 있다.|record,reason
고칠 부분을 찾다가 이미 충분한 결과까지 미루고 있는지 살펴보자.|priority,try
도움이 되는 지적도 잘된 점과 함께 구체적으로 전해보자.|facts,kind
친구를 돕기 전에 지금 원하는 도움이 무엇인지 물어보자.|feeling,boundary
검토 항목을 정해두고 모든 일을 혼자 확인하지 않도록 나눠보자.|plan,step
실수 기록을 남기되 다음에 바꿀 한 가지만 골라보자.|record,priority
쉬는 시간을 더 잘 쉬기 위한 과제로 만들지 않아도 된다.|quiet,selfkind
완벽한 후보 대신 오늘의 필수 조건을 만족하는지 확인해보자.|criteria,flexible
초안을 보여줄 시간을 정하고 작은 피드백을 받아보자.|plan,share
''',
    'libra': '''
대중 점성술에서 천칭자리는 공기 원소와 활동궁의 균형 이미지로 다뤄진다.|feeling,criteria
서로 다른 입장을 듣고 대화할 접점을 찾는 장면을 떠올려보자.|share,reason
모두가 만족할 답을 기다리다 내 바람이 빠지는지 살펴보자.|meaning,boundary
반대 의견을 말할 때도 고마운 점과 내 조건을 함께 전해보자.|kind,reason
관계를 유지하려는 노력에 서로 가능한 약속인지도 확인해보자.|feeling,plan
중재 역할을 맡았다면 최종 결정을 누가 언제 할지 정해보자.|plan,boundary
다른 관점을 비교한 뒤 내 말로 한 줄 정리해보자.|imagine,record
함께 쉬는 시간과 혼자 조용히 보내는 시간을 나눠보자.|small,quiet
후보마다 장단점을 적고 오늘 중요한 기준 두 개만 남겨보자.|criteria,priority
작은 선택 하나는 내 취향으로 정한 뒤 느낌을 살펴보자.|try,meaning
''',
    'scorpio': '''
대중 점성술에서 전갈자리는 물 원소와 고정궁의 깊이로 설명된다.|quiet,meaning
관심 있는 문제나 관계를 오래 집중해 살피는 장면을 떠올려보자.|facts,priority
확인하지 않은 의도를 계속 추측하고 있지는 않은지 살펴보자.|facts,pause
바로 속마음을 꺼내기 어렵다면 이야기할 시간을 먼저 정해보자.|pause,plan
가까운 사이에도 각자 혼자 있을 여유와 사생활을 조율해보자.|quiet,boundary
중요한 일을 깊게 맡더라도 진행 상황은 짧게 나눠보자.|record,share
한 주제를 탐구한 뒤 관찰한 사실과 내 해석을 나눠 적어보자.|facts,reason
생각이 같은 자리에서 맴돈다면 공간을 바꿔 가볍게 걸어보자.|sample,flexible
강하게 끌리는 답일수록 다른 설명도 하나 떠올려보자.|imagine,criteria
도움을 청하는 것도 관계에 참여하는 방식으로 시도해보자.|share,selfkind
''',
    'sagittarius': '''
대중 점성술에서 사수자리는 불 원소와 변통궁의 탐험 이미지로 다뤄진다.|idea,flexible
낯선 경험에서 새로운 관점을 찾는 장면을 떠올려볼 수 있다.|imagine,sample
새 계획을 늘리기 전에 지금 지킬 수 있는 약속부터 확인해보자.|facts,boundary
솔직한 의견도 상대가 받아들일 수 있는 말로 다듬어 전해보자.|reason,kind
함께 모험을 제안할 때 서로 원하는 속도와 범위를 물어보자.|invite,feeling
큰 방향을 제안한 뒤 실행할 첫 단계와 담당을 붙여보자.|step,plan
새로운 주제를 체험하고 무엇이 달라 보였는지 기록해보자.|sample,record
멀리 떠나지 않아도 가까운 동네의 다른 길을 걸어볼 수 있다.|idea,try
자유로운 선택을 위해 꼭 정해야 할 조건도 두 개 적어보자.|criteria,plan
하고 싶은 일 하나를 오늘 가능한 크기로 줄여보자.|priority,step
''',
    'capricorn': '''
대중 점성술에서 염소자리는 흙 원소와 활동궁의 꾸준한 목표로 설명된다.|plan,priority
큰 일을 작은 단계로 나눠 오래 이어가는 장면을 떠올려볼 수 있다.|step,record
성과가 쉬는 자격이 되어버리지는 않았는지 살펴보자.|selfkind,buffer
진지한 계획을 말할 때 지금의 마음도 한 문장 보태보자.|reason,feeling
책임감으로 챙긴 일에도 상대에게 도움을 부탁할 수 있다.|boundary,share
팀의 목표와 실제 가능한 시간 사이에 여유를 남겨보자.|plan,buffer
정기적인 연습 뒤에 달라진 점을 구체적으로 기록해보자.|step,record
계획표에 비어 있는 칸을 미완성으로 여기지 않고 남겨보자.|quiet,flexible
오래 갈 선택인지 볼 때 내게 의미 있는지도 물어보자.|criteria,meaning
큰 성과를 기다리지 말고 오늘 한 일을 하나 인정해보자.|record,selfkind
''',
    'aquarius': '''
대중 점성술에서 물병자리는 공기 원소와 고정궁의 독창성으로 설명된다.|idea,reason
익숙한 규칙을 다른 관점으로 다시 보는 장면을 떠올려볼 수 있다.|imagine,criteria
새로운 방식에 집중하다 함께하는 사람의 부담을 놓칠 수 있다.|feeling,facts
큰 개념을 이야기할 때 일상적인 예시 하나를 곁들여보자.|reason,facts
독립적인 시간이 필요하다면 관계 안에서 가능한 연락 방식을 말해보자.|quiet,boundary
모두를 위한 개선안을 내더라도 동료의 구체적인 요구부터 확인해보자.|share,feeling
서로 다른 분야를 연결한 아이디어를 작은 실험으로 만들어보자.|idea,sample
새 정보를 계속 탐색한 날에는 화면 없는 시간도 마련해보자.|quiet,buffer
새롭다는 이유 외에 실제 도움이 되는 조건도 비교해보자.|criteria,facts
독창적인 생각을 한 사람에게 먼저 보여주고 반응을 들어보자.|share,try
''',
    'pisces': '''
대중 점성술에서 물고기자리는 물 원소와 변통궁의 상상력으로 설명된다.|imagine,feeling
감정이나 이미지를 이야기로 표현하는 장면을 떠올려볼 수 있다.|record,meaning
다른 사람의 기분을 챙기다 내 바람까지 흐려지는지 살펴보자.|selfkind,boundary
막연한 느낌을 전할 때 실제 있었던 장면 하나도 함께 말해보자.|facts,feeling
공감하는 마음과 지금 해줄 수 있는 도움의 범위를 나눠보자.|kind,boundary
자유롭게 떠오른 생각에 전달할 결과와 날짜를 작게 붙여보자.|step,plan
상상한 내용을 작은 그림이나 예제로 만들어 확인해보자.|sample,try
좋아하는 음악을 듣고 편안했던 순간을 한 줄 남겨보자.|quiet,record
누구에게나 좋은 선택보다 내가 원하는 경험을 먼저 적어보자.|meaning,criteria
생각 속에 있던 한 가지를 오늘 가능한 행동으로 바꿔보자.|step,priority
''',
}


def interpretation_cards():
    from .astrology import SIGNS
    from .scenarios import SUGGESTIONS
    tips = {key: (trait, text) for key, trait, text in SUGGESTIONS}
    names = {key: name for key, name, _ in SIGNS}
    rows = []
    for kind, profiles in [('mbti', MBTI_PROFILES), ('zodiac', ZODIAC_PROFILES)]:
        for subject, content in profiles.items():
            lines = content.strip().splitlines()
            if len(lines) != len(FACETS):
                raise ValueError(f'{subject}: expected ten facets')
            for index, (facet, line) in enumerate(zip(FACETS, lines), 1):
                text, keys = line.split('|')
                keys = keys.split(',')
                name = subject if kind == 'mbti' else names[subject]
                url = (f'https://www.16personalities.com/{subject.lower()}-personality'
                       if kind == 'mbti' else f'https://www.astrology.com/zodiac-signs/{subject}')
                # Only the first three facets summarize the public profile.
                # The remaining facets are our fictional applications, not source claims.
                note = ('공개 해설의 핵심을 짧게 재서술한 학습용 해설.' if index <= 3
                        else '공개 해설의 주제에서 착안해 직접 쓴 일상 적용 예시.')
                rows.append({
                    'id': f'{kind}-{subject.lower()}-{index:02}',
                    'title': f'{name} · {facet}', 'text': f'{name}: {text} {note}',
                    'category': f'{"MBTI" if kind == "mbti" else "별자리"} · {facet}',
                    'traits': sorted({tips[key][0] for key in keys}), 'tips': keys,
                    'kind': 'interpretation', 'subject_kind': kind, 'subject': subject,
                    'facet': facet, 'document_id': f'profile-{kind}-{subject.lower()}',
                    'document_title': f'{name} 해설과 일상 적용',
                    'source': ('16Personalities 공개 유형 소개(NERIS 모델, 공식 MBTI와 다름)' if kind == 'mbti'
                               else 'Astrology.com 공개 별자리 소개(대중 점성술)') + ' 참고 · 한국어 재서술 및 직접 작성 예시',
                    'source_url': url, 'reviewed_on': REVIEWED_ON,
                    'editorial_note': note,
                })
    return rows

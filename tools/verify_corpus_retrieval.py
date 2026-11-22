"""Small Korean retrieval smoke check using actual native query embeddings.

Not a relevance benchmark: reports topical hits within the top three, including
all retrieved titles, so the result can be inspected rather than inferred.
"""
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from mbti_lab.embedding import LiteRTEmbeddings

CHECKS = [
    ('읽었는데 답을 안 해줘서 신경 쓰여', ['답장', '메시지', '연락', '읽음'], ''),
    ('계속 계획만 하고 프로젝트를 시작하지 못해', ['프로젝트', '시작', '초안'], ''),
    ('갑자기 여행을 가자는데 일정이 없어 부담스러워', ['여행'], ''),
    ('조용히 혼자 쉬고 싶은 주말이야', ['휴식', '조용', '혼자', '주말', '쉼'], ''),
    ('부탁을 거절 못 해서 내 일이 자꾸 밀려', ['부탁', '거절', '역할', '경계'], ''),
    ('발표를 완벽하게 준비하려다 시작이 늦어져', ['발표', '초안', '준비'], ''),
    ('INTJ는 어떤 성향이야?', [], 'INTJ'),
    ('ENFP는 어떤 성향이야?', [], 'ENFP'),
    ('황소자리의 성향은 어때?', [], 'taurus'),
    ('물병자리의 성향은 어때?', [], 'aquarius'),
]


def cosine(a, b):
    return sum(x*y for x, y in zip(a, b)) / math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))


def main():
    data = json.loads((ROOT / 'frontend/public/data/graph.json').read_text(encoding='utf-8'))
    embedder = LiteRTEmbeddings()
    checks = []
    try:
        assert data['model']['sha256'] == embedder.fingerprint
        for query, topics, subject in CHECKS:
            vector = embedder.embed_query(query)
            nearest = sorted(data['chunks'], key=lambda c: (-cosine(vector, c['embedding']), c['id']))[:3]
            passed = any(c.get('subject') == subject for c in nearest) if subject else any(
                word in c['title'] + c['category'] for c in nearest for word in topics)
            checks.append({'query': query, 'passed': passed, 'expected_subject': subject,
                           'expected_topics': topics, 'top3': [
                               {'id': c['id'], 'title': c['title'], 'cosine': round(cosine(vector, c['embedding']), 5)}
                               for c in nearest]})
        report = {'reviewed_on': '2026-11-22', 'cards': len(data['chunks']),
                  'model_sha256': embedder.fingerprint,
                  'criterion': 'At least one topical/subject match within top 3; exploratory smoke check, not accuracy measurement',
                  'passed': sum(c['passed'] for c in checks), 'checks': checks}
        (ROOT / 'docs/CORPUS_RETRIEVAL_CHECKS.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'Korean retrieval checks: {report["passed"]}/{len(checks)}; see docs/CORPUS_RETRIEVAL_CHECKS.json')
        if not all(c['passed'] for c in checks):
            raise SystemExit('Review failed retrieval checks before publishing')
    finally:
        embedder.close()


if __name__ == '__main__':
    main()

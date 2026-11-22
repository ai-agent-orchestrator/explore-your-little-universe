"""Exercise the shareable import on fresh temporary labels, then roll back."""
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ohgi_graph import get_driver, database

ROOT = Path(__file__).resolve().parent.parent


def main():
    query = (ROOT / 'cypher/lumi_graph_only_seed.cypher').read_text(encoding='utf-8')
    data = json.loads((ROOT / 'frontend/public/data/graph.json').read_text(encoding='utf-8'))
    labels = ['SharedTrait','MbtiTrait','MbtiType','ZodiacSign','RagDocument','RagChunk','RagTip']
    for label in labels:
        query = query.replace(':' + label, ':LumiImportCheck' + label)
    with get_driver() as driver, driver.session(database=database()) as session:
        tx = session.begin_transaction()
        try:
            for iteration in range(2):
                tx.run(query).consume()
                for label, expected in [('SharedTrait',8),('MbtiType',16),('ZodiacSign',12),
                                         ('RagDocument',len({c['document_id'] for c in data['chunks']})),
                                         ('RagChunk',len(data['chunks'])),('RagTip',len(data['suggestions']))]:
                    count = tx.run(f'MATCH (n:LumiImportCheck{label}) RETURN count(n) AS n').single()['n']
                    assert count == expected, (label,count,expected)
                links = tx.run('MATCH ()-[r:DESCRIBED_BY]->(c:LumiImportCheckRagChunk) RETURN count(r) AS n').single()['n']
                assert links == 280, links
            print('PASS: fresh graph import, all node counts and idempotent re-run; rolled back')
        finally:
            tx.rollback()


if __name__ == '__main__':
    main()

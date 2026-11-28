"""Seed a fictional 12-sign/MBTI crossover for graph learning; no predictions."""
import os
from pathlib import Path
from lumi_core.catalog.zodiac import SIGNS
from lumi_core.graph.seeds import ZODIAC_SEED as SEED, MBTI_SEED, trait_rows, sign_rows
from lumi_core.graph.client import get_driver, database as configured_database

# Deliberately authored toy mappings, not empirical personality claims.





def main():
    database = configured_database()
    mbti_rows, rows = trait_rows(), sign_rows()
    with get_driver() as driver:
        def seed(tx):
            tx.run(MBTI_SEED, rows=mbti_rows).consume()
            tx.run(SEED, rows=rows).consume()
        with driver.session(database=database) as session:
            session.execute_write(seed)
        records, _, _ = driver.execute_query('''
            MATCH (z:ZodiacSign)-[:HAS_TRAIT]->(t:SharedTrait)
            WHERE z.id IN $ids
            RETURN count(DISTINCT z) AS signs, count(*) AS links,
                   count(DISTINCT t) AS shared_traits
            ''', ids=[s[0] for s in SIGNS], database_=database)
        counts = records[0].data()
        assert counts == {'signs': 12, 'links': 24, 'shared_traits': 8}, counts
        print(f'PASS {database}: {counts}')
        # Sequential re-runs should retain exactly these relationships.
        records, _, _ = driver.execute_query('''
            MATCH (m:MbtiType {code:'INTJ'})-[:HAS_TRAIT]->(t:SharedTrait)
                  <-[:HAS_TRAIT]-(z:ZodiacSign)
            RETURN z.name AS sign, collect(t.title) AS common_traits
            ORDER BY sign
            ''', database_=database)
        for record in records:
            print(record.data())


if __name__ == '__main__':
    main()

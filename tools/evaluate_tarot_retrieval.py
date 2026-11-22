"""Measure fixed retrieval coverage, never LLM accuracy or prediction quality."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lumi_core.embedding.litert import LiteRTEmbeddings
from lumi_core.settings import ROOT,chroma_path
from lumi_core.graph.client import get_driver,database
from tarot_lab.repositories.chroma import ChromaRepository
from tarot_lab.repositories.neo4j import Neo4jRepository
from tarot_lab.fixtures.evaluation import evaluation_cases

def main():
    embedder=LiteRTEmbeddings();vector=None
    try:
        vector=ChromaRepository(chroma_path(),embedder.profile);results=[]
        with get_driver() as driver:
            graph=Neo4jRepository(driver,database())
            for case in evaluation_cases():
                ids=[d['card_id']+':'+d['orientation'] for d in case['draws']]
                paths=graph.meaning_paths(ids,case['mbti'],case['zodiac_id'])
                keywords=graph.meaning_keywords(ids)
                plain=embedder.embed_query(case['question'])
                expanded=embedder.embed_query(case['question']+'\n'+' '.join(keywords))
                found=vector.search_pair(plain,expanded,case['draws'])
                coverage={};wrong=0
                for variant,result in found.items():
                    coverage[variant]=sum(bool(group['chunks']) for group in result['draws'])
                    for group in result['draws']:
                        wrong+=sum(c['orientation']!=group['draw']['orientation'] or c['card_id']!=group['draw']['card_id'] for c in group['chunks'])
                results.append({'id':case['id'],'question':case['question'],'direction_coverage':coverage,
                    'wrong_direction_or_card':wrong,'graph_paths':len(paths),
                    'question_top_ids':[[c['id'] for c in g['chunks']] for g in found['question']['draws']],
                    'expanded_top_ids':[[c['id'] for c in g['chunks']] for g in found['expanded']['draws']]})
        report={'dataset':'tarot-v1','cases':len(results),'embedding_profile':embedder.profile,
                'criterion':'Three selected card directions retrieved; metadata filtering coverage, not human relevance accuracy',
                'llm_evaluation':'Not performed; no external LLM called','results':results}
        (ROOT/'docs/TAROT_RETRIEVAL_CHECKS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        assert all(r['wrong_direction_or_card']==0 and all(n==3 for n in r['direction_coverage'].values()) for r in results)
        print(f'PASS: {len(results)} fixed cases, all three directions covered, no wrong-card/direction results')
    finally:
        if vector: vector.close()
        embedder.close()

if __name__=='__main__': main()

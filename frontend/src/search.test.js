import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {cosine,vectorSearch,expandGraph,makePrompt} from './search.js';
import {evidenceCypher} from './study.js';
const data=JSON.parse(readFileSync(new URL('../public/data/graph.json',import.meta.url),'utf8'));
test('vector invariants reject mismatched and zero vectors',()=>{
  assert.equal(cosine([1,0],[1,0]),1);assert.equal(cosine([1,0],[0,1]),0);
  assert.throws(()=>cosine([1],[1,2]));assert.throws(()=>cosine([0],[1]));
});
test('Korean travel probe finds a relevant card',()=>{
  const seeds=vectorSearch(data,data.probe.embedding);
  assert.equal(seeds.length,3);assert.ok(seeds.some(c=>/여행/.test(c.title+c.text)));
});
test('graph extensions are supported by explicit paths and exclude seed chunks',()=>{
  const seeds=vectorSearch(data,data.probe.embedding);
  const seedIds=seeds.map(c=>c.id);
  for(const type of data.types)for(const sign of data.signs){
    const paths=expandGraph(data,seeds,type.code,sign.id);
    assert.ok(paths.length>0&&paths.length<=5);
    for(const path of paths){
      assert.ok(!seedIds.includes(path.chunk.id));
      assert.ok(path.chunk.traits.includes(path.trait));
      assert.ok(path.chunk.tips.includes(path.tip.id));
      assert.equal(path.tip.trait,path.trait);
      assert.ok(path.via.every(id=>seeds.find(s=>s.id===id).traits.includes(path.trait)));
    }
  }
});
test('prompt includes traceable evidence and question without network calls',()=>{
  const seeds=vectorSearch(data,data.probe.embedding);
  const paths=expandGraph(data,seeds,'INTJ','aquarius');
  const prompt=makePrompt('旅行？','INTJ','물병자리',seeds,paths);
  assert.ok(prompt.includes('旅行？'));assert.ok(prompt.includes(seeds[0].id));
});

test('expanded corpus contains 600 real, finite vectors and every profile facet',()=>{
  assert.equal(data.chunks.length,600);
  assert.equal(new Set(data.chunks.map(c=>c.id)).size,600);
  const subjects=new Map();
  for(const c of data.chunks){
    assert.equal(c.embedding.length,data.model.dimensions);
    assert.ok(c.embedding.every(Number.isFinite));
    assert.ok(Math.abs(c.embedding.reduce((sum,x)=>sum+x*x,0)-1)<.01);
    if(c.subject){subjects.set(c.subject,(subjects.get(c.subject)||0)+1);assert.match(c.source_url,/^https:\/\//);}
  }
  assert.equal(subjects.size,28);assert.ok([...subjects.values()].every(n=>n===10));
});

test('graph ranking uses semantic proximity and preserves vector seeds when selection changes',()=>{
  const seeds=vectorSearch(data,data.probe.embedding);
  const before=seeds.map(c=>c.id);
  const paths=expandGraph(data,seeds,'INTJ','aquarius');
  assert.deepEqual(seeds.map(c=>c.id),before);
  assert.ok(paths.every(p=>Number.isFinite(p.similarity)&&p.similarity>0));
  assert.ok(paths.every((p,i)=>i===0||p.rank<=paths[i-1].rank));
  expandGraph(data,seeds,'ESFP','leo');
  assert.deepEqual(vectorSearch(data,data.probe.embedding).map(c=>c.id),before);
});

test('Neo4j evidence queries support all corpus identifiers and reject injected IDs',()=>{
  for(const c of data.chunks){
    const query=evidenceCypher({via:[c.id],chunk:c,trait:c.traits[0],tip:{id:c.tips[0]}});
    assert.ok(query.includes(c.id));
  }
  assert.throws(()=>evidenceCypher({via:["x' RETURN 1 //"],chunk:data.chunks[0],trait:'I',tip:{id:'quiet'}}));
});

test('graph expansion stays near seed meaning rather than sorting by corpus ID',()=>{
  const fake={...data,chunks:[
    {id:'a-unrelated',traits:['I'],tips:['quiet'],embedding:[0,1]},
    {id:'z-related',traits:['I'],tips:['quiet'],embedding:[.99,.01]},
  ]};
  const paths=expandGraph(fake,[{id:'seed',traits:['I'],embedding:[1,0]}],'INTJ','aquarius');
  assert.equal(paths[0].chunk.id,'z-related');
});

test('question-aware graph expansion keeps the travel context visible',()=>{
  const seeds=vectorSearch(data,data.probe.embedding);
  const paths=expandGraph(data,seeds,'INTJ','aquarius',3,data.probe.embedding);
  assert.ok(paths.some(p=>/여행|관광|즉흥/.test(p.chunk.title+p.chunk.category)));
  assert.ok(paths.every(p=>Math.abs(p.similarity-cosine(data.probe.embedding,p.chunk.embedding))<1e-10));
});

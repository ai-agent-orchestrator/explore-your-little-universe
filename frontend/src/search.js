// Pure search/graph traversal, shared by the UI and executable tests.
export function cosine(a,b){
  if(!a?.length||a.length!==b?.length)throw Error('임베딩 차원이 일치하지 않습니다.');
  let dot=0,aa=0,bb=0;
  for(let i=0;i<a.length;i++){if(!Number.isFinite(a[i])||!Number.isFinite(b[i]))throw Error('잘못된 벡터입니다.');dot+=a[i]*b[i];aa+=a[i]*a[i];bb+=b[i]*b[i];}
  if(!aa||!bb)throw Error('빈 벡터입니다.');
  return Math.max(-1,Math.min(1,dot/Math.sqrt(aa*bb)));
}
export function vectorSearch(data,vector,k=3){
  return data.chunks.map(c=>({...c,score:cosine(vector,c.embedding)}))
    .sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id)).slice(0,k);
}
export function expandGraph(data,seeds,code,signId,limit=5,queryVector){
  const selectedType=data.types.find(t=>t.code===code);
  const selectedSign=data.signs.find(s=>s.id===signId);
  if(!selectedType||!selectedSign)throw Error('유형과 별자리를 선택해주세요.');
  const seedIds=new Set(seeds.map(c=>c.id));
  const seedTraits=new Set(seeds.flatMap(c=>c.traits));
  const unionTraits=new Set([...selectedType.traits,...selectedSign.traits]);
  const paths=[];
  for(const other of data.chunks){
    if(seedIds.has(other.id))continue;
    const seedSimilarity=Math.max(...seeds.map(seed=>cosine(seed.embedding,other.embedding)));
    const similarity=queryVector?cosine(queryVector,other.embedding):seedSimilarity;
    const direct=(other.subject_kind==='mbti'&&other.subject===code)||(other.subject_kind==='zodiac'&&other.subject===signId);
    for(const trait of other.traits){
      if(!seedTraits.has(trait))continue;
      for(const tip of data.suggestions){
        if(tip.trait!==trait||!other.tips.includes(tip.id))continue;
        const via=seeds.filter(s=>s.traits.includes(trait)).map(s=>s.id);
        const shared=selectedType.traits.includes(trait)&&selectedSign.traits.includes(trait);
        const selected=unionTraits.has(trait);
        const rank=.75*similarity+.25*seedSimilarity+(shared ? .02 : 0)+(selected ? .01 : 0)+(direct ? .015 : 0);
        paths.push({chunk:other,trait,tip,via,shared,selected,direct,similarity,rank});
      }
    }
  }
  // Selection only reorders graph paths; it never changes the vector seeds.
  paths.sort((a,b)=>b.rank-a.rank||a.chunk.id.localeCompare(b.chunk.id)||a.tip.id.localeCompare(b.tip.id));
  const usedChunks=new Set(),usedTips=new Set();
  return paths.filter(p=>{if(usedChunks.has(p.chunk.id)||usedTips.has(p.tip.id))return false;usedChunks.add(p.chunk.id);usedTips.add(p.tip.id);return true;}).slice(0,limit);
}
export function makePrompt(question,code,sign,seeds,paths){
  const lines=['다음은 재미와 자기 성찰용 해설 재서술 및 직접 작성한 가상 예시 자료입니다. 진단·궁합·성격의 과학적 예측을 하지 마세요.',
    '질문과 직접 관련된 근거만 사용해 한국어로 짧게 요약하고, 작은 행동 제안 1개를 해주세요. 근거가 부족하면 그렇게 말하고 출처 ID를 표시하세요.',
    `질문: ${question}`,`선택한 재미용 설정: ${code} / ${sign}`,'[벡터로 찾은 상황 글]'];
  const provenance=c=>`${c.source}${c.source_url?' · 참고: '+c.source_url:''}`;
  seeds.forEach(c=>lines.push(`[${c.id}] ${c.title}: ${c.text} / 출처: ${provenance(c)}`));
  lines.push('[그래프에서 추가한 근거 — 연관성이 답변의 정확성을 보장하지 않음]');
  paths.forEach(p=>lines.push(`[${p.chunk.id}] ${p.chunk.text} / 제안: ${p.tip.text} / 경로: ${p.via.join(',')} → 성향 ${p.trait} → ${p.chunk.id} / 출처: ${provenance(p.chunk)}`));
  return lines.join('\n');
}

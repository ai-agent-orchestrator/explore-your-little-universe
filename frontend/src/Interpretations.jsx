import React,{useState} from 'react';

export function Source({card}){
 return <span>{card.source}{card.source_url&&<> · <a href={card.source_url} target="_blank" rel="noreferrer">참고 자료 열기</a></>}<br/>{card.editorial_note}</span>;
}

export function Interpretations({data,code,signId}){
 const [facet,setFacet]=useState('기본 성향');
 const profiles=data.chunks.filter(c=>c.kind==='interpretation');
 const facets=[...new Set(profiles.map(c=>c.facet))];
 const selected=profiles.filter(c=>c.facet===facet&&
   ((c.subject_kind==='mbti'&&c.subject===code)||(c.subject_kind==='zodiac'&&c.subject===signId)));
 if(!selected.length)return null;
 return <section className="interpretation-library">
  <div className="section-title"><div><div className="overline">A LITTLE LIBRARY OF PERSPECTIVES</div><h2>나의 성향을 일상에서 읽어보기</h2></div>
   <label>살펴볼 주제 <select value={facet} onChange={e=>setFacet(e.target.value)}>{facets.map(f=><option key={f}>{f}</option>)}</select></label></div>
  <p>해설과 일상 사례 {data.chunks.length}개가 연결되어 있어요. 유형과 별자리를 바꾸고, 같은 주제의 두 관점을 살펴보세요.</p>
  <div className="interpretation-cards">{selected.map(card=><article className="evidence" key={card.id}>
   <div className="card-meta"><span>{card.subject_kind==='mbti'?'유형 해설':'별자리 해설'}</span><span>{card.facet}</span></div>
   <h3>{card.title}</h3><p>{card.text}</p>
   <p className="fine">{card.traits.map(key=>data.traits.find(t=>t.id===key)?.title).join(' · ')}</p>
   <p>{data.suggestions.find(t=>t.id===card.tips[0])?.text}</p>
   <details><summary>출처와 연결 확인</summary><p><Source card={card}/><br/>{card.id} · {card.document_id}<br/>
    {card.subject} → DESCRIBED_BY → {card.id} ← FROM_CHUNK ← {card.traits.join(', ')}</p></details>
  </article>)}</div>
  <p className="fine">공개 소개를 짧게 재서술하고 일상 적용 예시를 직접 작성했어요. 16Personalities는 공식 MBTI와 다른 NERIS 모델이며, 별자리와 공통 성향을 잇는 관계는 이 실습에서 정한 매핑이에요.</p>
 </section>;
}

import React,{useEffect,useState} from 'react';
import {Lumi} from './Lumi.jsx';

export const ZODIAC={
 aries:['♈','#edb59d','용기 한 스푼'],taurus:['♉','#b7d3ac','느긋한 한 걸음'],
 gemini:['♊','#f1d286','호기심 반짝'],cancer:['♋','#b7cce9','포근한 쉼표'],
 leo:['♌','#f1c479','햇살 같은 응원'],virgo:['♍','#bfceb7','차분한 작은 정리'],
 libra:['♎','#e2bbd7','마음의 균형'],scorpio:['♏','#bdb0dd','깊은 마음 한 조각'],
 sagittarius:['♐','#b8c3ed','새로운 관점 여행'],capricorn:['♑','#adc9cb','든든한 작은 발걸음'],
 aquarius:['♒','#b7cfe9','나만의 반짝임'],pisces:['♓','#c9bde8','다정한 상상'],
};
export function ZodiacLumi({sign,code,small=false}){
 const [symbol,color,note]=ZODIAC[sign.id];
 return <div className={'zodiac-lumi '+(small?'compact':'')} style={{'--zodiac':color}}><div className="zodiac-halo"><span className="zodiac-symbol" aria-label={sign.name}>{symbol}</span><Lumi code={code} small={small} colorOverride={color}/><span className="orbit-dot first"/><span className="orbit-dot second"/></div><b>{sign.name} 루미</b><span>{note}</span></div>;
}

export function UniverseGraph({data,code,signId}){
 const sign=data.signs.find(s=>s.id===signId),type=data.types.find(t=>t.code===code);
 const keys=[...new Set([...type.traits,...sign.traits])].sort();
 const [active,setActive]=useState(keys[0]);
 useEffect(()=>setActive(type.traits[0]),[code,signId]);
 const trait=data.traits.find(t=>t.id===active);
 const related=data.chunks.filter(c=>c.traits.includes(active));
 const selected=c=>(c.subject_kind==='mbti'&&c.subject===code)||(c.subject_kind==='zodiac'&&c.subject===signId);
 const cards=[...related].sort((a,b)=>Number(selected(b))-Number(selected(a))).slice(0,3);
 return <section className="universe-section"><div className="universe-mascot"><div className="overline">YOUR LITTLE STAR COMPANION</div><ZodiacLumi sign={sign} code={code}/><p>별자리는 작은 상상,<br/>성격 유형은 다른 관점을 여는 열쇠예요.<br/><b>나답게 가도 괜찮아요.</b></p></div><div className="universe-graph"><div className="section-title"><div><div className="overline">MBTI × ASTROLOGY × KNOWLEDGE GRAPH</div><h2>나의 작은 우주가 연결되는 모습</h2></div><span className="pill">Neo4j에서 가져온 예시 관계</span></div><div className="graph-scroll"><svg viewBox="0 0 700 350" role="img" aria-label={`${code}와 ${sign.name}가 연결된 공통 성향 그래프`}>{keys.map((key,i)=>{const y=38+i*(270/Math.max(keys.length-1,1));return <g key={key}>{type.traits.includes(key)&&<path d={`M155 100 C270 100 310 ${y} 390 ${y}`} fill="none" stroke="#c5b0df" strokeWidth="2"/>}{sign.traits.includes(key)&&<path d={`M155 255 C270 255 310 ${y} 390 ${y}`} fill="none" stroke="#9fc9be" strokeWidth="2"/>}<g role="button" tabIndex="0" aria-label={`성향 ${data.traits.find(t=>t.id===key).title}`} onClick={()=>setActive(key)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setActive(key)}}}><rect x="390" y={y-17} width="220" height="35" rx="17" fill={active===key?'#9b7cbd':'#f1edf8'}/><text x="500" y={y+5} textAnchor="middle" fontSize="14" fill={active===key?'white':'#806393'}>{data.traits.find(t=>t.id===key).title}</text></g></g>})}<circle cx="120" cy="100" r="35" fill="#9675b8"/><text x="120" y="106" textAnchor="middle" fontSize="17" fill="white">{code}</text><circle cx="120" cy="255" r="35" fill={ZODIAC[signId][1]}/><text x="120" y="261" textAnchor="middle" fontSize="26" fill="#665073">{ZODIAC[signId][0]}</text><text x="120" y="310" textAnchor="middle" fontSize="14" fill="#79668b">{sign.name}</text><text x="260" y="165" textAnchor="middle" fontSize="12" fill="#a18bb3">HAS_TRAIT</text></svg></div><div className="path-detail"><b>{trait?.title}</b><span className="block">연결된 해설·사례 {related.length}개 중: {cards.map(c=>c.title).join(' · ')}</span><span>노드를 눌러 연결된 이야기를 살펴보세요. 이 연결은 재미용 가상 매핑이에요.</span></div></div></section>;
}

export function DailyMission({paths,data,code,signId,example}){
 const [index,setIndex]=useState(0),[done,setDone]=useState(false);
 useEffect(()=>{setIndex(0);setDone(false)},[paths]);
 const path=paths[index%paths.length];if(!path)return null;
 const sign=data.signs.find(s=>s.id===signId);
 return <section className="mission"><ZodiacLumi code={code} sign={sign} small/><div><div className="overline">LUMI'S LITTLE ACTION</div><h2>{done?'시도해줘서 고마워요. 오늘 하루도 화이팅!':'오늘은 이 중 하나만 해봐도 좋아요.'}</h2><p className="mission-tip">{path.tip.text}</p><p>크게 바꾸지 않아도 괜찮아요. 내 속도로, 작은 한 걸음이면 충분해요.</p><span className="fine">{example?'저장된 예제의 제안':'검색한 근거에서 찾은 제안'} · {path.chunk.title} ({path.chunk.id})</span></div><div className="mission-actions"><button onClick={()=>setDone(!done)}>{done?'루미가 응원할게요 ♡':'가볍게 해볼게요 ♡'}</button><button onClick={()=>{setIndex((index+1)%paths.length);setDone(false)}}>다른 작은 행동 보기</button></div></section>;
}

import React from 'react';
const POSITIONS={past:'과거를 돌아보는 자리',present:'현재를 살피는 자리',future:'앞으로의 선택을 묻는 자리'};

export default function Card({draw,index,revealed,available,name,onReveal}){
 const direction=draw.orientation==='reversed'?'역방향':'정방향';
 return <article className="tarot-card-slot"><h3>{index+1}. {POSITIONS[draw.position]}</h3>
  <button type="button" className={'tarot-card '+(revealed?'is-revealed':'')} onClick={onReveal} disabled={!available||revealed}
    aria-pressed={revealed} aria-label={revealed?`${name} · ${direction}`:`${index+1}번째 카드 공개하기`}>
   <span className="tarot-card-inner"><span className="tarot-back"><span aria-hidden="true">✦</span><b>LUMI</b><small>작은 관점 한 장</small></span>
   <span className="tarot-front"><span className={'tarot-symbol '+(draw.orientation==='reversed'?'reversed':'')} aria-hidden="true">☾<small>↑</small></span><b>{name}</b><span>{direction}</span></span></span>
  </button>
  <p>{revealed?direction:available?'눌러서 천천히 펼쳐보세요.':'앞의 카드를 먼저 펼쳐주세요.'}</p>
 </article>;
}

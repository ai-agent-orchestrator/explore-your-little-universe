import React,{useState} from 'react';
import {evidenceCypher} from './study.js';
import {Source} from './Interpretations.jsx';
export function Study({paths}){
 const [message,setMessage]=useState('');const path=paths[0];if(!path)return null;
 const query=evidenceCypher(path);
 return <details className="study-panel"><summary>학습용 근거 · Neo4j에서 직접 확인하기</summary><p>브라우저 결과는 Neo4j에서 내보낸 공개 예시 그래프입니다. 아래 쿼리를 같은 DB에서 실행하면 실제 원문과 관계를 볼 수 있어요. 유형·별자리 연결은 직접 만든 재미용 매핑입니다.</p><pre>{query}</pre><button onClick={async()=>{try{await navigator.clipboard.writeText(query);setMessage('쿼리를 복사했습니다. Neo4j Browser에 붙여넣으세요.')}catch{setMessage('위 쿼리를 직접 선택해서 복사해주세요.')}}}>Neo4j 확인 쿼리 복사</button><span role="status">{message}</span><p><b>출처:</b> {path.chunk.document_title} · {path.chunk.document_id} · {path.chunk.id}<br/><Source card={path.chunk}/><br/><b>원문:</b> {path.chunk.text}</p></details>;
}

import React,{useEffect,useRef,useState} from 'react';
import Card from './Card.jsx';
import {Lumi} from '../Lumi.jsx';
import {health,cards,createReading,getReading,resumeReading,watchReading,loadSession,saveSession} from './api.js';
import './tarot.css';

const TYPES=['INTJ','INTP','ENTJ','ENTP','INFJ','INFP','ENFJ','ENFP','ISTJ','ISFJ','ESTJ','ESFJ','ISTP','ISFP','ESTP','ESFP'];
const SIGNS=[['aries','양자리'],['taurus','황소자리'],['gemini','쌍둥이자리'],['cancer','게자리'],['leo','사자자리'],['virgo','처녀자리'],['libra','천칭자리'],['scorpio','전갈자리'],['sagittarius','사수자리'],['capricorn','염소자리'],['aquarius','물병자리'],['pisces','물고기자리']];
const TERMINAL=['completed','failed','needs_evidence','validation_failed'];
const EVENTS={'session.created':'질문을 기록했어요.','draw.confirmed':'세 장이 정해졌어요.','graph.completed':'연결된 관점을 찾았어요.','retrieval.completed':'해설의 근거를 모았어요.','draft.validating':'해설과 출처를 확인하고 있어요.','report.completed':'해설이 준비됐어요.','report.needs_evidence':'이 카드의 근거를 더 준비해야 해요.','run.failed':'처리가 중단됐어요. 같은 카드로 다시 이어갈 수 있어요.'};
const ERRORS={embedding_unavailable:'임베딩 모델을 준비한 뒤 서버를 다시 시작해주세요.',llm_not_configured:'서버의 LLM 연결 설정이 필요해요.',postgres_unavailable:'질문 이력 저장소를 확인해주세요.',neo4j_unavailable:'관계 저장소를 확인해주세요.',chroma_unavailable:'해설 검색 자료를 준비해주세요.',not_found:'이 세션의 접근 정보가 없거나 만료됐어요.',run_in_progress:'이미 같은 카드를 처리하고 있어요. 연결을 다시 확인해주세요.',session_token_required:'첫 생성 응답을 받지 못했어요. 중복 뽑기를 막기 위해 같은 요청은 중단했어요. 새 질문으로 시작하려면 아래에서 새 세션을 선택해주세요.',idempotency_conflict:'저장된 요청과 내용이 달라요. 새 질문은 새 세션으로 시작해주세요.'};

export default function TarotMode({apiUrl}){
 const [session,setSession]=useState(()=>loadSession());
 const [input,setInput]=useState(()=>loadSession()?.input||{mbti:'INTJ',zodiac_id:'aquarius',question:'새 일을 시작해도 괜찮을까?',spread:'three_card_reflection'});
 const [catalogue,setCatalogue]=useState({});const [services,setServices]=useState(null);
 const [view,setView]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [status,setStatus]=useState('내 질문을 살필 세 장을 준비해요.'),[reconnect,setReconnect]=useState(0);
 const [revealed,setRevealed]=useState(()=>loadSession()?.revealed||[]);
 const cursor=useRef(session?.lastEventId||0);const controller=useRef(null);
 function remember(next){setSession(next);if(!saveSession(next))setError('이 브라우저에 이어보기 정보를 저장하지 못했어요. 새로고침하면 접근 정보를 잃을 수 있어요.')}
 function message(e){return ERRORS[e.code]||'서버에 연결하지 못했어요. 같은 세션의 연결을 다시 확인해주세요.'}

 useEffect(()=>{const abort=new AbortController();health(apiUrl,abort.signal).then(setServices).catch(()=>setError('로컬 타로 서버를 시작해주세요.'));cards(apiUrl,abort.signal).then(rows=>setCatalogue(Object.fromEntries(rows.map(c=>[c.card_id,c.name_ko])))).catch(()=>{});return()=>abort.abort()},[apiUrl]);

 useEffect(()=>{
  if(!session?.session_id)return;
  const abort=new AbortController();controller.current=abort;
  async function follow(){
   setBusy(true);setError('');
   try{
    let current=await getReading(apiUrl,session,abort.signal);setView(current);
    if(!TERMINAL.includes(current.status)){
     await watchReading(apiUrl,session,event=>{
      setStatus(EVENTS[event.event]||'이야기를 이어가고 있어요.');
      if(event.id!==null){cursor.current=event.id;setSession(prev=>{const next={...prev,lastEventId:event.id};saveSession(next);return next})}
     },{signal:abort.signal,after:cursor.current});
     current=await getReading(apiUrl,session,abort.signal);setView(current);
    }
    setStatus(current.status==='completed'?'해설이 준비됐어요. 세 장을 펼치고 살펴보세요.':current.status==='needs_evidence'?'이 카드의 근거를 더 준비해야 해요.':current.status==='validation_failed'?'해설이 검수를 통과하지 못했어요.':current.status==='failed'?'처리가 중단됐어요. 같은 카드로 이어갈 수 있어요.':'연결을 다시 확인해주세요.');
   }catch(e){if(!abort.signal.aborted)setError(message(e))}
   finally{if(!abort.signal.aborted)setBusy(false)}
  }
  follow();return()=>abort.abort();
 },[apiUrl,session?.session_id,reconnect]);

 useEffect(()=>()=>controller.current?.abort(),[]);
 async function submit(e){
  e.preventDefault();if(busy||session?.session_id)return;
  setBusy(true);setError('');
  const key=session?.key||crypto.randomUUID();const pending={key,input,revealed:[],lastEventId:0};remember(pending);
  try{const created=await createReading(apiUrl,input,key);cursor.current=0;setRevealed([]);remember({...pending,...created});setStatus('세 장이 정해졌어요. 한 장씩 펼쳐보세요.')}
  catch(e){setError(message(e));setBusy(false)}
 }
 async function resume(){setError('');setBusy(true);try{await resumeReading(apiUrl,session);setReconnect(n=>n+1)}catch(e){setError(message(e));setBusy(false)}}
 function reset(){controller.current?.abort();remember(null);setView(null);setRevealed([]);setError('');setBusy(false);cursor.current=0;setStatus('새 질문으로 다른 관점을 만나보세요.')}
 function reveal(index){const next=[...revealed,index];setRevealed(next);remember({...session,revealed:next})}
 const ready=services&&Object.values(services).every(value=>value==='ok');
 const draws=view?.draws||session?.draws||[];const report=view?.report;
 return <main className="tarot-mode"><section className="tarot-intro"><div><div className="overline">LUMI · TAROT REFLECTION LAB</div><h1>세 장의 관점으로,<br/><em>지금의 마음을 살펴요.</em></h1><p>MBTI와 별자리는 익숙한 시선, 카드는 새로운 질문이에요.<br/>정해진 미래 대신 내가 선택할 작은 행동을 찾아보세요.</p></div><Lumi code={input.mbti}/></section>
  <section className="ask-panel"><h2>오늘은 어떤 이야기를 나눌까요?</h2><p className="tarot-storage-note">이 실험은 질문·뽑기 이력·해설을 로컬 서버에 저장하고, 설정된 LLM에 질문과 근거를 전달해요. 이 탭에 보관한 접근 정보로 같은 세션을 이어볼 수 있어요.</p>
   <div className="tarot-health" aria-label="서버 준비 상태">{services?Object.entries(services).map(([name,value])=><span key={name} className={value==='ok'?'ready':'missing'}>{name} · {value==='ok'?'준비됨':value==='missing'?'설정 필요':'확인 필요'}</span>):<span>로컬 서버를 확인하고 있어요.</span>}</div>
   <form onSubmit={submit}><div className="selectors"><label>MBTI<select value={input.mbti} disabled={!!session?.key||busy} onChange={e=>setInput({...input,mbti:e.target.value})}>{TYPES.map(t=><option key={t}>{t}</option>)}</select></label><label>별자리<select value={input.zodiac_id} disabled={!!session?.key||busy} onChange={e=>setInput({...input,zodiac_id:e.target.value})}>{SIGNS.map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label></div>
    <label className="question-label" htmlFor="tarot-question">지금 떠오르는 고민</label><textarea id="tarot-question" value={input.question} disabled={!!session?.key||busy} minLength={2} maxLength={1000} rows={3} onChange={e=>setInput({...input,question:e.target.value})}/>
    {!session?.session_id&&<button className="primary" disabled={busy||!ready||input.question.trim().length<2}>{busy?'준비하고 있어요…':session?.key?'같은 요청 다시 확인':'질문을 남기고 세 장 만나기'}</button>}
   </form><p role="status" className="runtime-status">{status}</p>{error&&<p role="alert" className="notice">{error}</p>}
   {session?.key&&<div className="tarot-actions">{session.session_id&&<button disabled={busy} onClick={()=>setReconnect(n=>n+1)}>같은 세션 연결 확인</button>}{session.session_id&&['failed','needs_evidence','validation_failed'].includes(view?.status)&&<button disabled={busy||!ready} onClick={resume}>같은 카드로 다시 이어가기</button>}<button disabled={busy} onClick={reset}>새 세션 시작</button></div>}
   <p className="fine">새 세션은 새 카드로 시작해요. 브라우저 정보를 지워도 서버에 기록한 이력이 삭제되는 것은 아니에요.</p>
  </section>
  {draws.length>0&&<section className="tarot-spread" aria-label="확정된 세 장">{draws.map((draw,index)=><Card key={draw.card_id} draw={draw} index={index} name={catalogue[draw.card_id]||draw.card_id} revealed={revealed.includes(index)} available={index===revealed.length} onReveal={()=>reveal(index)}/>)}</section>}
  {report&&revealed.length===3&&<section className="tarot-report" aria-live="polite"><div className="overline">THREE PERSPECTIVES · ONE SMALL ACTION</div><h2>내 질문에 이어진 이야기</h2>{report.model_id?.startsWith('fake')&&<p className="notice">검증용 FakeLLM 결과입니다. 실제 LLM 해설 품질을 평가한 결과가 아니에요.</p>}{report.sections.map(s=><article key={s.card_id}><h3>{catalogue[s.card_id]||s.card_id} · {s.orientation==='reversed'?'역방향':'정방향'} · {s.position}</h3><p>{s.body}</p><details><summary>사용한 근거 확인</summary>{s.citations.map(id=>{const source=report.sources.find(c=>c.id===id);const path=report.graph_paths.find(p=>p.id===id);return <p key={id}><b>{source?.title||id}</b><br/>{source?.text||path?.node_ids?.join(' → ')}<br/>{source?.source||path?.source_id}</p>})}</details></article>)}<p>{report.summary}</p><div className="tarot-small-action"><b>오늘의 작은 행동</b><p>{report.small_action}</p></div></section>}
  <footer><p>직접 작성한 상징적 성찰 자료입니다. 성격·궁합·미래 사건을 판정하지 않아요. 과거·현재·미래는 질문을 나누는 자리 이름이에요.</p><a href="#">루미의 정적 탐색으로 돌아가기</a></footer>
 </main>;
}

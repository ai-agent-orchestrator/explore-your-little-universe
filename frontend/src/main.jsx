import React,{useEffect,useMemo,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {createEmbedder} from './embedding.js';
import {vectorSearch,expandGraph,makePrompt} from './search.js';
import './style.css';
import './extras.css';
import './page-background.css';
import {UniverseGraph,DailyMission} from './ZodiacLumi.jsx';
import {Study} from './Study.jsx';
import {Lumi as Star,OUTFITS} from './Lumi.jsx';
import {Interpretations,Source} from './Interpretations.jsx';

const EXAMPLES=['친구가 갑자기 여행을 가자고 해서 부담스러워','친구 답장이 늦으면 내가 잘못했나 신경 쓰여','하고 싶은 일은 많은데 시작을 못 하겠어','이번 주말은 아무 약속 없이 혼자 쉬고 싶어'];


function Evidence({card,score,extra,code}){return <article className={'evidence '+(extra?'extra':'')}><div className="card-meta"><span>{card.category}</span><span>{score!==undefined?'cosine '+score.toFixed(3):'GRAPH DISCOVERY'}</span></div><div className="lumi-card-title"><Star small code={code}/><h3>{card.title}</h3></div><p>{card.text}</p><details><summary>원문 · 출처 보기</summary><p>{card.document_title} · {card.id}<br/><Source card={card}/></p></details></article>}

function GraphPath({data,seeds,paths,code,sign}){
 const [active,setActive]=useState(0);
 useEffect(()=>setActive(0),[paths]);
 const p=paths[active];if(!p)return null;
 const trait=data.traits.find(t=>t.id===p.trait);
 const source=seeds.find(s=>s.id===p.via[0]);
 const nodes=[{x:100,y:90,label:source.title,kind:'검색된 글',text:source.text},
  {x:345,y:90,label:trait.title,kind:'공통 성향',text:`${source.id} ← FROM_CHUNK — ${trait.id} — FROM_CHUNK → ${p.chunk.id}`},
  {x:590,y:90,label:p.chunk.title,kind:'추가된 글',text:p.chunk.text},
  {x:825,y:90,label:'작은 행동 제안',kind:'제안',text:p.tip.text}];
 return <section className="graph-section"><div className="section-title"><div><div className="overline">FOLLOW THE LITTLE CONNECTIONS</div><div className="lumi-card-title"><Star small code={code}/><h2>한 이야기가 다른 이야기를 만날 때</h2></div></div><span className="pill">실제 저장된 연결 경로</span></div><div className="path-tabs">{paths.map((path,i)=><button key={path.chunk.id} className={active===i?'active':''} onClick={()=>setActive(i)}>{data.traits.find(t=>t.id===path.trait).title}</button>)}</div><div className="graph-scroll"><svg viewBox="0 0 930 190" aria-label="청크에서 성향을 거쳐 새 근거와 제안으로 이어지는 경로">{nodes.slice(1).map((n,i)=><g key={n.x}><path d={`M${nodes[i].x+23},90 L${n.x-23},90`} stroke="#c9bbdf" strokeWidth="2"/><text x={(nodes[i].x+n.x)/2} y="69" textAnchor="middle" fontSize="11" fill="#756a84">{i<2?'FROM_CHUNK':'FROM_CHUNK (근거)'}</text></g>)}{nodes.map((n,i)=><g key={n.x} role="button" tabIndex="0" onClick={()=>setDetail(n.text)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setDetail(n.text)}}} aria-label={n.label}><circle cx={n.x} cy={n.y} r="23" fill={['#9070bd','#c4ace3','#70a69b','#dfb95a'][i]}/><text x={n.x} y="98" textAnchor="middle" fill="white" fontSize="22">{['✦','✧','✦','♡'][i]}</text><text x={n.x} y="139" textAnchor="middle" fill="#453653" fontSize="13">{n.label}</text><text x={n.x} y="162" textAnchor="middle" fill="#80718d" fontSize="11">{n.kind}</text></g>)}</svg></div><PathDetail key={p.chunk.id} p={p} code={code} sign={sign} trait={trait}/></section>;
 // Click details are displayed as an accessible native dialog-free text area.
 function setDetail(text){const out=document.getElementById('path-detail');if(out)out.textContent=text;}
}
function PathDetail({p,code,sign,trait}){return <div id="path-detail" className="path-detail" aria-live="polite">{p.tip.text}<br/><span>{trait.title} · {p.shared?`${code}와 ${sign}가 공유하는 재미용 연결`:p.selected?'선택한 유형 또는 별자리와 연결':'검색된 상황 글에서 확장한 연결'}</span></div>}

function App(){
 const [data,setData]=useState(null),[fatal,setFatal]=useState('');
 const [code,setCode]=useState('INTJ'),[sign,setSign]=useState('aquarius');
 const [question,setQuestion]=useState(EXAMPLES[0]),[result,setResult]=useState(null);
 const [embedder,setEmbedder]=useState(null),[busy,setBusy]=useState(false),[status,setStatus]=useState('작은 이야기들을 준비하고 있어요.'),[notice,setNotice]=useState('');
 useEffect(()=>{let mounted=true;fetch(import.meta.env.BASE_URL+'data/graph.json').then(r=>{if(!r.ok)throw Error('그래프 데이터를 불러오지 못했습니다.');return r.json()}).then(d=>{if(mounted){setData(d);setStatus(d.chunks.length+"개의 작은 이야기가 기다리고 있어요. 이야기 들려줘서 고마워요.");setResult({query:d.probe.text,vector:d.probe.embedding,seeds:vectorSearch(d,d.probe.embedding),example:true,ms:0})}}).catch(e=>{if(mounted)setFatal(e.message)});return()=>{mounted=false}},[]);
 const paths=useMemo(()=>data&&result?expandGraph(data,result.seeds,code,sign,5,result.vector):[],[data,result,code,sign]);
 const selectedSign=data?.signs.find(s=>s.id===sign);
 const prompt=useMemo(()=>data&&result?makePrompt(result.query,code,selectedSign.name,result.seeds,paths):'',[data,result,paths,code,selectedSign]);
 async function search(e){e?.preventDefault();if(!data||busy||!question.trim())return;setBusy(true);setNotice('');
   try{const began=performance.now();let local=embedder;if(!local){local=await createEmbedder(data,setStatus);setEmbedder(local);setData(local.data)}setStatus('질문을 읽고 연결된 이야기를 찾고 있어요…');const start=performance.now();const vector=await local.embed(question.trim());const seeds=vectorSearch(local.data,vector);setResult({query:question.trim(),vector,seeds,example:false,ms:Math.round(performance.now()-start),totalMs:Math.round(performance.now()-began)});setStatus('이야기 들려줘서 고마워요. 오늘의 작은 한 걸음도 루미가 응원할게요!');}
   catch(error){console.error('Embedding initialization/search failed',error);setNotice('모델을 실행하지 못했어요. WebGPU가 지원되는 최신 Chrome 또는 Edge에서 다시 시도해주세요. 예제 결과는 계속 볼 수 있어요.');setStatus('저장된 예제는 계속 살펴볼 수 있어요.');}finally{setBusy(false)}
 }
 async function copy(){try{await navigator.clipboard.writeText(prompt);setNotice('프롬프트를 복사했어요. Gemini에 직접 붙여넣어 사용하세요.')}catch{setNotice('아래 프롬프트를 펼쳐 직접 복사해주세요.')}}
 if(fatal)return <main><h1>잠시 길을 잃었어요.</h1><p>{fatal}</p><button onClick={()=>location.reload()}>다시 불러오기</button></main>;
 if(!data)return <main><Star code={code} caption/><p>작은 이야기들을 불러오는 중…</p></main>;
 return <><header><a className="brand" href="#">✦ EXPLORE <b>YOUR LITTLE UNIVERSE</b></a><span className="header-label">MBTI × ASTROLOGY · JUST FOR FUN</span><a className="github" href="https://github.com/ai-agent-orchestrator/explore-your-little-universe" target="_blank" rel="noreferrer">GitHub</a></header><main>
 <section className="hero"><div><div className="overline">A LITTLE INSIGHT. ONE SMALL ACTION.</div><h1>오늘의 작은 고민,<br/><em>별다른 시선으로.</em></h1><p>A playful daily-action lab inspired by MBTI and astrology.<br/>정답을 정해주는 대신, 나를 이해할 작은 실마리를 함께 찾아요.</p><div className="hero-tags"><span>✧ 나를 읽는 재미</span><span>✧ 연결을 발견하는 즐거움</span><span>✧ 내 기기에서 검색</span></div><div className="serverless-badge">Serverless · Google LiteRT-LM · On-device search</div></div><div className="mascot"><div className="speech">안녕, 난 루미!<br/>{OUTFITS[code][3]}</div><Star code={code} caption/></div></section>
 <section className="ask-panel"><div className="section-title"><div><div className="overline">LET'S EXPLORE YOUR LITTLE UNIVERSE</div><h2>지금 떠오르는 이야기를 들려주세요.</h2></div><span className="pill">{embedder?'LiteRT-LM 준비됨':'키·로그인 없이 시작'}</span></div><form onSubmit={search}><div className="selectors"><label>MY TYPE<select value={code} disabled={busy} onChange={e=>setCode(e.target.value)}>{data.types.map(t=><option key={t.code}>{t.code}</option>)}</select></label><label>MY STAR SIGN<select value={sign} disabled={busy} onChange={e=>setSign(e.target.value)}>{data.signs.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></label><p>유형과 별자리는 재미용 필터예요.<br/>검색한 근거는 바꾸지 않고 연결 경로의 순서만 조정해요.</p></div><label className="question-label" htmlFor="question">TODAY'S LITTLE DILEMMA</label><div className="input-line"><textarea id="question" value={question} maxLength={400} rows="2" onChange={e=>setQuestion(e.target.value)} placeholder="약속, 연락, 일, 휴식, 여행에 관한 작은 고민을 적어보세요."/><button className="primary" disabled={busy||!question.trim()}>{busy?'읽고 있어요…':'내 이야기 탐색하기'}</button></div><div className="examples">{EXAMPLES.slice(1).map(q=><button type="button" disabled={busy} key={q} onClick={()=>setQuestion(q)}>{q}</button>)}</div></form><p className="runtime-status" role="status">{status}</p>{!embedder&&<p className="fine">첫 검색 시 공개 임베딩 모델 약 165MB를 다운로드해 브라우저에서 실행해요. 최신 Chrome·Edge와 여유 메모리가 필요해요.</p>}{notice&&<p className="notice" role="status">{notice}</p>}</section>
 <UniverseGraph data={data} code={code} signId={sign}/><Interpretations data={data} code={code} signId={sign}/>{result&&<><div className="results-title"><div><div className="overline">TWO WAYS TO SEE YOUR STORY</div><h2>비슷한 이야기에서, 연결된 관점으로.</h2><p>“{result.query}”</p></div><span className="pill">{result.example?'저장된 질문의 예제 결과':`브라우저 검색 ${result.ms}ms`}</span></div>{result.example&&<p className="example-note">현재는 미리 계산한 예제 벡터의 결과입니다. 위에서 검색하면 입력한 질문을 LiteRT-LM으로 직접 임베딩합니다.</p>}<div className="compare"><section><div className="column-title"><span className="step">01</span><div><h2>비슷한 이야기</h2><p>VECTOR ONLY · 의미가 가까운 해설·사례 3개</p></div></div>{result.seeds.map(c=><Evidence key={c.id} card={c} score={c.score} code={code}/>)}<p className="fine">cosine은 문장 벡터의 유사도이며 확률·성격 점수·궁합 점수가 아닙니다. 언제나 가까운 글을 반환하므로 관련성은 직접 확인해주세요.</p></section><section><div className="column-title"><span className="step mint">02</span><div><h2>한 걸음 넓힌 관점</h2><p>VECTOR + GRAPH · 같은 근거에서 관계 확장</p></div></div>{paths.slice(0,3).map(p=><article className="discovery" key={p.chunk.id}><div className="card-meta"><span>{data.traits.find(t=>t.id===p.trait).title}</span><span>{p.shared?'TYPE + STAR':p.selected?'YOUR CONNECTION':'GRAPH LINK'}</span></div><div className="lumi-card-title"><Star small code={code}/><h3>{p.tip.text}</h3></div><p>{p.chunk.text}</p><details><summary>어떻게 연결됐나요?</summary><p>{p.via.join(', ')} → {p.trait} → {p.chunk.id} → {p.tip.id}<br/><Source card={p.chunk}/></p></details></article>)}<p className="fine">추가된 글은 직접 검색된 3개 글과 중복되지 않습니다. 관계가 있다고 질문의 정답인 것은 아니에요.</p></section></div><DailyMission data={data} paths={paths.slice(0,3)} code={code} signId={sign} example={result.example}/><GraphPath data={data} seeds={result.seeds} paths={paths.slice(0,3)} code={code} sign={selectedSign.name}/><Study paths={paths}/><section className="gemini-panel"><div><div className="overline">TAKE THE STORY A LITTLE FURTHER</div><div className="lumi-card-title"><Star small code={code}/><h2>더 이야기하고 싶다면, Gemini와.</h2></div><p>검색한 원문과 연결 경로를 하나의 프롬프트로 묶었어요.<br/>원할 때 직접 복사해 가져가세요. 자동으로 전송하지 않습니다.</p></div><div className="gemini-actions"><button onClick={copy}>근거 프롬프트 복사</button><a href="https://gemini.google.com/" target="_blank" rel="noreferrer">Gemini 열기</a></div><details><summary>프롬프트 미리보기</summary><textarea aria-label="Gemini용 근거 프롬프트" readOnly value={prompt} rows="12"/></details></section></>}
 <footer><div><b>✦ Explore Your Little Universe</b><p>A little insight. One small action.</p></div><p>공개 해설의 한국어 재서술, 직접 작성한 일상 예시와 재미용 성향 연결입니다. 공식 MBTI 검사·점성술 예측·진단·치료를 제공하지 않습니다.<br/>질문은 서버로 보내거나 저장하지 않습니다. 모델 다운로드 시 모델 호스트에 접속합니다.<br/>Neo4j에서 내보낸 공개 예시 그래프를 사용하며, 실행 중 DB에 접속하지 않습니다.</p></footer></main></>;
}
createRoot(document.getElementById('root')).render(<App/>);

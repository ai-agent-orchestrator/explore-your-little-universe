export class APIError extends Error{
 constructor(code,status){super(code);this.code=code;this.status=status}
}

function endpoint(base,path){
 const url=new URL(base);
 if(!['http:','https:'].includes(url.protocol)||url.username||url.password||url.search||url.hash)throw new Error('잘못된 서버 주소입니다.');
 return new URL(path,url.origin).href;
}

async function jsonRequest(base,path,{token,headers,...options}={}){
 const response=await fetch(endpoint(base,path),{...options,headers:{...headers,...(token?{Authorization:'Bearer '+token}:{})}});
 const body=await response.json();
 if(!response.ok)throw new APIError(body.error||'request_failed',response.status);
 return body;
}

export const health=(base,signal)=>jsonRequest(base,'/api/health',{signal});
export const cards=(base,signal)=>jsonRequest(base,'/api/cards',{signal});
export const getReading=(base,session,signal)=>jsonRequest(base,'/api/readings/'+session.session_id,{token:session.session_token,signal});
export const resumeReading=(base,session,signal)=>jsonRequest(base,'/api/readings/'+session.session_id+'/resume',{method:'POST',token:session.session_token,signal});
export const createReading=(base,input,key,token,signal)=>jsonRequest(base,'/api/readings',{
 method:'POST',token,signal,headers:{'Content-Type':'application/json','Idempotency-Key':key},body:JSON.stringify(input)});

// Incremental SSE parsing: supports split CRLF, UTF-8 decoder output, multi-line
// data, heartbeats and duplicate IDs without placing auth in a URL.
export function createSSEParser(onEvent,after=0){
 let buffer='',data=[],type='message',id='',cursor=after;
 function line(value){
  if(value===''){
   if(data.length){
    const sequence=/^\d+$/.test(id)?Number(id):null;
    if(sequence===null||sequence>cursor){
     const event={id:sequence,event:type,data:data.join('\n')};
     onEvent(event);
     if(sequence!==null)cursor=sequence;
    }
   }
   data=[];type='message';id='';return;
  }
  if(value.startsWith(':'))return;
  const colon=value.indexOf(':');const key=colon<0?value:value.slice(0,colon);
  let text=colon<0?'':value.slice(colon+1);if(text.startsWith(' '))text=text.slice(1);
  if(key==='data')data.push(text);
  else if(key==='event')type=text;
  else if(key==='id'&&!text.includes('\0'))id=text;
 }
 return {
  push(text){buffer+=text;let end;while((end=buffer.indexOf('\n'))>=0){const current=buffer.slice(0,end).replace(/\r$/,'');buffer=buffer.slice(end+1);line(current)}},
  end(){return cursor},
 };
}

export async function watchReading(base,session,onEvent,{signal,after=0}={}){
 const response=await fetch(endpoint(base,'/api/readings/'+session.session_id+'/events'),{
  signal,headers:{Authorization:'Bearer '+session.session_token,'Last-Event-ID':String(after),Accept:'text/event-stream'}});
 if(!response.ok){const body=await response.json();throw new APIError(body.error||'stream_failed',response.status)}
 if(!response.body)throw new Error('스트림을 읽을 수 없습니다.');
 const parser=createSSEParser(event=>onEvent({...event,data:JSON.parse(event.data)}),after);
 const reader=response.body.getReader();const decoder=new TextDecoder();
 try{
  while(true){const {done,value}=await reader.read();if(done)break;parser.push(decoder.decode(value,{stream:true}))}
  parser.push(decoder.decode());return parser.end();
 }finally{await reader.cancel().catch(()=>{});reader.releaseLock()}
}

export const STORAGE_KEY='lumi-tarot-session-v1';
export function loadSession(){try{return JSON.parse(sessionStorage.getItem(STORAGE_KEY)||'null')}catch{return null}}
export function saveSession(value){try{if(value)sessionStorage.setItem(STORAGE_KEY,JSON.stringify(value));else sessionStorage.removeItem(STORAGE_KEY);return true}catch{return false}}

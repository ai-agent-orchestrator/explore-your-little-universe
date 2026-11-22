import React,{lazy,Suspense,useEffect,useState} from 'react';
import StaticExplorer from './static/StaticExplorer.jsx';
import './modes.css';

const apiUrl=import.meta.env.VITE_TAROT_API_URL;
const TarotMode=import.meta.env.VITE_TAROT_API_URL ? lazy(()=>import('./tarot/TarotMode.jsx')) : null;

function ModeShell(){
 const [mode,setMode]=useState(location.hash==='#tarot'?'tarot':'static');
 useEffect(()=>{const update=()=>setMode(location.hash==='#tarot'?'tarot':'static');window.addEventListener('hashchange',update);return()=>window.removeEventListener('hashchange',update)},[]);
 return <><nav className="lumi-mode-nav" aria-label="탐색 모드"><a href="#" aria-current={mode==='static'?'page':undefined}>정적 탐색</a><a href="#tarot" aria-current={mode==='tarot'?'page':undefined}>타로 실험 · 로컬 서버</a></nav>{mode==='tarot'?<Suspense fallback={<main><p>타로 화면을 준비하고 있어요.</p></main>}><TarotMode apiUrl={apiUrl}/></Suspense>:<StaticExplorer/>}</>;
}

export default function App(){return apiUrl?<ModeShell/>:<StaticExplorer/>;}

import {EmbeddingEngine,Backend,loadLiteRtLm} from '@litert-lm/core';
import {cosine} from './search.js';
let enginePromise;
let runtimeLoaded=false;
const base=import.meta.env.BASE_URL;
export async function createEmbedder(data,onProgress){
  if(enginePromise)return enginePromise;
  enginePromise=(async()=>{
    const model=data.model;
    onProgress('LiteRT-LM 실행기를 준비하고 있습니다…');
    if(!runtimeLoaded){await loadLiteRtLm(new URL(base+'runtime/',location.href).href);runtimeLoaded=true;}
    const url=`https://huggingface.co/${model.repo}/resolve/${model.revision}/${model.file}`;
    const cacheName='mindmap-model-'+model.sha256;
    onProgress('임베딩 모델을 불러옵니다. 첫 실행은 약 165MB를 다운로드합니다.');
    let response;
    try{response=await (await caches.open(cacheName)).match(url);}catch{/* Cache API unavailable: load without persistence. */}
    if(!response){
      response=await fetch(url);
      if(!response.ok)throw Error('모델 다운로드에 실패했습니다. 네트워크를 확인해주세요.');
      try{await (await caches.open(cacheName)).put(url,response.clone());}catch{/* Storage quota may be limited. */}
    }
    const bytes=await response.arrayBuffer();
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
    if(digest!==model.sha256){try{await caches.delete(cacheName);}catch{}throw Error('모델 체크섬이 일치하지 않습니다. 다시 시도해주세요.');}
    onProgress('기기에서 임베딩 모델을 시작합니다…');
    const engine=await EmbeddingEngine.create({model:new Blob([bytes]).stream(),backend:Backend.GPU,maxInputLength:256,minInputLength:256,mainExecutorSettings:{numThreads:2}});
    try{
      const options={normalize:true,outputSize:model.dimensions,insertSpecialTokens:true};
      const embed=async text=>{
        const {embedding}=await engine.computeEmbedding(text,options);
        if(embedding.length!==model.dimensions||embedding.some(x=>!Number.isFinite(x)))throw Error('유효하지 않은 임베딩 결과입니다.');
        return embedding;
      };
      onProgress('모델과 벡터 호환성을 확인합니다…');
      const probe=await embed(data.probe.text);
      const agreement=cosine(probe,data.probe.embedding);
      // Different native/web kernels can round differently. A failed probe must
      // never mix vector spaces: rebuild this tiny public corpus in the browser.
      let chunks=data.chunks;
      if(agreement<.995){
        chunks=[];
        for(let i=0;i<data.chunks.length;i++){
          onProgress(`브라우저 벡터를 재구축합니다 ${i+1}/${data.chunks.length}`);
          const card=data.chunks[i];
          // must match lumi_core.corpus.chunk.embedding_text (plain-v1)
          chunks.push({...card,embedding:await embed(card.title+'\n'+card.text)});
        }
      }
      return {embed,data:{...data,chunks},agreement,reindexed:agreement<.995,close:()=>engine.delete()};
    }catch(error){engine.delete();throw error;}
  })().catch(error=>{enginePromise=undefined;throw error;});
  return enginePromise;
}

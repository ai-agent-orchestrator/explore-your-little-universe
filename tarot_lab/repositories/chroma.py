"""Explicit native embeddings only; never enables Chroma's default model."""
import hashlib
import json
from pathlib import Path
from lumi_core.embedding.litert import validate_vector
from lumi_core.corpus.chunk import content_hash
from lumi_core.versions import DATASET_VERSION
from tarot_lab.errors import ProfileMismatch, VectorUnavailable

def collection_name(profile,dataset=DATASET_VERSION):
    return f'lumi_{dataset}_{hashlib.sha256(profile.encode()).hexdigest()[:8]}'

def metadata(chunk):
    fields=('title','category','document_id','document_title','source','source_url','source_kind',
            'reviewed_on','editorial_note','card_id','orientation','position','topic','locale','content_hash')
    result={key:chunk.get(key) or '' for key in fields}
    result['content_hash']=chunk.get('content_hash') or content_hash(chunk)
    result.update(traits=json.dumps(chunk.get('traits',[])),tips=json.dumps(chunk.get('tips',[])),
                  dataset_version=DATASET_VERSION)
    return result

class ChromaRepository:
    def __init__(self,path,embedding_profile,*,create=False,dataset=DATASET_VERSION,client=None):
        if client is None:
            import chromadb
            from chromadb.config import Settings
            client=chromadb.PersistentClient(path=str(Path(path)),settings=Settings(anonymized_telemetry=False))
        self.client=client
        self.profile=embedding_profile
        self.dataset=dataset
        name=collection_name(embedding_profile,dataset)
        try:
            if create:
                self.collection=client.get_or_create_collection(name,embedding_function=None,
                    metadata={'embedding_profile':embedding_profile,'dataset_version':dataset},
                    configuration={'hnsw':{'space':'cosine'}})
            else:
                self.collection=client.get_collection(name,embedding_function=None)
            meta=self.collection.metadata or {}
            if meta.get('embedding_profile')!=embedding_profile or meta.get('dataset_version')!=dataset:
                raise ProfileMismatch()
            if self.collection.configuration.get('hnsw',{}).get('space')!='cosine':
                raise ProfileMismatch('Chroma distance must be cosine')
        except ProfileMismatch:
            raise
        except Exception as exc:
            raise VectorUnavailable() from exc

    def ping(self):
        if self.collection.count()==0: raise VectorUnavailable('Empty corpus')

    def close(self):
        self.client.close()

    def upsert(self,chunks,vectors):
        if len(chunks)!=len(vectors): raise ValueError('Vector count mismatch')
        for vector in vectors: validate_vector(vector)
        for offset in range(0,len(chunks),100):
            rows=chunks[offset:offset+100]
            self.collection.upsert(ids=[r['id'] for r in rows],documents=[r['text'] for r in rows],
                embeddings=vectors[offset:offset+100],metadatas=[metadata(r) for r in rows])

    def _search(self,vector,where,k):
        validate_vector(vector)
        try:
            result=self.collection.query(query_embeddings=[vector],where=where,n_results=k,
                                         include=['documents','metadatas','distances'])
            return [dict(meta,id=id,text=text,distance=float(distance),similarity=1-float(distance))
                    for id,text,meta,distance in zip(result['ids'][0],result['documents'][0],
                                                   result['metadatas'][0],result['distances'][0])]
        except Exception as exc: raise VectorUnavailable() from exc

    def search_for_draw(self,query_vec,card_id,orientation,k=3):
        return self._search(query_vec,{'$and':[{'card_id':card_id},{'orientation':orientation},
                                               {'dataset_version':self.dataset}]},k)

    def search_general(self,query_vec,k=3):
        return self._search(query_vec,{'$and':[{'card_id':''},{'dataset_version':self.dataset}]},k)

    def search_pair(self,question_vector,expanded_vector,draws):
        def search(vector):
            return {'draws':[{'draw':d,'chunks':self.search_for_draw(vector,d['card_id'],d['orientation'])} for d in draws],
                    'general':self.search_general(vector)}
        return {'question':search(question_vector),'expanded':search(expanded_vector)}

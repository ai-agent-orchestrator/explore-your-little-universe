"""Optional neo4j-graphrag adapter; the shared engine has no graph dependency."""
from neo4j_graphrag.embeddings.base import Embedder
from lumi_core.embedding.litert import (MODEL_REPO, MODEL_REVISION, MODEL_FILE, MODEL_PATH,
                                        DIMENSIONS, ROOT, sha256, validate_vector)
from lumi_core.embedding.litert import LiteRTEmbeddings as Engine

class LiteRTEmbeddings(Embedder):
    def __init__(self, model_path=MODEL_PATH):
        super().__init__()
        self._engine = Engine(model_path)
    def __getattr__(self, key):
        return getattr(self._engine, key)
    def embed_query(self, text):
        return self._engine.embed_query(text)
    def close(self):
        self._engine.close()

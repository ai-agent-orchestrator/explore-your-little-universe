"""LiteRT-LM adapter for neo4j-graphrag. Model identity travels with vectors."""
import hashlib
import math
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parents[2]
MODEL_REPO = 'litert-community/embeddinggemma-2-text-270m-litert-lm'
MODEL_REVISION = '9be6e8b90982095dc05c2bd162e4b954ee4dbac7'
MODEL_FILE = 'embeddinggemma-2-text-270m.litertlm'
MODEL_PATH = ROOT / 'models' / MODEL_FILE
DIMENSIONS = 768


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def validate_vector(vector):
    if len(vector) != DIMENSIONS or not all(math.isfinite(x) for x in vector):
        raise ValueError('Invalid embedding dimension or values')
    if sum(x * x for x in vector) < 1e-12:
        raise ValueError('Zero embedding')
    return vector


class LiteRTEmbeddings:
    def __init__(self, model_path=MODEL_PATH):
        import litert_lm
        self.path = Path(model_path)
        if not self.path.is_file():
            raise ValueError('Run python -m mbti_lab.download_model first')
        self.fingerprint = sha256(self.path)
        self.profile = f'litert-lm-api-0.18.0:{self.fingerprint}:dim768:normalized:plain-v1'
        self.engine = litert_lm.EmbeddingEngine(model_path=str(self.path),
                                               backend=litert_lm.Backend.CPU())
        self.options = litert_lm.EmbeddingOptions(normalize=True, output_size=DIMENSIONS)
        self.lock = Lock()

    @property
    def embedding_model_name(self):
        return MODEL_REPO

    def embed_query(self, text):
        # Identical plain-text preprocessing for stored cards and queries.
        with self.lock:
            response = self.engine.compute_embedding(contents=text, options=self.options)
        return validate_vector(response.embedding)

    def close(self):
        self.engine.close()

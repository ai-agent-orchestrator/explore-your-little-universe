from dataclasses import dataclass
import os
from pathlib import Path
from lumi_core import settings
from lumi_core.embedding.litert import MODEL_PATH

@dataclass(frozen=True)
class TarotSettings:
    postgres_dsn: str
    chroma_path: Path
    model_path: Path
    llm: dict

def load_settings():
    settings.load()
    return TarotSettings(settings.postgres(),settings.chroma_path(),
        Path(os.getenv('LUMI_MODEL_PATH',str(MODEL_PATH))),settings.llm())

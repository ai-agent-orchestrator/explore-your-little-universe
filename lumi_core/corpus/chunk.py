"""Shared chunk and plain-v1 embedding input contract."""
import hashlib
from typing import TypedDict, NotRequired

class Chunk(TypedDict):
    id: str
    title: str
    text: str
    category: str
    traits: list[str]
    tips: list[str]
    kind: str
    subject_kind: str
    subject: str
    facet: NotRequired[str]
    document_id: str
    document_title: str
    source: str
    source_url: str
    reviewed_on: str
    editorial_note: str

def embedding_text(chunk: Chunk) -> str:
    return chunk['title'] + '\n' + chunk['text']

def content_hash(chunk: Chunk) -> str:
    return hashlib.sha256(embedding_text(chunk).encode('utf-8')).hexdigest()[:16]

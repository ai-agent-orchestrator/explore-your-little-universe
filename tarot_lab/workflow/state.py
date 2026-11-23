from typing import TypedDict, NotRequired

class ReadingState(TypedDict):
    session_id: str
    question: str
    mbti: str
    zodiac_id: str
    draws: list[dict]
    dataset_version: str
    mapping_version: str
    embedding_profile: str
    graph_paths: list[dict]
    keywords: list[str]
    chunks: list[dict]
    retrieval_comparison: dict
    draft: dict
    validation_errors: list[str]
    rewrite_count: int
    status: str
    error_code: NotRequired[str | None]

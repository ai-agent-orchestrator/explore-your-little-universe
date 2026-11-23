"""Lazy settings; importing this module neither connects nor loads credentials."""
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE = 'mbti-zodiac'

def project_database(value):
    if value != DATABASE:
        raise ValueError(f'NEO4J_DATABASE must be {DATABASE}; restaurant DB is reserved.')
    return value

def load():
    from dotenv import load_dotenv
    for name in ('.env.mbti', '.env.tarot'):
        load_dotenv(ROOT / name, override=False)

@dataclass(frozen=True)
class Neo4jSettings:
    uri: str
    username: str
    password: str
    database: str

def neo4j():
    load()
    if not os.getenv('NEO4J_PASSWORD'):
        raise ValueError('Set NEO4J_PASSWORD in local .env.mbti')
    return Neo4jSettings(os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
                         os.getenv('NEO4J_USERNAME', 'neo4j'), os.environ['NEO4J_PASSWORD'],
                         project_database(os.getenv('NEO4J_DATABASE', DATABASE)))

def postgres():
    load()
    return os.getenv('LUMI_POSTGRES_DSN', '')

def chroma_path():
    load()
    return Path(os.getenv('LUMI_CHROMA_PATH', str(ROOT / 'data/chroma')))

def llm():
    load()
    return {key: os.getenv('LUMI_LLM_' + key.upper(), '') for key in ('base_url','model','api_key')}

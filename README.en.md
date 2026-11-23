# Explore Your Little Universe

[한국어](README.md) | **English**

**A database schema practice project using Neo4j + PostgreSQL + Chroma.** Model MBTI, horoscopes, and tarot readings in the database suited to each responsibility: graph relationships, relational profiles and reading sessions, and interpretation texts with vector embeddings.

<img src="docs/images/lumi.svg" alt="Lumi, a little star companion" width="180">

## 1. Current public Beta — Serverless · Google LiteRT-LM

The current Beta is a static React app for exploring 600 MBTI and zodiac interpretations and scenarios. It uses a public snapshot built in Neo4j and Google LiteRT-LM embedding search in the browser. Lumi is a small guide character.

**[Open the Beta](https://ai-agent-orchestrator.github.io/explore-your-little-universe/)** · [Run and build instructions](docs/STATIC_REACT_RAG.md) · [Corpus and sources](docs/INTERPRETATION_CORPUS.md) · [Previous version v1](https://github.com/ai-agent-orchestrator/explore-your-little-universe/tree/v1)

Use a current Chrome or Edge browser; the first real search downloads a model. The server mode below is a separate next-step design.

## 2. Next step — Tarot + three databases + LangGraph (initial trial design)

**This server mode is a design. Tarot draws, PostgreSQL, Chroma, LangGraph, and a generative LLM are not implemented in the current public Beta.** Extend the MBTI and horoscope model with **78 tarot cards × upright/reversed = 156 meanings**, separating relationships, interpretations, and sessions.

| Component | Data and responsibility |
| --- | --- |
| **PostgreSQL** | Profile snapshots, questions, sessions and draw history, three-card positions and orientations, execution status and reports. PostgreSQL-backed LangGraph checkpoints resume the same session after interruption. |
| **Neo4j** | MBTI, zodiac signs, cards, elements, symbols, and source-backed editorial rules. Bounded 2–3-hop queries return interpretation keywords and evidence paths. |
| **Chroma** | Original interpretation texts and embeddings by orientation and context. Search with the question and graph keywords while filtering by drawn card, orientation, and dataset edition. |
| **LangGraph** | Load confirmed draws → graph lookup → semantic retrieval → draft → validation → save, with bounded rewrites and resume. |
| **React + FastAPI** | Card shuffle/flip presentation, session APIs, and progress events. The server confirms the draw and the UI reveals those same three cards. |

### Database schema practice

| Store | Planned schema and practice |
| --- | --- |
| **PostgreSQL** | `profiles`, `reading_sessions`, `reading_draws`, `reading_reports`, `reading_events`, plus dedicated checkpointer tables. Practice keys, constraints, transactions, profile snapshots, and session resume. |
| **Neo4j** | `MbtiType`, `ZodiacSign`, `SharedTrait`, `TarotCard`, `TarotMeaning`, `Element`, `Archetype`, `InterpretationRule`, and source nodes. Separate 78 card identities from 156 meanings and query evidence paths. |
| **Chroma** | Interpretation texts and embeddings with metadata such as `card_id`, `orientation`, `topic`, `dataset_version`, and `source_url`. Practice ingestion, semantic search, metadata filtering, and source tracing. |

These schemas are planned. See the [detailed schema and trial design](docs/TAROT_3DB_LANGGRAPH_PLAN.md) and [implementation handoff](docs/CLAUDE_TAROT_IMPLEMENTATION.md).

The proposed flow is confirmed draw → graph context → card/direction-filtered retrieval → cited draft → validation → saved report. Rewriting is capped at two attempts; missing evidence ends in a needs-evidence state. Resuming never redraws the cards.

The initial content target is 780 tarot chunks plus the existing 600 texts, for 1,380 total. This is an authoring target, not an implemented corpus. Symbolic readings support reflection and database learning; they are not validated personality, compatibility, or future predictions.

## Neo4j lab — MBTI + 12 zodiac signs

The original graph lab remains available:

- [12 zodiac signs + MBTI graph](docs/ASTROLOGY_LAB.md)
- [Original MBTI web lab](mbti_lab/README.md)
- [Earlier SQLite-based three-database experiment](docs/THREE_DB_COLLAB_PLAN.md) — historical reference; the final design uses PostgreSQL, Neo4j, and Chroma as described above

Use Python 3.12 and a dedicated local Neo4j database named `mbti-zodiac`. See [database separation](docs/DATABASE_SEPARATION.md) and the Korean README for setup. Connection settings stay in local, ignored files.

```cypher
MATCH p = (:MbtiType {code:'INTJ'})-[:HAS_TRAIT]->(:SharedTrait)
          <-[:HAS_TRAIT]-(:ZodiacSign {name:'물병자리'})
RETURN p;
```

The fictional content supports graph-learning and entertainment. It is not an official MBTI test, astrology forecast, compatibility score, diagnosis, or treatment recommendation.

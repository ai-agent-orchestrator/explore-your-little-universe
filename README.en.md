# Explore Your Little Universe

[한국어](README.md) | **English**

**A database schema practice project using Neo4j + PostgreSQL + Chroma.** Model MBTI, horoscopes, and tarot readings in the database suited to each responsibility: graph relationships, relational profiles and reading sessions, and interpretation texts with vector embeddings.

<img src="docs/images/lumi.svg" alt="Lumi, a little star companion" width="480">

## Serverless · Google LiteRT-LM explained

**1. Implementation in progress — improving browser search from the current public Beta.**

The current Beta is a static React app for exploring 600 MBTI and zodiac interpretations and scenarios. It uses a public snapshot built in Neo4j and Google LiteRT-LM embedding search in the browser. Lumi is a small guide character.

**[Open the Beta](https://ai-agent-orchestrator.github.io/explore-your-little-universe/)** · [Run and build instructions](docs/STATIC_REACT_RAG.md) · [Corpus and sources](docs/INTERPRETATION_CORPUS.md) · [Previous version v1](https://github.com/ai-agent-orchestrator/explore-your-little-universe/tree/v1)

Use a current Chrome or Edge browser; the first real search downloads a model. The server mode below is a separate next-step design.

## Tarot + three databases + LangGraph (initial trial design)

**This server mode is a design. Tarot draws, PostgreSQL, Chroma, LangGraph, and a generative LLM are not implemented in the current public Beta.** Extend the MBTI and horoscope model with **78 tarot cards × upright/reversed = 156 meanings**, separating relationships, interpretations, and sessions.

| Component | Data and responsibility |
| --- | --- |
| **PostgreSQL** | Profile snapshots, questions, sessions and draw history, three-card positions and orientations, execution status and reports. PostgreSQL-backed LangGraph checkpoints resume the same session after interruption. |
| **Neo4j** | MBTI, zodiac signs, cards, elements, symbols, and source-backed editorial rules. Bounded 2–3-hop queries return interpretation keywords and evidence paths. |
| **Chroma** | Original interpretation texts and embeddings by orientation and context. Search with the question and graph keywords while filtering by drawn card, orientation, and dataset edition. |
| **LangGraph** | Load confirmed draws → graph lookup → semantic retrieval → draft → validation → save, with bounded rewrites and resume. |
| **React + FastAPI** | Card shuffle/flip presentation, session APIs, and progress events. The server confirms the draw and the UI reveals those same three cards. |

### How one reading connects the stores

The planned server flow starts with a profile such as INTJ / Aquarius and a question about facing change. PostgreSQL answers **who asked what and which cards were drawn**; Neo4j answers **how the selected profile and card meanings connect through symbols and editorial rules**; Chroma answers **which interpretation passages best explain those connections for this question**. Shared identifiers and dataset versions connect the results.

1. **React + FastAPI → PostgreSQL:** Confirm three cards, orientations, and positions on the server. Save the profile snapshot, question, and draw in one transaction. Retries and resume reuse the confirmed draw.
2. **PostgreSQL → Neo4j:** LangGraph loads the session and queries bounded, source-backed paths for the selected MBTI, zodiac sign, and card meanings, returning evidence paths and keywords.
3. **Neo4j → Chroma:** Search with the question and graph keywords. Filter each card's passages by `card_id`, `orientation`, and `dataset_version`; return original text, chunk IDs, and sources.
4. **Chroma → LangGraph:** Generate a grounded draft and validate the three cards, orientations, and citations. Allow at most two rewrites; insufficient evidence ends in a needs-evidence state.
5. **LangGraph → PostgreSQL → React:** Save the final report, evidence IDs, and validation results; deliver progress and results through FastAPI. PostgreSQL-backed checkpoints resume the same session after interruption.

This practices relational keys, constraints, and transactions; graph modeling and path queries; and vector ingestion, retrieval, and metadata filters. Confirm the session first and read a fixed knowledge edition rather than using a distributed transaction across all three stores. These are planned server capabilities.

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

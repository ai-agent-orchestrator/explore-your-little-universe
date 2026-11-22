# Explore Your Little Universe — static GraphRAG lab

[Open the live playground](https://ai-agent-orchestrator.github.io/explore-your-little-universe/)

**A playful daily-action lab inspired by MBTI and astrology.**

Lumi, a little star companion, helps you explore everyday dilemmas and discover one small action. The content is fictional and for entertainment and self-reflection; it is not a personality assessment, compatibility prediction, diagnosis, or treatment.

## Architecture

This is a fully static React application. It requires no Spring server, Python web server, Ollama, paid API, or database credentials at runtime.

1. Offline authoring: Python + LiteRT-LM embed 600 source-informed interpretation and original scenario cards. Neo4j stores the vectors and relationships in the dedicated `mbti-zodiac` database.
2. Export: an allowlisted editorial learning graph is written to `frontend/public/data/graph.json`. The browser receives only public examples and model metadata.
3. Runtime: React loads that snapshot. LiteRT-LM embeds the visitor's question on the device. JavaScript computes cosine similarity and traverses the exported graph.
4. Optional continuation: the visitor copies a grounded prompt and pastes it into Gemini. No Gemini API is integrated and no prompt is automatically sent.

The static app demonstrates vector + graph context expansion. It does **not** benchmark Neo4j query latency during browser use and does not use an LLM to generate an answer.

## Structured + unstructured data

The structured side has 16 MBTI types, 12 zodiac signs, and eight shared traits. The unstructured side contains 600 cards: 60 preserved scenarios, 160 type interpretations, 120 zodiac interpretations, and 260 new everyday examples in 26 additional themes. Profile summaries are short paraphrases of public descriptions; practical applications are authored examples. 16Personalities uses NERIS, distinct from official MBTI. [Corpus sources and validation](INTERPRETATION_CORPUS.md). There are 24 original action suggestions, each backed by specific scenario cards.

```text
MbtiType ──HAS_TRAIT──▶ SharedTrait ◀──HAS_TRAIT── ZodiacSign
                            │
                         FROM_CHUNK
                            ▼
                        RagChunk ──FROM_DOCUMENT──▶ RagDocument
                            ▲
                         FROM_CHUNK
                            │
                          RagTip

SharedTrait ──SUGGESTS──▶ RagTip
```

Graph expansion starts from exactly the same top-three vector results used in the left column. It follows `seed chunk ← trait → another chunk ← suggestion`, excludes the original chunks, and limits the output. Eligible graph paths are ranked by question cosine (75%) and maximum seed cosine (25%), with small boosts for shared/selected traits and direct profile links. The selected type and sign only reorder graph paths; they never alter the vector evidence. Each profile also has ten DESCRIBED_BY links to its interpretation cards. A relationship is not proof that a suggestion answers the question.

## Run React only

Use Node.js 22.12 or later and a current Chrome/Edge browser with WebGPU enabled.

```powershell
cd frontend
npm ci
npm run dev
```

An explicitly marked example appears immediately. The first actual search downloads a pinned model (~165MB), verifies its SHA-256, loads WebGPU/WASM inference, and checks a known probe against the exported native vector. If probe cosine agreement is below 0.995, all 600 cards are re-embedded in the browser before searching, avoiding mixed vector spaces. Model loading, device memory, and browser support affect startup time. Cached model reuse depends on browser storage quota. CPU authoring works natively; the browser currently uses WebGPU because this model's external weights failed to load in the tested WASM CPU path. There is no silent CPU fallback.

The app uses `@litert-lm/core` 0.19.0; native authoring uses `litert-lm-api` 0.18.0. Both use the exact same pinned `embeddinggemma-2-text-270m.litertlm` file, 768 output dimensions, normalized embeddings, and plain-text preprocessing. Changing model, dimensions, or preprocessing requires rebuilding the corpus. Cosine values are not probabilities. Neo4j's vector score is transformed and can differ from the raw cosine displayed in the UI.

## Rebuild the Neo4j corpus and snapshot

The static app does not need these Python steps. They are for editing or inspecting the data in Neo4j.

```powershell
.venv/Scripts/python -m pip install -r requirements-rag.txt
.venv/Scripts/python -m mbti_lab.download_model
# Use local .env.mbti settings. Database must be mbti-zodiac.
.venv/Scripts/python -m mbti_lab.rag_seed
.venv/Scripts/python tools/generate_browser_import.py
.venv/Scripts/python tools/verify_corpus_retrieval.py
```

`ohgi_graph.py` exposes `get_driver()` and `run(driver, cypher, **params)` for the seed/export workflow, explicitly refusing other DB names. No credentials are exported. Model weights are under ignored `models/`. `LiteRTEmbeddings` implements the official `neo4j-graphrag` Embedder interface; the seed script verifies the native Neo4j vector index using `VectorRetriever`. Browser runtime uses neither `GraphRAG` nor the Python retriever, because it has no server.

`MERGE` reuses stable IDs on sequential runs and overwrites vector/content properties. Editing the corpus to remove old traits or tips does not delete historical graph relationships automatically; use a fresh dedicated learning DB for schema changes. Existing unrelated data is not removed. The public snapshot is allowlisted to the 600 explicitly authored card IDs.

Inspect in Neo4j Browser (`:use mbti-zodiac`):

```cypher
MATCH p = (t:SharedTrait)-[:FROM_CHUNK]->(c:RagChunk)
          -[:FROM_DOCUMENT]->(:RagDocument)
WHERE c.id IN ['scenario-25','scenario-26','scenario-01']
RETURN p;
```

Expand a seed into a different evidence card and supported suggestion:

```cypher
MATCH p = (seed:RagChunk {id:'scenario-25'})<-[:FROM_CHUNK]-(t:SharedTrait)
          -[:FROM_CHUNK]->(other:RagChunk)<-[:FROM_CHUNK]-(tip:RagTip)
MATCH (t)-[:SUGGESTS]->(tip)
WHERE other <> seed
RETURN p LIMIT 20;
```

## Weekend validation

Run automated checks first:

```powershell
.venv/Scripts/python -m unittest discover -s mbti_lab -p "test_*.py"
cd frontend
npm test
npm run build
npm run preview
```

Use the same question and compare the two columns. The following are manual relevance checks, not guaranteed rankings:

| Question | Expected topic |
| --- | --- |
| 친구가 갑자기 여행을 가자고 해서 부담스러워 | spontaneous trip, scheduling |
| 친구 답장이 늦으면 내가 잘못했나 신경 쓰여 | delayed replies, checking facts |
| 하고 싶은 일은 많은데 시작을 못 하겠어 | starting a task, small steps |
| 이번 주말은 아무 약속 없이 혼자 쉬고 싶어 | rest, boundaries |
| 여행 일정을 나 혼자 다 짜다가 지쳤어 | sharing responsibilities |
| 내일 비가 와서 여행 계획이 틀어졌어 | changing plans |
| 우주선 연료 가격은 얼마야 | out-of-corpus: nearest results may be irrelevant |

Record first-load wall time separately from warm search time, test mobile layout, confirm that expanded cards are not copies of the vector seeds, and inspect each source/path. Change MBTI/sign while keeping the question fixed: vector results should stay unchanged while graph ordering can change. Open network tools: question text should never appear in a network request. Finally, stop Neo4j and confirm the static app still works.

## Deploy

Build `frontend/dist` and upload it to a static host. Relative asset paths support GitHub Pages project URLs. No `.env` is necessary. Browser inference requires WebGPU, and secure context (HTTPS or localhost) is required for model checksum/clipboard APIs. The runtime chooses a compatible WASM variant, including asyncify for browsers without JSPI. Startup can fail on devices with insufficient WASM memory or unavailable WebGPU; an error is shown while the saved example stays available.

## Initial validation, 2026-11-19

Native LiteRT-LM generated 768-dimensional Korean vectors. Neo4j's official retriever returned a spontaneous-trip card first for the travel probe. Browser WebGPU inference also ran successfully: the trip query took approximately 24ms and the delayed-reply query approximately 77ms after the model was ready on the development PC. The latter returned the delayed-reply card first (cosine about 0.901). These are two warm exploratory observations, not a benchmark or a guaranteed device target. Cold load, relevance over the full question set, and mobile performance remain for weekend validation.

## References

- [LiteRT-LM repository selected for this project](https://github.com/ai-agent-orchestrator/LiteRT-LM)
- [Official embedding model guide](https://developers.google.com/edge/litert-lm/embedding_models)
- [Pinned model repository](https://huggingface.co/litert-community/embeddinggemma-2-text-270m-litert-lm)
- [Neo4j vector indexes](https://neo4j.com/docs/cypher-manual/current/indexes/search-indexes/vector-indexes/)

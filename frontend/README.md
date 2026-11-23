# Explore Your Little Universe — static React app

[Open the public playground](https://ai-agent-orchestrator.github.io/explore-your-little-universe/)

```powershell
npm ci
npm run dev
```

No runtime backend or database credentials are needed. The app uses an exported editorial Neo4j learning graph, Google LiteRT-LM WebGPU embeddings, cosine search, and local graph traversal. WebGPU-enabled Chrome/Edge is required for actual question embeddings. An explicitly marked saved example is always available.

```powershell
npm test
npm run build
npm run preview
```

The `predev`/`prebuild` scripts copy the npm package's WASM runtime into ignored `public/runtime`. The production output is `dist`. All required assets except the pinned public model download are served statically. Questions stay on the device. Read [the full architecture and authoring guide](../docs/STATIC_REACT_RAG.md) for Neo4j seed/export steps and the difference between native DB search and browser search.

The live version includes 600 interpretation/scenario cards with source attribution, 24 suggestions, 16 MBTI Lumi outfits, 12 zodiac color/symbol variants, a relationship graph, an action card, source evidence, copyable Neo4j queries, and optional manually copied Gemini prompts.

## Tarot experience (`src/tarot/`)

`TarotReading` is a React + Motion card flow: shuffle → gold-orbit fan → pick 3 → gather → flip one by one (reversed cards render rotated).

- Cards are chosen by a *draw provider* (`draw.js`), not by the animation. With `VITE_TAROT_API=https://…` the server confirms the 3 cards via `POST /api/readings` (`Idempotency-Key`, draws validated against the deck). Without it the component runs in a clearly labelled **preview mode** with browser-side random cards.
- Assets: `python3 tools/build_tarot_assets.py` rebuilds `public/tarot/` (22 major + 56 minor WebP cards, card back, `deck.json`) from `docs/images/tarot/`. The minor sheets are split by detecting card rectangles; each crop is normalised to 2:3.
- `npm test` includes `src/tarot/draw.test.js`.

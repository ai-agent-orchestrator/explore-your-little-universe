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

// Select your own learning database first. All Lumi relationships, not one proof path.
MATCH p = (a)-[r]->(b)
WHERE type(r) IN ['HAS_TRAIT','FROM_CHUNK','FROM_DOCUMENT','SUGGESTS','DESCRIBED_BY']
  AND any(label IN labels(a) WHERE label IN ['MbtiType','ZodiacSign','SharedTrait','RagChunk','RagTip'])
  AND any(label IN labels(b) WHERE label IN ['SharedTrait','RagChunk','RagTip','RagDocument'])
RETURN p
LIMIT 500;

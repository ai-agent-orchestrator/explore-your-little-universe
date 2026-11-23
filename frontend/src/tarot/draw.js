// Draw helpers for the tarot mode.
// The animation on screen is theatre; the cards come from `drawProvider`.
// - serverDraws(): the server confirms 3 cards (POST /api/readings). Production path.
// - localDraws(): browser-side random preview used only when no server is configured.
//   Its results are NOT server-confirmed and the UI says so.

export const POSITIONS = ['past', 'present', 'future'];
export const POSITION_LABEL = {past: '과거', present: '현재', future: '미래'};
export const ORIENTATION_LABEL = {upright: '정방향', reversed: '역방향'};

function cryptoInt(max, getRandomValues = (a) => crypto.getRandomValues(a)) {
  // uniform integer in [0, max) by rejection sampling
  const limit = Math.floor(0x100000000 / max) * max;
  const buf = new Uint32Array(1);
  do getRandomValues(buf); while (buf[0] >= limit);
  return buf[0] % max;
}

/** Browser-side preview draw: 3 distinct cards, each upright/reversed. `randInt(n)` is injectable for tests. */
export function localDraws(deck, randInt = cryptoInt) {
  const pool = deck.cards.map((c) => c.card_id);
  const out = [];
  for (let i = 0; i < 3; i++) {
    const j = randInt(pool.length);
    const [card_id] = pool.splice(j, 1);
    out.push({card_id, orientation: randInt(2) === 0 ? 'upright' : 'reversed', position: POSITIONS[i], ordinal: i});
  }
  return out;
}

/** Validates a draw list (from any provider) against the deck. Throws on anything unexpected. */
export function normalizeDraws(raw, deck) {
  if (!Array.isArray(raw) || raw.length !== 3) throw new Error('카드 3장이 확정되지 않았습니다.');
  const known = new Set(deck.cards.map((c) => c.card_id));
  const draws = raw.map((d, i) => ({
    card_id: d.card_id,
    orientation: d.orientation,
    position: d.position,
    ordinal: Number.isInteger(d.ordinal) ? d.ordinal : i,
  })).sort((a, b) => a.ordinal - b.ordinal);
  const ids = new Set(draws.map((d) => d.card_id));
  const pos = new Set(draws.map((d) => d.position));
  const ords = new Set(draws.map((d) => d.ordinal));
  if (ids.size !== 3 || pos.size !== 3 || ords.size !== 3) throw new Error('중복된 카드·위치·순서가 있습니다.');
  for (const d of draws) {
    if (!known.has(d.card_id)) throw new Error(`알 수 없는 카드: ${d.card_id}`);
    if (d.orientation !== 'upright' && d.orientation !== 'reversed') throw new Error('방향 값이 올바르지 않습니다.');
    if (!POSITIONS.includes(d.position)) throw new Error('위치 값이 올바르지 않습니다.');
  }
  if (draws.some((d, i) => d.ordinal !== i)) throw new Error('순서는 0~2여야 합니다.');
  return draws;
}

/** Server-confirmed draw. `input` = {mbti, zodiac_id, question, spread}. */
export async function serverDraws({base, deck, input, signal, idempotencyKey, fetchImpl = fetch}) {
  const key = idempotencyKey || (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random());
  const res = await fetchImpl(base.replace(/\/$/, '') + '/api/readings', {
    method: 'POST',
    signal,
    headers: {'Content-Type': 'application/json', 'Idempotency-Key': key},
    body: JSON.stringify({spread: 'three_card_reflection', ...input}),
  });
  if (res.status === 409) throw new Error('같은 요청 키로 다른 입력이 전송됐어요. 다시 시도해주세요.');
  if (!res.ok) throw new Error(`서버가 카드를 확정하지 못했어요 (HTTP ${res.status}).`);
  const body = await res.json();
  return {sessionId: body.session_id, status: body.status, eventsUrl: body.events_url, draws: normalizeDraws(body.draws, deck)};
}

/** Picks the provider from build-time config. VITE_TAROT_API unset → preview mode. */
export function makeProvider(base) {
  if (base) {
    return {mode: 'server', draw: ({deck, input, signal}) => serverDraws({base, deck, input, signal})};
  }
  return {
    mode: 'preview',
    draw: async ({deck}) => ({sessionId: null, draws: normalizeDraws(localDraws(deck), deck)}),
  };
}

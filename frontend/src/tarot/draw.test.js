import test from 'node:test';
import assert from 'node:assert/strict';
import {localDraws, normalizeDraws, serverDraws, makeProvider} from './draw.js';

const deck = {cards: Array.from({length: 78}, (_, i) => ({card_id: 'c' + i}))};

test('localDraws: 3 distinct cards, valid orientation, positions in order', () => {
  for (let n = 0; n < 200; n++) {
    const d = localDraws(deck);
    assert.equal(new Set(d.map((x) => x.card_id)).size, 3);
    assert.deepEqual(d.map((x) => x.position), ['past', 'present', 'future']);
    assert.ok(d.every((x) => ['upright', 'reversed'].includes(x.orientation)));
    normalizeDraws(d, deck);
  }
});

test('localDraws: injectable RNG is deterministic', () => {
  const seq = [0, 0, 0, 1, 0, 0];
  let k = 0;
  const d = localDraws(deck, () => seq[k++]);
  assert.deepEqual(d.map((x) => [x.card_id, x.orientation]), [['c0', 'upright'], ['c1', 'reversed'], ['c2', 'upright']]);
});

test('localDraws: roughly uniform over the deck', () => {
  const counts = new Map();
  for (let n = 0; n < 7800; n++) for (const x of localDraws(deck)) counts.set(x.card_id, (counts.get(x.card_id) || 0) + 1);
  assert.equal(counts.size, 78);
  for (const v of counts.values()) assert.ok(v > 150 && v < 360, 'count ' + v); // mean 300
});

test('normalizeDraws rejects bad input', () => {
  const ok = [0, 1, 2].map((i) => ({card_id: 'c' + i, orientation: 'upright', position: ['past', 'present', 'future'][i], ordinal: i}));
  assert.equal(normalizeDraws(ok, deck).length, 3);
  assert.throws(() => normalizeDraws(ok.slice(0, 2), deck));
  assert.throws(() => normalizeDraws([ok[0], ok[0], ok[2]], deck), /중복/);
  assert.throws(() => normalizeDraws([{...ok[0], card_id: 'zzz'}, ok[1], ok[2]], deck), /알 수 없는/);
  assert.throws(() => normalizeDraws([{...ok[0], orientation: 'sideways'}, ok[1], ok[2]], deck), /방향/);
  assert.throws(() => normalizeDraws([{...ok[0], position: 'later'}, ok[1], ok[2]], deck), /위치/);
});

test('normalizeDraws sorts by ordinal', () => {
  const shuffled = [2, 0, 1].map((i) => ({card_id: 'c' + i, orientation: 'reversed', position: ['past', 'present', 'future'][i], ordinal: i}));
  assert.deepEqual(normalizeDraws(shuffled, deck).map((d) => d.ordinal), [0, 1, 2]);
});

test('serverDraws sends Idempotency-Key, never client-chosen cards, and validates the reply', async () => {
  let seen;
  const fetchImpl = async (url, init) => {
    seen = {url, init};
    return {ok: true, status: 201, json: async () => ({session_id: 's1', status: 'draw_confirmed', events_url: '/e',
      draws: [0, 1, 2].map((i) => ({card_id: 'c' + (i + 5), orientation: 'reversed', position: ['past', 'present', 'future'][i], ordinal: i}))})};
  };
  const r = await serverDraws({base: 'http://x/', deck, input: {mbti: 'INTJ', zodiac_id: 'aquarius', question: 'q'}, fetchImpl, idempotencyKey: 'k1'});
  assert.equal(seen.url, 'http://x/api/readings');
  assert.equal(seen.init.headers['Idempotency-Key'], 'k1');
  assert.deepEqual(Object.keys(JSON.parse(seen.init.body)).sort(), ['mbti', 'question', 'spread', 'zodiac_id']);
  assert.equal(r.sessionId, 's1');
  assert.equal(r.draws[0].card_id, 'c5');
});

test('serverDraws surfaces 409 and HTTP errors', async () => {
  const mk = (status) => async () => ({ok: false, status});
  await assert.rejects(serverDraws({base: 'b', deck, input: {}, fetchImpl: mk(409)}), /다른 입력/);
  await assert.rejects(serverDraws({base: 'b', deck, input: {}, fetchImpl: mk(500)}), /500/);
});

test('makeProvider: preview without base, server with base', async () => {
  assert.equal(makeProvider('').mode, 'preview');
  assert.equal(makeProvider('http://x').mode, 'server');
  const r = await makeProvider('').draw({deck});
  assert.equal(r.draws.length, 3);
});

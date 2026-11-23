import test from 'node:test';
import assert from 'node:assert/strict';
import {
  STAGES, stageIndex, assertSameDraws, normalizeReport, getReading, resumeReading,
  ReadingStream, rememberSession, recallSession, forgetSession, statusMessage,
} from './session.js';

const deck = {cards: Array.from({length: 78}, (_, i) => ({card_id: 'c' + i}))};
const POS = ['past', 'present', 'future'];
const mkDraws = (ids = [1, 2, 3], ori = 'upright') =>
  ids.map((n, i) => ({card_id: 'c' + n, orientation: ori, position: POS[i], ordinal: i}));
const okRes = (body, status = 200) => async () => ({ok: status < 400, status, json: async () => body});

test('stageIndex tracks the furthest stage reached, in any arrival order', () => {
  assert.equal(stageIndex([]), -1);
  assert.equal(stageIndex(['session.created']), 0);
  assert.equal(stageIndex(['graph.completed', 'session.created']), 2);
  assert.equal(stageIndex(['run.failed']), -1);
  assert.equal(stageIndex(STAGES.map((s) => s.key)), STAGES.length - 1);
});

test('assertSameDraws: card immutability across reconnect/resume', () => {
  const a = mkDraws();
  assert.equal(assertSameDraws(null, a), a);
  assert.doesNotThrow(() => assertSameDraws(a, mkDraws()));
  assert.throws(() => assertSameDraws(a, mkDraws([1, 2, 4])), /다른 카드/);
  assert.throws(() => assertSameDraws(a, mkDraws([1, 2, 3], 'reversed')), /다른 카드/);
});

test('normalizeReport accepts text + evidence, rejects empty, maps evidence_ids', () => {
  assert.equal(normalizeReport({}), null);
  assert.equal(normalizeReport({report: '   '}), null);
  const r = normalizeReport({report: '본문', evidence: [{id: 'ch1', title: 'T', source_url: 'u'}, null], model_id: 'm'});
  assert.equal(r.text, '본문');
  assert.deepEqual(r.evidence, [{id: 'ch1', title: 'T', url: 'u'}]);
  assert.equal(r.modelId, 'm');
  assert.deepEqual(normalizeReport({report: 'x', evidence_ids: ['a']}).evidence, [{id: 'a', title: 'a', url: null}]);
});

test('getReading returns draws and only exposes a report once completed', async () => {
  const draws = mkDraws();
  const running = await getReading({base: 'b', sessionId: 's', deck, fetchImpl: okRes({status: 'running', draws, report: '아직'})});
  assert.equal(running.status, 'running');
  assert.equal(running.report, null, '검수 전 본문을 결과로 노출하지 않는다');
  const done = await getReading({base: 'b', sessionId: 's', deck, fetchImpl: okRes({status: 'completed', draws, report: '완성', evidence_ids: ['ch1']})});
  assert.equal(done.report.text, '완성');
});

test('getReading rejects a session whose cards changed', async () => {
  await assert.rejects(getReading({base: 'b', sessionId: 's', deck, previousDraws: mkDraws(),
    fetchImpl: okRes({status: 'completed', draws: mkDraws([9, 8, 7])})}), /다른 카드/);
});

test('getReading maps 404/403/500 to readable errors', async () => {
  for (const [code, re] of [[404, /찾을 수 없/], [403, /권한/], [500, /HTTP 500/]]) {
    await assert.rejects(getReading({base: 'b', sessionId: 's', deck, fetchImpl: okRes({}, code)}), re);
  }
});

test('resumeReading keeps the confirmed cards and surfaces 409', async () => {
  const draws = mkDraws();
  let seen;
  const r = await resumeReading({base: 'b/', sessionId: 's 1', deck, previousDraws: draws,
    fetchImpl: async (url, init) => { seen = {url, method: init.method}; return {ok: true, status: 200, json: async () => ({status: 'running'})}; }});
  assert.equal(seen.url, 'b/api/readings/s%201/resume');
  assert.equal(seen.method, 'POST');
  assert.deepEqual(r.draws, draws);
  await assert.rejects(resumeReading({base: 'b', sessionId: 's', deck, fetchImpl: okRes({}, 409)}), /실행 중/);
  await assert.rejects(resumeReading({base: 'b', sessionId: 's', deck, previousDraws: draws,
    fetchImpl: okRes({status: 'running', draws: mkDraws([5, 6, 7])})}), /다른 카드/);
});

// Minimal EventSource double: records listeners, lets a test emit frames.
class FakeES {
  constructor(url) { this.url = url; this.listeners = {}; this.closedCount = 0; FakeES.last = this; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  close() { this.closedCount++; }
  emit(type, id, data) { for (const fn of this.listeners[type] || []) fn({type, lastEventId: id, data: JSON.stringify(data ?? {})}); }
}

test('ReadingStream: delivers events, drops replays, closes on a terminal event', () => {
  const got = [];
  const s = new ReadingStream({base: 'b', sessionId: 's', EventSourceImpl: FakeES, onEvent: (e) => got.push(e)}).start();
  assert.equal(FakeES.last.url, 'b/api/readings/s/events');
  FakeES.last.emit('session.created', '1', {});
  FakeES.last.emit('draw.confirmed', '2', {draws: mkDraws()});
  FakeES.last.emit('draw.confirmed', '2', {draws: mkDraws()}); // replayed after reconnect
  assert.deepEqual(got.map((e) => e.type), ['session.created', 'draw.confirmed']);
  assert.deepEqual(got[1].payload.draws.length, 3);
  FakeES.last.emit('report.completed', '3', {report: '완성'});
  assert.equal(got.at(-1).type, 'report.completed');
  assert.equal(FakeES.last.closedCount, 1, '종료 이벤트 후 연결을 닫는다');
  FakeES.last.emit('run.failed', '4', {});
  assert.equal(got.length, 3, '닫힌 뒤 이벤트는 무시한다');
  s.close();
});

test('ReadingStream: run.failed is terminal, errors are reported as reconnecting', () => {
  const got = [], errs = [];
  new ReadingStream({base: 'b', sessionId: 's', EventSourceImpl: FakeES, onEvent: (e) => got.push(e), onError: (e, i) => errs.push(i)}).start();
  FakeES.last.onerror();
  assert.deepEqual(errs, [{reconnecting: true}]);
  FakeES.last.emit('run.failed', '9', {error_code: 'db_unavailable'});
  assert.equal(got[0].payload.error_code, 'db_unavailable');
  assert.equal(FakeES.last.closedCount, 1);
});

test('ReadingStream: without EventSource support it errors instead of throwing', () => {
  const errs = [];
  new ReadingStream({base: 'b', sessionId: 's', EventSourceImpl: null, onError: (e) => errs.push(e.message)}).start();
  assert.match(errs[0], /진행 상황/);
});

test('session memory: remember → recall → forget, with expiry and bad data', () => {
  const mem = new Map();
  const storage = {getItem: (k) => (mem.has(k) ? mem.get(k) : null), setItem: (k, v) => mem.set(k, v), removeItem: (k) => mem.delete(k)};
  assert.equal(recallSession(1000, storage), null);
  rememberSession({sessionId: 's1', draws: mkDraws()}, storage);
  assert.equal(recallSession(60000, storage).sessionId, 's1');
  assert.equal(recallSession(-1, storage), null, '오래된 세션은 버린다');
  rememberSession({sessionId: 's2', draws: mkDraws()}, storage);
  forgetSession(storage);
  assert.equal(recallSession(60000, storage), null);
  mem.set('karmic-resonance:last-reading', '{not json');
  assert.equal(recallSession(60000, storage), null);
});

test('statusMessage explains terminal states and appends the error code', () => {
  assert.match(statusMessage('needs_evidence'), /근거/);
  assert.match(statusMessage('failed', 'db_unavailable'), /db_unavailable/);
  assert.equal(statusMessage('running'), '');
});

test('ReadingStream: sinceId skips an earlier attempt’s replayed log', () => {
  const got = [];
  new ReadingStream({base: 'b', sessionId: 's', sinceId: 5, EventSourceImpl: FakeES, onEvent: (e) => got.push(e)}).start();
  assert.equal(FakeES.last.url, 'b/api/readings/s/events?last_event_id=5');
  FakeES.last.emit('run.failed', '5', {});      // the failure that triggered the resume
  FakeES.last.emit('graph.completed', '6', {}); // the new attempt
  assert.deepEqual(got.map((e) => e.type), ['graph.completed']);
  assert.equal(FakeES.last.closedCount, 0, '이전 실패로 새 실행을 끝내지 않는다');
  FakeES.last.emit('report.completed', '9', {report: 'r'});
  assert.equal(got.length, 2);
});

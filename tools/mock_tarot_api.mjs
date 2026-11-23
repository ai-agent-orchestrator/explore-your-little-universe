#!/usr/bin/env node
// Mock of the reading API (docs/TAROT_3DB_LANGGRAPH_PLAN.md §7) for frontend work.
// It implements the contract only — no PostgreSQL, Neo4j, Chroma or LLM.
// Never deploy it: sessions live in memory and there is no ownership check.
//
//   node tools/mock_tarot_api.mjs [--port 8787] [--deck frontend/public/tarot/deck.json]
//
// Scenario per request, so the UI states can be exercised:
//   POST /api/readings { ..., "_scenario": "ok" | "needs_evidence" | "fail_once" | "slow" }
// or, so a browser can trigger one without a custom client, by putting the marker in
// the question itself: "...[needs_evidence]". Test-only; a real server ignores both.

import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {randomUUID, randomInt} from 'node:crypto';

const arg = (name, fallback) => {
  const i = process.argv.indexOf('--' + name);
  return i > 0 ? process.argv[i + 1] : fallback;
};
const PORT = Number(arg('port', 8787));
const deck = JSON.parse(readFileSync(arg('deck', 'frontend/public/tarot/deck.json'), 'utf8'));
const POSITIONS = ['past', 'present', 'future'];

const sessions = new Map(); // session_id → session
const byKey = new Map(); // idempotency key → session_id

/** The server, not the browser, decides the cards: 3 distinct, each with an orientation. */
function confirmDraws() {
  const pool = deck.cards.map((c) => c.card_id);
  return POSITIONS.map((position, ordinal) => ({
    card_id: pool.splice(randomInt(pool.length), 1)[0],
    orientation: randomInt(2) ? 'reversed' : 'upright',
    position,
    ordinal,
  }));
}

const requestHash = (b) => JSON.stringify([b.mbti || '', b.zodiac_id || '', (b.question || '').trim(), b.spread || '']);

function emit(s, event_type, payload = {}) {
  const e = {sequence: s.events.length + 1, event_type, payload, created_at: new Date().toISOString()};
  s.events.push(e);
  for (const res of s.listeners) writeEvent(res, e);
  return e;
}

function writeEvent(res, e) {
  res.write(`id: ${e.sequence}\nevent: ${e.event_type}\ndata: ${JSON.stringify(e.payload)}\n\n`);
}

const REPORT = (draws) => [
  `지금 떠올린 질문을 세 장의 카드로 나눠 읽어볼게요. 과거 자리의 ${draws[0].card_id}는 지금의 고민이 어디에서 시작됐는지를 비춰요.`,
  `현재 자리의 ${draws[1].card_id}는 당신이 지금 어떤 선택지 앞에 서 있는지 보여줘요. ${draws[1].orientation === 'reversed' ? '역방향이라 잠시 속도를 늦추라는 신호로 읽을 수 있어요.' : '정방향이라 지금의 방향을 조금 더 밀고 나가도 좋다는 뜻으로 읽을 수 있어요.'}`,
  `미래 자리의 ${draws[2].card_id}는 정해진 결과가 아니라, 오늘의 작은 한 걸음이 어디로 이어질 수 있는지에 대한 이야기예요. 타로는 예측이 아니라 지금의 마음을 들여다보는 도구라는 점을 기억해주세요.`,
].join('\n\n');

/** Walks a session through the pipeline, emitting the progress events the UI listens for. */
function run(s) {
  if (s.status === 'running') return;
  s.status = 'running';
  const tick = s.scenario === 'slow' ? 2200 : 700;
  const steps = [
    () => emit(s, 'graph.completed', {paths: 4}),
    () => emit(s, 'retrieval.completed', {chunks: 9}),
    () => emit(s, 'draft.validating', {rewrite_count: s.rewrites}),
    () => {
      if (s.scenario === 'needs_evidence') {
        s.status = 'needs_evidence';
        emit(s, 'report.needs_evidence', {error_code: 'insufficient_evidence', resumable: false});
      } else if (s.scenario === 'fail_once' && !s.recovered) {
        s.status = 'failed';
        emit(s, 'run.failed', {error_code: 'llm_unavailable', resumable: true, status: 'failed'});
      } else {
        s.status = 'completed';
        s.report = {report: REPORT(s.draws), evidence: s.draws.map((d, i) => ({id: `chunk_${d.card_id}_${d.orientation}`, title: `${d.card_id} ${d.orientation} 해설`, source_url: `https://example.invalid/${i}`})),
          model_id: 'mock-writer-1', prompt_version: 'mock-v1', completed_at: new Date().toISOString()};
        emit(s, 'report.completed', s.report);
      }
      for (const res of s.listeners) res.end();
      s.listeners.clear();
    },
  ];
  steps.forEach((fn, i) => setTimeout(fn, tick * (i + 1)));
}

const json = (res, code, body) => {
  res.writeHead(code, {'Content-Type': 'application/json; charset=utf-8'});
  res.end(JSON.stringify(body));
};

const server = createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Idempotency-Key');
  if (req.method === 'OPTIONS') { res.writeHead(204); return res.end(); }

  const url = new URL(req.url, 'http://localhost');
  const m = url.pathname.match(/^\/api\/readings(?:\/([^/]+))?(\/events|\/resume)?$/);
  if (!m) return json(res, 404, {error: 'not_found'});
  const [, id, sub] = m;

  if (!id && req.method === 'POST') {
    const key = req.headers['idempotency-key'];
    if (!key) return json(res, 400, {error: 'idempotency_key_required'});
    const body = JSON.parse(await text(req) || '{}');
    const hash = requestHash(body);
    const existing = byKey.get(key);
    if (existing) {
      const s = sessions.get(existing);
      if (s.request_hash !== hash) return json(res, 409, {error: 'idempotency_key_conflict'});
      return json(res, 200, view(s));
    }
    if (body.card_id || body.draws || body.orientation) return json(res, 400, {error: 'client_chosen_cards_not_allowed'});
    const s = {session_id: randomUUID(), request_hash: hash, draws: confirmDraws(), status: 'draw_confirmed',
      events: [], listeners: new Set(), report: null, rewrites: 0, recovered: false,
      scenario: body._scenario || scenarioFromQuestion(body.question) || 'ok'};
    sessions.set(s.session_id, s);
    byKey.set(key, s.session_id);
    emit(s, 'session.created', {});
    emit(s, 'draw.confirmed', {draws: s.draws});
    run(s);
    return json(res, 201, view(s));
  }

  const s = id && sessions.get(id);
  if (!s) return json(res, 404, {error: 'session_not_found'});

  if (sub === '/events' && req.method === 'GET') {
    res.writeHead(200, {'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive'});
    const last = Number(req.headers['last-event-id'] || url.searchParams.get('last_event_id') || 0);
    for (const e of s.events) if (e.sequence > last) writeEvent(res, e);
    if (['completed', 'needs_evidence', 'failed'].includes(s.status)) return res.end();
    s.listeners.add(res);
    req.on('close', () => s.listeners.delete(res));
    return;
  }
  if (sub === '/resume' && req.method === 'POST') {
    if (s.status === 'completed') return json(res, 200, view(s));
    if (s.status === 'running') return json(res, 409, {error: 'already_running'});
    s.recovered = true;
    s.status = 'draw_confirmed';
    run(s);
    return json(res, 202, view(s));
  }
  if (!sub && req.method === 'GET') return json(res, 200, view(s));
  return json(res, 405, {error: 'method_not_allowed'});
});

function view(s) {
  return {
    session_id: s.session_id,
    status: s.status,
    draws: s.draws, // the same cards for the life of the session
    events_url: `/api/readings/${s.session_id}/events`,
    resumable: s.status === 'failed',
    error_code: s.status === 'needs_evidence' ? 'insufficient_evidence' : s.status === 'failed' ? 'llm_unavailable' : null,
    ...(s.status === 'completed' && s.report ? s.report : {}),
  };
}

const scenarioFromQuestion = (q) => (String(q || '').match(/\[(ok|needs_evidence|fail_once|slow)\]/) || [])[1];

const text = (req) => new Promise((resolve) => { let b = ''; req.on('data', (c) => (b += c)); req.on('end', () => resolve(b)); });

server.listen(PORT, '127.0.0.1', () => console.log(`mock tarot API on http://127.0.0.1:${PORT} (${deck.cards.length} cards)`));

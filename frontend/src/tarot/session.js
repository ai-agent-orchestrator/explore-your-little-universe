// Reading session client: status polling, SSE progress, resume.
// Contract: docs/TAROT_3DB_LANGGRAPH_PLAN.md §7.
//
//   GET  /api/readings/{id}         → confirmed draws, run status, report when finished
//   GET  /api/readings/{id}/events  → SSE progress (id = per-session sequence)
//   POST /api/readings/{id}/resume  → re-run a resumable failure with the SAME cards
//
// Two rules this module enforces on the client side:
//  1. Cards never change. A reconnect, resume or reload that returns different
//     cards for the same session is an error, not a new reading (§8 완료 조건).
//  2. Nothing is shown as a result before validation passed. Only `report.completed`
//     carries a report; draft/validating events carry progress only (§7).

import {normalizeDraws} from './draw.js';

/** Ordered progress stages. `key` matches the event type that completes the stage. */
export const STAGES = [
  {key: 'session.created', label: '세션 생성'},
  {key: 'draw.confirmed', label: '카드 확정'},
  {key: 'graph.completed', label: '관계·출처 조회'},
  {key: 'retrieval.completed', label: '해설 검색'},
  {key: 'draft.validating', label: '작성·검수'},
  {key: 'report.completed', label: '리포트 완료'},
];

export const TERMINAL_EVENTS = ['report.completed', 'report.needs_evidence', 'run.failed'];
export const EVENT_TYPES = [...STAGES.map((s) => s.key), 'report.needs_evidence', 'run.failed'];

const STATUS_MESSAGE = {
  needs_evidence: '근거가 충분하지 않아 해설을 완성하지 않았어요. 카드는 그대로 남아 있어요.',
  validation_failed: '검수를 통과하지 못해 해설을 저장하지 않았어요. 카드는 그대로 남아 있어요.',
  failed: '실행 중 문제가 생겼어요.',
};

export function statusMessage(status, errorCode) {
  const base = STATUS_MESSAGE[status] || '';
  return errorCode ? `${base} (${errorCode})`.trim() : base;
}

/** How far the run has progressed, as an index into STAGES (-1 = nothing yet). */
export function stageIndex(eventTypes) {
  let i = -1;
  for (const t of eventTypes) {
    const k = STAGES.findIndex((s) => s.key === t);
    if (k > i) i = k;
  }
  return i;
}

function apiUrl(base, path) {
  return base.replace(/\/$/, '') + path;
}

/** Throws when two draw lists are not the same cards in the same positions. */
export function assertSameDraws(previous, next) {
  if (!previous) return next;
  const key = (d) => `${d.ordinal}:${d.card_id}:${d.orientation}:${d.position}`;
  const a = previous.map(key).join('|');
  const b = next.map(key).join('|');
  if (a !== b) throw new Error('서버가 이 세션에 다른 카드를 반환했어요. 결과를 표시하지 않습니다.');
  return next;
}

/** Report payloads are only trusted when the run actually completed validation. */
export function normalizeReport(body) {
  if (!body || typeof body.report !== 'string' || !body.report.trim()) return null;
  const evidence = Array.isArray(body.evidence) ? body.evidence
    : Array.isArray(body.evidence_ids) ? body.evidence_ids.map((id) => ({id}))
      : [];
  return {
    text: body.report,
    evidence: evidence.filter((e) => e && (e.id || e.chunk_id || e.source_url))
      .map((e) => ({id: e.id || e.chunk_id, title: e.title || e.document_title || e.id || e.chunk_id, url: e.source_url || e.url || null})),
    modelId: body.model_id || null,
    promptVersion: body.prompt_version || null,
    completedAt: body.completed_at || null,
  };
}

/** GET /api/readings/{id} — the authoritative view of a session. */
export async function getReading({base, sessionId, deck, previousDraws, fetchImpl = fetch, signal}) {
  const res = await fetchImpl(apiUrl(base, `/api/readings/${encodeURIComponent(sessionId)}`), {signal});
  if (res.status === 404) throw new Error('세션을 찾을 수 없어요.');
  if (res.status === 401 || res.status === 403) throw new Error('이 세션을 볼 권한이 없어요.');
  if (!res.ok) throw new Error(`세션을 불러오지 못했어요 (HTTP ${res.status}).`);
  const body = await res.json();
  const draws = assertSameDraws(previousDraws, normalizeDraws(body.draws, deck));
  return {
    sessionId: body.session_id || sessionId,
    status: body.status || 'unknown',
    errorCode: body.error_code || null,
    resumable: Boolean(body.resumable),
    draws,
    report: body.status === 'completed' ? normalizeReport(body) : null,
  };
}

/** POST /api/readings/{id}/resume — same cards, same versions, re-run. */
export async function resumeReading({base, sessionId, deck, previousDraws, fetchImpl = fetch, signal}) {
  const res = await fetchImpl(apiUrl(base, `/api/readings/${encodeURIComponent(sessionId)}/resume`), {method: 'POST', signal});
  if (res.status === 409) throw new Error('이미 실행 중인 세션이에요. 잠시 후 다시 시도해주세요.');
  if (!res.ok) throw new Error(`다시 이어가지 못했어요 (HTTP ${res.status}).`);
  const body = await res.json();
  return {
    status: body.status || 'running',
    draws: body.draws ? assertSameDraws(previousDraws, normalizeDraws(body.draws, deck)) : previousDraws,
    report: body.status === 'completed' ? normalizeReport(body) : null,
  };
}

/**
 * SSE progress stream with per-session sequence ids.
 * Duplicates (after a reconnect) are dropped, so replayed events are harmless.
 * The browser's EventSource reconnects on its own and resends Last-Event-ID;
 * `EventSourceImpl` is injectable so the behaviour can be tested without one.
 */
export class ReadingStream {
  constructor({base, sessionId, onEvent, onOpen, onError, EventSourceImpl, maxSeen = 500, sinceId = 0}) {
    // `sinceId` skips the event log a previous attempt left behind: after a resume the
    // server replays the old run's terminal event, which must not end the new run.
    // EventSource cannot set Last-Event-ID on a first connect, so it goes in the query too.
    this.sinceId = Number(sinceId) || 0;
    this.url = apiUrl(base, `/api/readings/${encodeURIComponent(sessionId)}/events`)
      + (this.sinceId ? `?last_event_id=${this.sinceId}` : '');
    this.lastId = this.sinceId;
    this.onEvent = onEvent || (() => {});
    this.onOpen = onOpen || (() => {});
    this.onError = onError || (() => {});
    this.ES = EventSourceImpl || (typeof EventSource !== 'undefined' ? EventSource : null);
    this.seen = new Set();
    this.seenOrder = [];
    this.maxSeen = maxSeen;
    this.closed = false;
    this.es = null;
  }

  start() {
    if (!this.ES) { this.onError(new Error('이 브라우저에서는 진행 상황을 받을 수 없어요.')); return this; }
    this.es = new this.ES(this.url, {withCredentials: true});
    this.es.onopen = () => this.onOpen();
    this.es.onerror = () => { if (!this.closed) this.onError(new Error('진행 연결이 끊겼어요. 다시 연결하는 중이에요…'), {reconnecting: true}); };
    for (const type of EVENT_TYPES) this.es.addEventListener(type, (e) => this._handle(type, e));
    this.es.addEventListener('message', (e) => this._handle(e.type && e.type !== 'message' ? e.type : null, e));
    return this;
  }

  _handle(type, e) {
    if (this.closed) return;
    const id = e.lastEventId || e.id;
    if (id != null && id !== '') {
      const n = Number(id);
      if (Number.isFinite(n)) {
        if (n <= this.sinceId) return; // belongs to an earlier attempt
        if (n > this.lastId) this.lastId = n;
      }
      if (this.seen.has(id)) return; // replayed after reconnect
      this.seen.add(id);
      this.seenOrder.push(id);
      if (this.seenOrder.length > this.maxSeen) this.seen.delete(this.seenOrder.shift());
    }
    let payload = {};
    if (e.data) { try { payload = JSON.parse(e.data); } catch { payload = {raw: e.data}; } }
    const eventType = type || payload.event_type;
    if (!eventType) return;
    this.onEvent({type: eventType, id, payload});
    if (TERMINAL_EVENTS.includes(eventType)) this.close();
  }

  close() {
    this.closed = true;
    if (this.es) { this.es.close(); this.es = null; }
  }
}

const STORE_KEY = 'karmic-resonance:last-reading';

/** Remembers the session so a reload resumes the same cards instead of drawing new ones. */
export function rememberSession(entry, storage = safeStorage()) {
  if (!storage) return;
  try { storage.setItem(STORE_KEY, JSON.stringify({...entry, savedAt: Date.now()})); } catch { /* storage unavailable */ }
}

export function recallSession(maxAgeMs = 6 * 60 * 60 * 1000, storage = safeStorage()) {
  if (!storage) return null;
  try {
    const raw = storage.getItem(STORE_KEY);
    if (!raw) return null;
    const v = JSON.parse(raw);
    if (!v?.sessionId || !Array.isArray(v.draws)) return null;
    if (v.savedAt && Date.now() - v.savedAt > maxAgeMs) { storage.removeItem(STORE_KEY); return null; }
    return v;
  } catch { return null; }
}

export function forgetSession(storage = safeStorage()) {
  if (!storage) return;
  try { storage.removeItem(STORE_KEY); } catch { /* storage unavailable */ }
}

function safeStorage() {
  try { return typeof sessionStorage !== 'undefined' ? sessionStorage : null; } catch { return null; }
}

// Drives one reading run: SSE progress, report delivery, failure/resume.
// Card identity is owned by the draw that opened the session; this hook never
// replaces it — a mismatch from the server is surfaced as an error instead.

import {useCallback, useEffect, useRef, useState} from 'react';
import {
  ReadingStream, getReading, resumeReading, normalizeReport, stageIndex,
  rememberSession, forgetSession, statusMessage,
} from './session.js';

const IDLE = {sessionId: null, status: 'idle', events: [], report: null, error: '', reconnecting: false, resumable: false, errorCode: null};
const POLL_BACKOFF = [6000, 12000, 24000];

export function useReadingRun({apiBase, deck}) {
  const [run, setRun] = useState(IDLE);
  const streamRef = useRef(null);
  const drawsRef = useRef(null);
  const pollRef = useRef({timer: null, tries: 0});
  const lastSeqRef = useRef(0); // highest event sequence seen, so a resume ignores the old run's log
  const aliveRef = useRef(true);
  const activeRef = useRef(null); // session a late response is still allowed to update
  const live = (sessionId) => aliveRef.current && activeRef.current === sessionId;

  useEffect(() => () => { aliveRef.current = false; streamRef.current?.close(); clearTimeout(pollRef.current.timer); }, []);

  const stopPolling = useCallback(() => { clearTimeout(pollRef.current.timer); pollRef.current = {timer: null, tries: 0}; }, []);

  const finish = useCallback((patch) => {
    streamRef.current?.close();
    stopPolling();
    setRun((r) => ({...r, reconnecting: false, ...patch}));
  }, [stopPolling]);

  // Fall back to the status endpoint when the event stream cannot stay connected.
  // poll and schedulePoll call each other, so the pair is held in a ref to keep
  // both free of stale closures.
  const pollFns = useRef({});
  pollFns.current.schedule = (sessionId) => {
    const {tries, timer} = pollRef.current;
    if (timer) return; // a check is already pending; onerror fires on every retry
    if (tries >= POLL_BACKOFF.length) {
      setRun((r) => (r.status === 'running'
        ? {...r, reconnecting: false, error: '진행 상황을 받지 못했어요. 새로고침하면 같은 카드로 이어서 볼 수 있어요.'}
        : r));
      return;
    }
    pollRef.current = {tries: tries + 1, timer: setTimeout(() => {
      pollRef.current = {...pollRef.current, timer: null};
      pollFns.current.poll(sessionId);
    }, POLL_BACKOFF[tries])};
  };
  pollFns.current.poll = async (sessionId) => {
    try {
      const s = await getReading({base: apiBase, sessionId, deck, previousDraws: drawsRef.current});
      if (!live(sessionId)) return;
      if (s.status === 'completed' && s.report) return finish({status: 'completed', report: s.report});
      if (s.status === 'needs_evidence' || s.status === 'validation_failed' || s.status === 'failed') {
        return finish({status: s.status, resumable: s.resumable, errorCode: s.errorCode, error: statusMessage(s.status, s.errorCode)});
      }
      pollFns.current.schedule(sessionId);
    } catch (e) {
      if (!live(sessionId)) return;
      if (/다른 카드/.test(e.message)) return finish({status: 'failed', error: e.message});
      pollFns.current.schedule(sessionId);
    }
  };
  const schedulePoll = useCallback((sessionId) => pollFns.current.schedule(sessionId), []);

  const open = useCallback((sessionId, draws, sinceId = 0) => {
    drawsRef.current = draws;
    activeRef.current = sessionId;
    streamRef.current?.close();
    stopPolling();
    streamRef.current = new ReadingStream({
      base: apiBase,
      sessionId,
      sinceId,
      onOpen: () => { stopPolling(); setRun((r) => ({...r, reconnecting: false})); },
      onError: (e, info) => {
        setRun((r) => ({...r, reconnecting: Boolean(info?.reconnecting)}));
        schedulePoll(sessionId);
      },
      onEvent: ({type, id, payload}) => {
        if (!live(sessionId)) return;
        stopPolling();
        const seq = Number(id);
        if (Number.isFinite(seq) && seq > lastSeqRef.current) lastSeqRef.current = seq;
        setRun((r) => ({...r, reconnecting: false, events: r.events.includes(type) ? r.events : [...r.events, type]}));
        if (type === 'report.completed') {
          const report = normalizeReport(payload);
          if (report) return finish({status: 'completed', report});
          // The event carried no body: ask the status endpoint for the stored report.
          getReading({base: apiBase, sessionId, deck, previousDraws: drawsRef.current})
            .then((s) => live(sessionId) && finish(s.report ? {status: 'completed', report: s.report}
              : {status: 'failed', error: '완성된 해설을 불러오지 못했어요.'}))
            .catch((err) => live(sessionId) && finish({status: 'failed', error: err.message}));
          return;
        }
        if (type === 'report.needs_evidence' || type === 'run.failed') {
          const status = type === 'run.failed' ? (payload.status || 'failed') : 'needs_evidence';
          finish({status, resumable: Boolean(payload.resumable), errorCode: payload.error_code || null,
            error: statusMessage(status, payload.error_code)});
        }
      },
    }).start();
    setRun({...IDLE, sessionId, status: 'running', events: ['session.created', 'draw.confirmed']});
    if (!sinceId) lastSeqRef.current = 0;
    rememberSession({sessionId, draws});
  }, [apiBase, deck, finish, schedulePoll, stopPolling]);

  const resume = useCallback(async () => {
    const sessionId = run.sessionId;
    if (!sessionId) return;
    activeRef.current = sessionId;
    setRun((r) => ({...r, status: 'running', error: '', resumable: false}));
    try {
      const r = await resumeReading({base: apiBase, sessionId, deck, previousDraws: drawsRef.current});
      if (!live(sessionId)) return;
      if (r.status === 'completed' && r.report) return finish({status: 'completed', report: r.report});
      open(sessionId, drawsRef.current, lastSeqRef.current);
    } catch (e) {
      if (live(sessionId)) finish({status: 'failed', error: e.message});
    }
  }, [apiBase, deck, finish, open, run.sessionId]);

  /** Re-attach to a session remembered from a previous page load. */
  const restore = useCallback(async (sessionId, draws) => {
    drawsRef.current = draws;
    activeRef.current = sessionId;
    let s;
    try {
      s = await getReading({base: apiBase, sessionId, deck, previousDraws: draws});
    } catch (e) {
      forgetSession(); // the remembered session is gone or no longer ours
      throw e;
    }
    if (!live(sessionId)) return null;
    if (s.status === 'completed' && s.report) {
      setRun({...IDLE, sessionId, status: 'completed', report: s.report, events: ['report.completed']});
    } else if (s.status === 'running' || s.status === 'draw_confirmed') {
      open(sessionId, s.draws);
    } else {
      setRun({...IDLE, sessionId, status: s.status, resumable: s.resumable, errorCode: s.errorCode,
        error: statusMessage(s.status, s.errorCode) || '이 세션의 해설을 불러오지 못했어요.'});
    }
    return s;
  }, [apiBase, deck, open]);

  const reset = useCallback(() => {
    streamRef.current?.close();
    stopPolling();
    drawsRef.current = null;
    activeRef.current = null;
    lastSeqRef.current = 0;
    forgetSession();
    setRun(IDLE);
  }, [stopPolling]);

  return {run, stage: stageIndex(run.events), open, resume, restore, reset};
}

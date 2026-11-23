import React, {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {motion, useReducedMotion, useMotionValue, useSpring} from 'motion/react';
import {Lumi} from '../Lumi.jsx';
import {makeProvider, POSITIONS, POSITION_LABEL, ORIENTATION_LABEL} from './draw.js';
import {STAGES, recallSession} from './session.js';
import {useReadingRun} from './useReadingRun.js';
import './tarot.css';

// Flow: idle → shuffling → fan → (pick 3) → gathering → revealing → done
// Card identities come from the provider (server-confirmed in production);
// the shuffle and which fan cards the user taps are presentation only.

const GUIDE = {
  idle: '덱을 섞어볼까요? 질문을 떠올리며 시작해요.',
  shuffling: '카드를 섞는 중이에요…',
  fan: '마음이 끌리는 카드 3장을 골라주세요.',
  gathering: '선택한 카드를 모으고 있어요.',
  revealing: '한 장씩 천천히 뒤집어봐요.',
  done: '세 장이 모두 열렸어요.',
};

function useStageSize(ref) {
  const [w, setW] = useState(900);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setW(Math.round(e.contentRect.width)));
    ro.observe(el);
    setW(Math.round(el.clientWidth));
    return () => ro.disconnect();
  }, [ref]);
  return w;
}

/** Fan / stack / slot geometry for a given stage width and card count. */
export function layout(w, count) {
  const cw = Math.round(Math.min(124, Math.max(72, w / 8.2)));
  const ch = Math.round(cw * 1.5);
  const spanDeg = w < 560 ? 32 : 38;
  const span = (spanDeg * Math.PI) / 180;
  const R = Math.min(cw * 4.8, (w / 2 - cw / 2 - 10) / Math.sin(span));
  // vertical extent of the fan (centre card top → outermost rotated card bottom) decides the stage height
  const drop = R * (1 - Math.cos(span));
  const bottom = drop + (ch / 2) * Math.cos(span) + (cw / 2) * Math.sin(span);
  const padTop = Math.round(ch * 0.34 + 14); // room for a lifted (picked) centre card
  const pad = 30;
  const h = Math.round(Math.max(ch * 2.2, padTop + ch / 2 + bottom + pad));
  const y0 = padTop + ch / 2 - h / 2; // centre card's y relative to stage centre
  const fan = Array.from({length: count}, (_, i) => {
    const t = count === 1 ? 0 : (i / (count - 1)) * 2 - 1;
    const a = t * span;
    return {x: R * Math.sin(a), y: R * (1 - Math.cos(a)) + y0, rotate: (a * 180) / Math.PI};
  });
  const slotScale = Math.min(1.38, (w - 24) / (3 * cw * 1.14 + 20));
  const gap = cw * slotScale * 1.12;
  return {cw, ch, R, span, h, y0, fan, slotScale, gap};
}

function Orbit({w, L}) {
  const r = L.R + L.ch * 0.6;
  const cx = w / 2;
  const cy = L.h / 2 + L.y0 + L.R;
  const a = L.span + 0.1;
  const p = (t) => [cx + r * Math.sin(t), cy - r * Math.cos(t)];
  const [x1, y1] = p(-a);
  const [x2, y2] = p(a);
  return (
    <svg className="tarot-orbit" width={w} height={L.h} aria-hidden="true">
      <defs>
        <linearGradient id="orbitGold" x1="0" x2="1">
          <stop offset="0" stopColor="#f6dc8a" stopOpacity="0" />
          <stop offset=".5" stopColor="#f6dc8a" />
          <stop offset="1" stopColor="#f6dc8a" stopOpacity="0" />
        </linearGradient>
      </defs>
      <motion.path d={`M${x1},${y1} A${r},${r} 0 0 1 ${x2},${y2}`} fill="none" stroke="url(#orbitGold)" strokeWidth="2"
        initial={{pathLength: 0, opacity: 0}} animate={{pathLength: 1, opacity: 1}} transition={{duration: 1.4, ease: 'easeOut'}} />
    </svg>
  );
}

function Face({card, reversed}) {
  return (
    <div className="tarot-face tarot-front">
      <img src={import.meta.env.BASE_URL + card.image} alt="" draggable="false" style={reversed ? {transform: 'rotate(180deg)'} : undefined} />
    </div>
  );
}

function TarotCard({i, L, phase, pickOrder, picked, full, card, reversed, flipped, reduce, onPick, onFlip, back, label, disabledPick}) {
  const f = L.fan[i];
  const inFan = phase === 'fan';
  const gathered = phase === 'gathering' || phase === 'revealing' || phase === 'done';
  const stackX = (i - L.fan.length / 2) * 0.35;
  const stackY = (i - L.fan.length / 2) * -0.45;

  let animate; let transition;
  const t = reduce ? {duration: 0.01} : null;
  if (phase === 'idle') {
    animate = {x: stackX, y: stackY, rotate: 0, scale: 1, opacity: 1};
    transition = t || {type: 'spring', stiffness: 160, damping: 20};
  } else if (phase === 'shuffling') {
    const dir = i % 2 ? 1 : -1;
    const amp = reduce ? 0 : L.cw * (0.7 + (i % 5) * 0.08);
    animate = {x: [stackX, dir * amp, dir * amp * 0.2, stackX], y: [stackY, stackY - (i % 4) * 10, stackY - 6, stackY],
      rotate: [0, dir * (7 + (i % 3) * 3), dir * -3, 0], scale: 1, opacity: 1};
    transition = t || {duration: 1.1, delay: (i % 8) * 0.03, repeat: 1, ease: 'easeInOut'};
  } else if (inFan) {
    animate = {x: f.x, y: f.y - (picked ? L.ch * 0.34 : 0), rotate: f.rotate, scale: 1, opacity: 1};
    transition = t || {type: 'spring', stiffness: 110, damping: 16, delay: picked ? 0 : i * 0.03};
  } else if (gathered && pickOrder >= 0) {
    animate = {x: (pickOrder - 1) * L.gap, y: -L.ch * 0.12, rotate: 0, scale: L.slotScale, opacity: 1};
    transition = t || {type: 'spring', stiffness: 80, damping: 15, delay: pickOrder * 0.12};
  } else {
    animate = {x: f.x * 0.6, y: f.y + 120, rotate: f.rotate, scale: 0.85, opacity: 0};
    transition = t || {duration: 0.6};
  }

  // pointer tilt (only for opened cards)
  const rx = useSpring(useMotionValue(0), {stiffness: 200, damping: 18});
  const ry = useSpring(useMotionValue(0), {stiffness: 200, damping: 18});
  const onMove = (e) => {
    if (!flipped || reduce) return;
    const r = e.currentTarget.getBoundingClientRect();
    ry.set(((e.clientX - r.left) / r.width - 0.5) * 22);
    rx.set(-((e.clientY - r.top) / r.height - 0.5) * 22);
  };
  const onLeave = () => { rx.set(0); ry.set(0); };

  const interactive = (inFan && !disabledPick) || ((phase === 'revealing' || phase === 'done') && pickOrder >= 0 && !flipped);
  const handle = inFan ? () => onPick(i) : () => onFlip(pickOrder);
  const hidden = gathered && pickOrder < 0;

  return (
    <motion.div className={'tarot-card' + (picked ? ' picked' : '')} style={{width: L.cw, height: L.ch, marginLeft: -L.cw / 2, marginTop: -L.ch / 2, zIndex: pickOrder >= 0 && gathered ? 10 + pickOrder : i}}
      initial={false} animate={animate} transition={transition}
      whileHover={inFan && !picked && !reduce ? {y: f.y - 26, scale: 1.07, transition: {duration: 0.15}} : undefined}>
      <motion.div className="tarot-tilt" style={{rotateX: rx, rotateY: ry, transformPerspective: 900}} onPointerMove={onMove} onPointerLeave={onLeave}>
        <motion.div className="tarot-flip" initial={false} animate={{rotateY: flipped ? 180 : 0}}
          transition={reduce ? {duration: 0.01} : {duration: 0.95, ease: [0.3, 0.7, 0.2, 1]}}>
          <div className="tarot-face tarot-back"><img src={back} alt="" draggable="false" /></div>
          {card && <Face card={card} reversed={reversed} />}
        </motion.div>
      </motion.div>
      <button type="button" className="tarot-hit" tabIndex={hidden || !(interactive || inFan) ? -1 : 0} disabled={!interactive}
        aria-label={label} aria-pressed={inFan ? picked : undefined} onClick={handle} />
      {pickOrder >= 0 && picked && inFan && <span className="tarot-badge">{pickOrder + 1}</span>}
      {flipped && !reduce && <motion.span className="tarot-glow" initial={{opacity: 0.9, scale: 0.9}} animate={{opacity: 0, scale: 1.5}} transition={{duration: 1.2}} />}
    </motion.div>
  );
}

export function TarotReading({mbti, zodiacId, question, lumiCode = 'ENFP', apiBase = import.meta.env.VITE_TAROT_API || '', onComplete}) {
  const reduce = useReducedMotion();
  const provider = useMemo(() => makeProvider(apiBase), [apiBase]);
  const stageRef = useRef(null);
  const w = useStageSize(stageRef);
  const [deck, setDeck] = useState(null);
  const [phase, setPhase] = useState('idle');
  const [count, setCount] = useState(21);
  const [picks, setPicks] = useState([]);
  const [result, setResult] = useState(null); // {draws, sessionId}
  const [flipped, setFlipped] = useState([false, false, false]);
  const [error, setError] = useState('');
  const abortRef = useRef(null);
  const drawPromise = useRef(null);
  const {run, stage, open, resume, restore, reset: resetRun} = useReadingRun({apiBase, deck});
  const L = useMemo(() => layout(w, count), [w, count]);

  useEffect(() => {
    let live = true;
    fetch(import.meta.env.BASE_URL + 'tarot/deck.json').then((r) => { if (!r.ok) throw Error('deck'); return r.json(); })
      .then((d) => live && setDeck(d)).catch(() => live && setError('카드 데이터를 불러오지 못했어요.'));
    return () => { live = false; abortRef.current?.abort(); };
  }, []);

  // A reload re-attaches to the same session: the cards it confirmed are the cards
  // we show again. A new draw is never requested for an existing session.
  useEffect(() => {
    if (!deck || provider.mode !== 'server' || phase !== 'idle' || result) return;
    const saved = recallSession();
    if (!saved) return;
    let live = true;
    restore(saved.sessionId, saved.draws)
      .then((s) => { if (live && s) { setResult({sessionId: saved.sessionId, draws: s.draws}); setPicks([0, 1, 2]); setFlipped([true, true, true]); setPhase('done'); } })
      .catch(() => {});
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deck, provider.mode]);

  const byId = useMemo(() => new Map((deck?.cards || []).map((c) => [c.card_id, c])), [deck]);
  const needsQuestion = provider.mode === 'server' && !question.trim();

  const start = useCallback(() => {
    if (!deck) return;
    setError(''); setPicks([]); setResult(null); setFlipped([false, false, false]);
    setCount(w < 520 ? 13 : 21);
    abortRef.current?.abort();
    const ctl = new AbortController();
    abortRef.current = ctl;
    // The draw is requested once, up front, and never re-requested (flipping or re-render cannot change it).
    drawPromise.current = provider.draw({deck, signal: ctl.signal, input: {mbti, zodiac_id: zodiacId, question: question.trim()}});
    drawPromise.current.catch(() => {});
    setPhase('shuffling');
  }, [deck, provider, mbti, zodiacId, question, w]);

  // shuffling → fan
  useEffect(() => {
    if (phase !== 'shuffling') return;
    const id = setTimeout(() => setPhase('fan'), reduce ? 400 : 2500);
    return () => clearTimeout(id);
  }, [phase, reduce]);

  // 3 picks → gather (wait for the confirmed draw)
  useEffect(() => {
    if (phase !== 'fan' || picks.length !== 3) return;
    let live = true;
    const id = setTimeout(async () => {
      try {
        const r = await drawPromise.current;
        if (!live) return;
        setResult(r);
        setPhase('gathering');
        if (provider.mode === 'server' && r.sessionId) open(r.sessionId, r.draws);
      } catch (e) {
        if (!live || e?.name === 'AbortError') return;
        setError(e.message || '카드를 확정하지 못했어요.');
        setPhase('idle');
      }
    }, reduce ? 100 : 650);
    return () => { live = false; clearTimeout(id); };
  }, [phase, picks, reduce, provider.mode, open]);

  useEffect(() => {
    if (phase !== 'gathering') return;
    const id = setTimeout(() => setPhase('revealing'), reduce ? 100 : 1300);
    return () => clearTimeout(id);
  }, [phase, reduce]);

  useEffect(() => {
    if (phase === 'revealing' && flipped.every(Boolean)) {
      const id = setTimeout(() => { setPhase('done'); onComplete?.(result); }, reduce ? 100 : 1100);
      return () => clearTimeout(id);
    }
  }, [phase, flipped, reduce, result, onComplete]);

  const pick = (i) => setPicks((p) => (p.includes(i) ? p.filter((x) => x !== i) : p.length < 3 ? [...p, i] : p));
  const flip = (k) => setFlipped((f) => (f[k] ? f : f.map((v, j) => (j === k ? true : v))));
  const nextUnflipped = flipped.findIndex((v) => !v);
  const reset = () => { abortRef.current?.abort(); resetRun(); setPhase('idle'); setPicks([]); setResult(null); setFlipped([false, false, false]); setError(''); };

  const back = import.meta.env.BASE_URL + (deck?.back || 'tarot/back.webp');
  const draws = result?.draws;

  return (
    <section className="tarot-section" aria-labelledby="tarot-title">
      <div className="section-title">
        <div>
          <div className="overline">LUMI'S TAROT · EXPERIMENTAL</div>
          <h2 id="tarot-title">과거 · 현재 · 미래, 세 장의 카드</h2>
        </div>
        <span className="pill">{provider.mode === 'server' ? '서버 확정 뽑기' : '미리보기(연출용)'}</span>
      </div>

      <div className="tarot-guide" role="status" aria-live="polite">
        <Lumi small code={lumiCode} />
        <p>{error || (phase === 'idle' && needsQuestion ? '위에 고민을 먼저 적어주세요. 그 질문으로 카드를 뽑아요.' : GUIDE[phase])}</p>
      </div>

      <div className={'tarot-stage phase-' + phase} ref={stageRef} style={{height: L.h}}>
        <div className="tarot-stars" aria-hidden="true" />
        {phase === 'fan' && <Orbit w={w} L={L} />}
        {deck && Array.from({length: count}, (_, i) => {
          const k = picks.indexOf(i);
          const d = k >= 0 && draws ? draws[k] : null;
          const card = d ? byId.get(d.card_id) : null;
          const gathered = phase === 'gathering' || phase === 'revealing' || phase === 'done';
          const label = phase === 'fan'
            ? `${i + 1}번째 카드 ${k >= 0 ? '선택 취소' : '선택'} (${picks.length}/3 선택됨)`
            : gathered && k >= 0
              ? (flipped[k] ? `${POSITION_LABEL[POSITIONS[k]]} 카드: ${card?.name_ko || card?.name_en}` : `${POSITION_LABEL[POSITIONS[k]]} 카드 뒤집기`)
              : '카드';
          return (
            <TarotCard key={i} i={i} L={L} phase={phase} pickOrder={k} picked={k >= 0} card={card} reversed={d?.orientation === 'reversed'}
              flipped={k >= 0 && flipped[k]} reduce={reduce} back={back} label={label}
              disabledPick={picks.length >= 3 && k < 0} onPick={pick} onFlip={flip} />
          );
        })}
        {(phase === 'revealing' || phase === 'done') && draws && (
          <div className="tarot-slots" style={{top: `calc(50% + ${-L.ch * 0.12 + (L.ch * L.slotScale) / 2 + 12}px)`}}>
            {draws.map((d, k) => (
              <div className={'tarot-slot' + (flipped[k] ? ' open' : '')} key={d.position} style={{width: L.gap - 6, left: `calc(50% + ${(k - 1) * L.gap}px)`}}>
                <b>{POSITION_LABEL[d.position]}</b>
                {flipped[k] && <span>{byId.get(d.card_id)?.name_ko || byId.get(d.card_id)?.name_en}<small>{ORIENTATION_LABEL[d.orientation]}</small></span>}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="tarot-actions">
        {phase === 'idle' && <button className="primary" disabled={!deck || needsQuestion} onClick={start}>{error ? '다시 시도' : '카드 섞기'}</button>}
        {phase === 'fan' && <button className="tarot-ghost" disabled={!picks.length} onClick={() => setPicks([])}>선택 비우기 ({picks.length}/3)</button>}
        {phase === 'revealing' && nextUnflipped >= 0 && <button className="primary" onClick={() => flip(nextUnflipped)}>{POSITION_LABEL[POSITIONS[nextUnflipped]]} 카드 뒤집기</button>}
        {phase === 'done' && <button className="tarot-ghost" onClick={reset}>처음부터 다시</button>}
      </div>

      {phase === 'done' && draws && (
        <ol className="tarot-summary">
          {draws.map((d) => {
            const c = byId.get(d.card_id);
            return (
              <li key={d.position}>
                <span className="tarot-pos">{POSITION_LABEL[d.position]}</span>
                <b>{c?.name_ko || c?.name_en}</b>{c?.name_ko && <em>{c.name_en}</em>}
                <span className={'tarot-ori ' + d.orientation}>{ORIENTATION_LABEL[d.orientation]}</span>
              </li>
            );
          })}
        </ol>
      )}

      {provider.mode === 'server' && run.status !== 'idle' && (
        <section className="tarot-run">
          <ol className="tarot-steps" aria-label="해설 생성 진행">
            {STAGES.map((st, i) => {
              const done = i <= stage;
              const current = !done && i === stage + 1 && run.status === 'running';
              return (
                <li key={st.key} className={done ? 'done' : current ? 'current' : ''} aria-current={current ? 'step' : undefined}>
                  <span className="tarot-dot" aria-hidden="true" />{st.label}
                  <span className="tarot-sr">{done ? ' 완료' : current ? ' 진행 중' : ' 대기'}</span>
                </li>
              );
            })}
          </ol>
          <p className="tarot-run-status" role="status" aria-live="polite">
            {run.reconnecting ? '연결이 끊겨 다시 연결하는 중이에요. 카드는 그대로예요.'
              : run.status === 'running' ? '루미가 근거를 모아 해설을 쓰고 있어요…'
                : run.error || (run.report ? '해설이 완성됐어요.' : '')}
          </p>
          {run.resumable && <button className="tarot-ghost" onClick={resume}>같은 카드로 다시 이어가기</button>}
        </section>
      )}

      {run.report && (
        <article className="tarot-report">
          <h3>루미의 해설</h3>
          {run.report.text.split(/\n{2,}/).map((para, i) => <p key={i}>{para}</p>)}
          {run.report.evidence.length > 0 && (
            <details>
              <summary>근거 {run.report.evidence.length}개 · 출처 보기</summary>
              <ul>
                {run.report.evidence.map((e) => (
                  <li key={e.id}>{e.url ? <a href={e.url} target="_blank" rel="noreferrer">{e.title}</a> : e.title}</li>
                ))}
              </ul>
            </details>
          )}
          {run.report.modelId && <p className="fine">생성 모델 {run.report.modelId}{run.report.promptVersion ? ` · 프롬프트 ${run.report.promptVersion}` : ''}</p>}
        </article>
      )}

      <p className="fine tarot-note">
        {provider.mode === 'server'
          ? '이 모드는 질문·MBTI·별자리를 서버로 전송하고 세션 기록이 저장됩니다. 카드는 서버가 한 번만 확정하며 뒤집기·새로고침으로 바뀌지 않아요. 타로는 재미와 성찰을 위한 도구이며 예측·진단이 아닙니다.'
          : '미리보기 모드예요. 서버가 연결되지 않아 카드는 이 브라우저에서 임의로 뽑은 연출용이며 질문은 어디에도 전송되지 않아요. 카드별 해설은 서버 연결 후 제공됩니다. 타로는 재미와 성찰을 위한 도구이며 예측·진단이 아닙니다.'}
      </p>
    </section>
  );
}

export default TarotReading;

// The Assistant: questions about the method and, if the planner agrees for this session, about
// summaries of their results (docs/FLEXIBLE_ANALYSIS.md section 5). A modal sheet over the open
// project, so nothing on the step underneath changes.
//
// What it does, in order:
//  - says plainly what it can and cannot see;
//  - asks once per session before sharing anything beyond the question and where the planner is,
//    showing exactly what would be sent, with any column or group left out on request;
//  - shows when it cannot answer (switched off, this month's limit reached, offline, the
//    stand-in engine) and why, while everything else keeps working;
//  - fills numbers from what was sent, strikes through any it cannot match, and does not show an
//    answer that claims a cause.

import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { create } from 'zustand';
import { getEngine } from '../engine/client';
import type { Explanation } from '../engine/protocol';
import { useExplore } from '../explore/exploreStore';
import { useSession } from '../state/store';
import { claimsCause, numbersIn, numbersInText, renderAnswer, type Piece } from './answer';
import { ask, AssistantRefusal, fetchStatus, newSessionId, type Status, type Turn } from './client';
import { buildContext, LIMITS, sanitizeLabel, type Context, type PayloadInputs, type ShareChoice } from './payload';


// ---------------------------------------------------------------- state for this page session

interface Answer extends Turn {
  /** What the question carried, to fill placeholders from exactly that. */
  context?: Context;
  question?: string;
  methodNumbers?: number[];
  streaming?: boolean;
  /** Not shown: it claimed a cause. */
  causal?: boolean;
  failed?: string;
}

type Reach = { kind: 'checking' } | { kind: 'status'; status: Status } | { kind: 'unreachable' } | { kind: 'offline' } | { kind: 'stand-in' };

interface AssistantState {
  session: string;
  turns: Answer[];
  busy: boolean;
  /** The planner's agreement for this session: what to include, and the exact JSON they saw. */
  consent: { choice: ShareChoice; siteId: string | null; seen: string } | null;
  site: { id: string; explanation: Explanation } | null;
  deeper: boolean;
}

const useAssistant = create<AssistantState>(() => ({
  session: newSessionId(),
  turns: [],
  busy: false,
  consent: null,
  site: null,
  deeper: false,
}));

function useInputs(): PayloadInputs {
  const step = useSession((s) => s.step);
  const table = useSession((s) => s.table);
  const run = useSession((s) => s.run);
  const columns = useSession((s) => s.columns);
  const indexRun = useSession((s) => s.indexResult);
  const exploreResult = useExplore((s) => (s.status === 'done' ? s.result : null));
  const exploreEntries = useExplore((s) => s.entries);
  const site = useAssistant((s) => s.site);
  return useMemo(() => {
    const confidence = site && run ? run.sites.find((x) => x.siteId === site.id)?.confidence.level ?? null : null;
    return {
      step, table, run,
      engine: getEngine().kind === 'mock' ? 'stand-in' : 'real',
      entries: columns?.entries ?? (exploreEntries.length ? exploreEntries : null),
      explore: exploreResult,
      index: indexRun?.result ?? null,
      site: site?.explanation ?? null,
      siteConfidence: confidence,
    };
  }, [step, table, run, columns, indexRun, exploreResult, exploreEntries, site]);
}

const pretty = (v: unknown) => JSON.stringify(v, null, 2);

function resumeDate(iso?: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', timeZone: 'UTC' });
}

// ---------------------------------------------------------------- pieces

function StatusLine({ reach }: { reach: Reach }) {
  if (reach.kind === 'checking') return <p className="as-status" role="status">Checking whether the assistant can answer.</p>;
  if (reach.kind === 'stand-in') {
    return <p className="as-status as-status--calm" role="status">The assistant is not available with the sample stand-in engine. Everything else in the planner works as usual.</p>;
  }
  if (reach.kind === 'offline') {
    return <p className="as-status as-status--calm" role="status">You are offline. The assistant needs a connection; everything else in the planner keeps working on this device.</p>;
  }
  if (reach.kind === 'unreachable') {
    return <p className="as-status as-status--calm" role="status">The assistant could not be reached just now. Everything else in the planner keeps working.</p>;
  }
  const s = reach.status;
  if (s.state === 'available') {
    const used = Math.round(s.usedShare * 100);
    return <p className="as-status" role="status">Available. About {used}% of this month's limit is used.</p>;
  }
  if (s.state === 'paused' && s.scope === 'month') {
    const when = resumeDate(s.resumes);
    return (
      <div className="as-status as-status--paused" role="status">
        <p className="as-status__title">The assistant has reached this month's limit</p>
        <p>It starts again {when ? `on ${when}` : 'next month'}. Everything else in the planner keeps working.</p>
      </div>
    );
  }
  if (s.state === 'paused' && s.scope === 'day') {
    return (
      <div className="as-status as-status--paused" role="status">
        <p className="as-status__title">The assistant has reached today's limit</p>
        <p>It starts again tomorrow. Everything else in the planner keeps working.</p>
      </div>
    );
  }
  return <p className="as-status as-status--paused" role="status">{s.message}</p>;
}

function WhatItSees() {
  return (
    <details className="as-sees">
      <summary className="hig-focus">What the Assistant Can and Cannot See</summary>
      <div className="as-sees__body">
        <h4>Always</h4>
        <p>Your question, this conversation, EV-SIENT's method and common questions, which step you are on, and your file's size (rows and columns).</p>
        <h4>Only if you agree, for this session</h4>
        <p>Summaries the planner already worked out: column headers and what each column holds, the share of blanks, a rough count of different values, rounded 10th, 50th and 90th percentiles (never the smallest or largest value), category labels with their counts (any group under 10 left out), sites per tier, Explore patterns, Your Index settings, and one site's score breakdown, renamed Site A. You see exactly what would be sent first, and can leave out any column.</p>
        <h4>Never</h4>
        <p>Rows or any single cell, sample values, site names, IDs, addresses, coordinates, notes or other free text, your own columns' values for any site, or your file's name.</p>
        <p className="as-fine">Questions go to Claude on Amazon Bedrock with data retention switched off, so they are not stored by AWS or Anthropic. The assistant gives planning support, not engineering advice.</p>
      </div>
    </details>
  );
}

function Pieces({ pieces }: { pieces: Piece[] }) {
  return (
    <>
      {pieces.map((p, i) => {
        if (p.kind === 'text') return <span key={i}>{p.text}</span>;
        if (p.kind === 'value') return <span key={i} className="as-value" title="Filled in from what was shared">{p.text}</span>;
        if (p.kind === 'missing') return <span key={i} className="as-missing">(value not available)</span>;
        return <del key={i} className="as-unverified">{p.text}<span className="hig-visually-hidden"> (unverified)</span></del>;
      })}
    </>
  );
}

function AnswerView({ turn }: { turn: Answer }) {
  const shown = useMemo(() => {
    if (turn.causal) return null;
    const allowed = [
      ...numbersIn(turn.context ?? {}),
      ...numbersInText(turn.question ?? ''),
      ...(turn.methodNumbers ?? []),
    ];
    return renderAnswer(turn.text, turn.context ?? {}, allowed);
  }, [turn.text, turn.context, turn.question, turn.methodNumbers, turn.causal]);
  if (turn.failed) return <p className="as-answer__note">{turn.failed}</p>;
  if (turn.causal) {
    return <p className="as-answer__note">This answer described a cause, which your data cannot show, so it is not shown. Ask about patterns or what goes together instead.</p>;
  }
  const unverified = shown?.some((p) => p.kind === 'unverified');
  const paragraphs: Piece[][] = [[]];
  for (const p of shown ?? []) {
    if (p.kind !== 'text') { paragraphs[paragraphs.length - 1].push(p); continue; }
    const parts = p.text.split(/\n{2,}/);
    parts.forEach((part, i) => {
      if (i > 0) paragraphs.push([]);
      if (part) paragraphs[paragraphs.length - 1].push({ kind: 'text', text: part });
    });
  }
  return (
    <>
      {paragraphs.map((ps, i) => <p key={i} className="as-answer__p"><Pieces pieces={ps} /></p>)}
      {turn.streaming && <p className="as-answer__note" aria-hidden="true">Writing</p>}
      {!turn.streaming && unverified && (
        <p className="as-answer__note">Struck-through numbers did not match anything that was shared, so check them before you use them.</p>
      )}
    </>
  );
}

// ---------------------------------------------------------------- sharing (consent)

function ShareReview({ inputs, onDone }: { inputs: PayloadInputs; onDone: () => void }) {
  const consent = useAssistant((s) => s.consent);
  const site = useAssistant((s) => s.site);
  const [choice, setChoice] = useState<ShareChoice>(consent?.choice ?? {
    columns: !!inputs.table, readiness: !!inputs.run, explore: !!inputs.explore, index: !!inputs.index, site: false, withheld: [],
  });
  const [siteId, setSiteId] = useState<string>(consent?.siteId ?? site?.id ?? '');
  const [siteError, setSiteError] = useState<string | null>(null);

  useEffect(() => {
    if (!choice.site || !siteId || site?.id === siteId) return;
    let live = true;
    getEngine().explain(siteId).then(
      (explanation) => { if (live) { useAssistant.setState({ site: { id: siteId, explanation } }); setSiteError(null); } },
      () => { if (live) setSiteError('That site\'s breakdown could not be read.'); },
    );
    return () => { live = false; };
  }, [choice.site, siteId, site?.id]);

  const effective: ShareChoice = { ...choice, site: choice.site && !!siteId && site?.id === siteId };
  const context = buildContext(inputs, effective);
  const preview = pretty(context);
  const set = (patch: Partial<ShareChoice>) => setChoice((c) => ({ ...c, ...patch }));
  const toggleColumn = (name: string, withhold: boolean) =>
    set({ withheld: withhold ? [...choice.withheld, name] : choice.withheld.filter((n) => n !== name) });

  const agree = () => {
    useAssistant.setState({ consent: { choice: effective, siteId: effective.site ? siteId : null, seen: JSON.stringify(context.shared ?? null) } });
    onDone();
  };

  const groups: { key: keyof Omit<ShareChoice, 'withheld'>; label: string; available: boolean }[] = [
    { key: 'columns', label: 'Column summaries', available: !!inputs.table },
    { key: 'readiness', label: 'Readiness results (sites per tier)', available: !!inputs.run },
    { key: 'explore', label: 'Explore patterns', available: !!inputs.explore },
    { key: 'index', label: 'Your Index settings', available: !!inputs.index },
    { key: 'site', label: "One site's score breakdown, sent as Site A", available: !!inputs.run },
  ];

  return (
    <section className="as-review" aria-labelledby="as-review-title">
      <h3 id="as-review-title" className="as-h3">What Would Be Shared</h3>
      <fieldset className="as-fieldset">
        <legend>Include</legend>
        {groups.map((g) => (
          <label key={g.key} className="as-check">
            <input type="checkbox" checked={choice[g.key] && g.available} disabled={!g.available} onChange={(e) => set({ [g.key]: e.target.checked })} />
            <span>{g.label}{!g.available ? ' (nothing yet)' : ''}</span>
          </label>
        ))}
        {choice.site && inputs.run && (
          <label className="as-select">
            <span>Site to explain</span>
            <select className="hig-focus" value={siteId} onChange={(e) => setSiteId(e.target.value)}>
              <option value="">Choose a site</option>
              {inputs.run.sites.map((s) => <option key={s.siteId} value={s.siteId}>{s.name || s.siteId}</option>)}
            </select>
            <span className="as-fine">Its name and ID stay on this device; only its score and drivers are sent, as Site A.</span>
          </label>
        )}
        {siteError && <p className="as-fine" role="alert">{siteError}</p>}
      </fieldset>
      {choice.columns && inputs.table && (
        <fieldset className="as-fieldset">
          <legend>Columns to leave out</legend>
          <div className="as-columns">
            {inputs.table.columns.map((name, i) => (
              <label key={`${i}-${name}`} className="as-check">
                <input type="checkbox" checked={choice.withheld.includes(name)} onChange={(e) => toggleColumn(name, e.target.checked)} />
                <span>{sanitizeLabel(name) || `Column ${i + 1}`}</span>
              </label>
            ))}
          </div>
        </fieldset>
      )}
      <h4 className="as-h4" id="as-preview-title">Exactly what is sent with each question</h4>
      <p className="as-fine">Besides your question and this conversation's earlier questions and answers, this is everything:</p>
      <pre className="as-preview" tabIndex={0} aria-labelledby="as-preview-title">{preview}</pre>
      <div className="as-actions">
        <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered-prominent hig-focus" onClick={agree}>
          <span className="hig-button__label">Share for This Session</span>
        </button>
        <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus" onClick={onDone}>
          <span className="hig-button__label">Cancel</span>
        </button>
      </div>
    </section>
  );
}

function ShareSummary({ stale, onReview }: { stale: boolean; onReview: () => void }) {
  const consent = useAssistant((s) => s.consent);
  if (!consent) {
    return (
      <section className="as-share" aria-label="Sharing">
        <p>Nothing from your results is shared. The assistant sees your question, which step you are on and your file's size.</p>
        <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus" onClick={onReview}>
          <span className="hig-button__label">Review What Would Be Shared</span>
        </button>
      </section>
    );
  }
  const c = consent.choice;
  const parts = [
    c.columns && 'column summaries', c.readiness && 'readiness results', c.explore && 'Explore patterns',
    c.index && 'Your Index settings', c.site && "one site's breakdown (as Site A)",
  ].filter(Boolean) as string[];
  return (
    <section className="as-share" aria-label="Sharing">
      <p>Shared for this session: {parts.length ? parts.join(', ') : 'nothing'}{c.withheld.length ? `, leaving out ${c.withheld.length} column${c.withheld.length === 1 ? '' : 's'}` : ''}.</p>
      {stale && <p className="as-share__stale" role="status">Your results changed since you agreed, so nothing from them is shared until you review it again.</p>}
      <div className="as-actions">
        <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus" onClick={onReview}>
          <span className="hig-button__label">Review or Change</span>
        </button>
        <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--borderless hig-focus" onClick={() => useAssistant.setState({ consent: null })}>
          <span className="hig-button__label">Stop Sharing</span>
        </button>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- the dialog

export function AssistantPanel({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const inputs = useInputs();
  const { turns, busy, consent, deeper, session } = useAssistant();
  const [reach, setReach] = useState<Reach>({ kind: 'checking' });
  const [reviewing, setReviewing] = useState(false);
  const [question, setQuestion] = useState('');
  const [announce, setAnnounce] = useState('');

  useEffect(() => { if (ref.current && !ref.current.open) ref.current.showModal(); }, []);

  // Where the assistant stands: never asked over the network with the stand-in engine or offline.
  const refresh = useMemo(() => async () => {
    if (getEngine().kind === 'mock') { setReach({ kind: 'stand-in' }); return; }
    if (!navigator.onLine) { setReach({ kind: 'offline' }); return; }
    setReach({ kind: 'checking' });
    try { setReach({ kind: 'status', status: await fetchStatus() }); } catch { setReach({ kind: 'unreachable' }); }
  }, []);
  useEffect(() => {
    void refresh();
    const on = () => void refresh();
    window.addEventListener('online', on);
    window.addEventListener('offline', on);
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', on); };
  }, [refresh]);

  const sharedNow = consent ? buildContext(inputs, consent.choice).shared : undefined;
  const stale = !!consent && JSON.stringify(sharedNow ?? null) !== consent.seen;
  const canAsk = reach.kind === 'status' && reach.status.state === 'available' && !busy;
  const full = turns.length >= LIMITS.historyTurns + 2;

  async function submit(e: FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || !canAsk || full) return;
    const context: Context = consent && !stale && sharedNow ? { app: buildContext(inputs, null).app, shared: sharedNow } : buildContext(inputs, null);
    // Earlier questions with their answers. A failed or hidden answer is dropped with its
    // question, so turns keep alternating and nothing the planner did not see is sent back.
    const clean: Turn[] = [];
    for (let i = 0; i + 1 < turns.length; i += 2) {
      const [u, a] = [turns[i], turns[i + 1]];
      if (u.role === 'user' && a.role === 'assistant' && !a.failed && !a.causal && a.text) {
        clean.push({ role: 'user', text: u.text }, { role: 'assistant', text: a.text });
      }
    }
    const user: Answer = { role: 'user', text: q };
    const answer: Answer = { role: 'assistant', text: '', context, question: q, streaming: true };
    useAssistant.setState({ busy: true, turns: [...turns, user, answer] });
    setQuestion('');
    setAnnounce('');
    const update = (patch: Partial<Answer>) => useAssistant.setState((s) => {
      const next = s.turns.slice();
      next[next.length - 1] = { ...next[next.length - 1], ...patch };
      return { turns: next };
    });
    let text = '';
    try {
      await ask({ v: 1, session, question: q, history: clean.slice(-LIMITS.historyTurns), context, ...(deeper ? { deeper: true } : {}) }, (ev) => {
        if (ev.t === 'meta') update({ methodNumbers: ev.methodNumbers });
        else if (ev.t === 'text') { text += ev.v; update({ text }); }
        else if (ev.t === 'error') update({ failed: ev.message });
      });
      const causal = claimsCause(text);
      update({ streaming: false, causal, text: text.slice(0, LIMITS.assistantChars), ...(text ? {} : { failed: 'The assistant gave no answer. Try asking again.' }) });
      setAnnounce(causal ? 'The answer described a cause, so it is not shown.' : 'Answer ready.');
    } catch (err) {
      const message = err instanceof AssistantRefusal ? err.message : 'The assistant could not be reached. Everything else in the planner keeps working.';
      update({ streaming: false, failed: message });
      setAnnounce(message);
      if (err instanceof AssistantRefusal && (err.code === 'cap' || err.code === 'off')) void refresh();
    } finally {
      useAssistant.setState({ busy: false });
    }
  }

  return (
    <dialog
      ref={ref}
      className="as-sheet"
      aria-labelledby="as-title"
      onClose={onClose}
      onClick={(e) => { if (e.target === ref.current) ref.current.close(); }}
    >
      <div className="as-sheet__head">
        <h2 id="as-title" className="as-sheet__title">Assistant</h2>
        <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--borderless hig-focus" onClick={() => ref.current?.close()}>
          <span className="hig-button__label">Done</span>
        </button>
      </div>
      <div className="as-sheet__body">
        <StatusLine reach={reach} />
        <WhatItSees />
        {reviewing
          ? <ShareReview inputs={inputs} onDone={() => setReviewing(false)} />
          : <ShareSummary stale={stale} onReview={() => setReviewing(true)} />}

        {turns.length > 0 && (
          <ol className="as-log" aria-label="Conversation">
            {turns.map((t, i) => (
              <li key={i} className={`as-turn as-turn--${t.role}`} aria-busy={t.streaming || undefined}>
                <p className="as-turn__who">{t.role === 'user' ? 'You' : 'Assistant'}</p>
                {t.role === 'user' ? <p className="as-answer__p">{t.text}</p> : <AnswerView turn={t} />}
              </li>
            ))}
          </ol>
        )}
        <p className="hig-visually-hidden" role="status" aria-live="polite">{announce}</p>
      </div>
      <form className="as-ask" onSubmit={submit}>
        <label htmlFor="as-question" className="as-ask__label">Your Question</label>
        <textarea
          id="as-question"
          className="as-ask__input hig-focus"
          rows={2}
          maxLength={LIMITS.questionChars}
          value={question}
          disabled={!canAsk || full}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); e.currentTarget.form?.requestSubmit(); } }}
          aria-describedby="as-ask-note"
        />
        <div className="as-ask__row">
          {reach.kind === 'status' && reach.status.state === 'available' && reach.status.deeper && (
            <label className="as-check">
              <input type="checkbox" checked={deeper} onChange={(e) => useAssistant.setState({ deeper: e.target.checked })} />
              <span>Deeper Answer</span>
            </label>
          )}
          {turns.length > 0 && (
            <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--borderless hig-focus" disabled={busy}
              onClick={() => useAssistant.setState({ turns: [] })}>
              <span className="hig-button__label">New Conversation</span>
            </button>
          )}
          <button type="submit" className="hig-button hig-button--ios hig-button--medium hig-button--bordered-prominent hig-focus" disabled={!canAsk || full || !question.trim()}>
            <span className="hig-button__label">{busy ? 'Asking' : 'Ask'}</span>
          </button>
        </div>
        <p id="as-ask-note" className="as-fine">
          {full ? 'This conversation has reached its length. Start a new conversation to ask more. ' : ''}
          Planning support, not engineering advice. Answers can be wrong: numbers are checked against what was shared.
        </p>
      </form>
    </dialog>
  );
}

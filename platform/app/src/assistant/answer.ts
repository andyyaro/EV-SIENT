// Turning the model's answer into what the planner reads (docs/FLEXIBLE_ANALYSIS.md section 5:
// "answers write numbers as placeholders filled from tool results, and any number that does not
// match a tool result is struck through; causal verbs are refused").
//
// 1. Placeholders. The model writes [[shared.columns.2.p50]] instead of a number from the data;
//    the value is filled here from exactly what was sent, so it cannot be misquoted.
// 2. The number check. Any number the model typed itself must match a number that was sent, one
//    in the planner's question, or one written in the method. Anything else is shown struck
//    through and marked unverified.
// 3. Causal claims. An answer that says one thing causes another is not shown.
//
// Pure functions and no runtime imports, so Node runs this file in the tests.

export type Piece =
  | { kind: 'text'; text: string }
  | { kind: 'value'; text: string; path: string }
  | { kind: 'missing'; path: string }
  | { kind: 'unverified'; text: string };

const PLACEHOLDER = /\[\[([A-Za-z0-9_.]{1,120})\]\]/g;
// Numbers as people write them: 1,234.5 or 1234.5 or .5, with an optional sign.
const NUMBER = /(?<![\w.])-?(?:\d{1,3}(?:,\d{3})+|\d+)?(?:\.\d+)?(?![\w])/g;

function roundSig(x: number, digits: number): number {
  if (!Number.isFinite(x) || x === 0) return x === 0 ? 0 : x;
  return Number(x.toPrecision(digits));
}

/** A value from the payload, as the planner reads it. */
export function formatValue(v: unknown): string | null {
  if (typeof v === 'number' && Number.isFinite(v)) return v.toLocaleString('en-US', { maximumSignificantDigits: 6 });
  if (typeof v === 'string' && v.length <= 80) return v;
  if (typeof v === 'boolean') return v ? 'yes' : 'no';
  return null;
}

/** The value at a dotted path such as "shared.columns.2.p50", or undefined. */
export function lookUp(data: unknown, path: string): unknown {
  let at: unknown = data;
  for (const part of path.split('.')) {
    if (at === null || typeof at !== 'object') return undefined;
    if (Array.isArray(at)) {
      if (!/^\d+$/.test(part)) return undefined;
      at = at[Number(part)];
    } else {
      if (!Object.prototype.hasOwnProperty.call(at, part)) return undefined;
      at = (at as Record<string, unknown>)[part];
    }
  }
  return at;
}

/** Every finite number anywhere in a value. */
export function numbersIn(data: unknown, out: number[] = []): number[] {
  if (typeof data === 'number' && Number.isFinite(data)) out.push(data);
  else if (Array.isArray(data)) data.forEach((d) => numbersIn(d, out));
  else if (data && typeof data === 'object') Object.values(data).forEach((d) => numbersIn(d, out));
  return out;
}

/** Numbers written in a piece of text (a question, the method). */
export function numbersInText(text: string): number[] {
  const out: number[] = [];
  for (const m of text.matchAll(NUMBER)) {
    if (!m[0] || m[0] === '-' || m[0] === '.') continue;
    const v = Number(m[0].replace(/,/g, ''));
    if (Number.isFinite(v)) out.push(v);
  }
  return out;
}

/** Whether a number the model typed matches one it was given, allowing for its rounding. */
export function matches(typed: string, allowed: number[]): boolean {
  const v = Number(typed.replace(/,/g, ''));
  if (!Number.isFinite(v)) return false;
  // Small whole numbers read as words ("2 sites", "step 4", "rank 2 or better").
  if (Number.isInteger(v) && Math.abs(v) <= 10) return true;
  const digits = typed.replace(/[^0-9]/g, '').replace(/^0+/, '').length || 1;
  return allowed.some((a) => {
    if (a === v) return true;
    if (roundSig(a, digits) === v) return true;
    // A share sent as 0.23 may be written as 23 (percent).
    if (Math.abs(a) <= 1 && roundSig(a * 100, digits) === v) return true;
    return false;
  });
}

/** Split an answer into text, filled placeholders and unverified numbers. */
export function renderAnswer(answer: string, data: unknown, allowed: number[]): Piece[] {
  const pieces: Piece[] = [];
  const pushText = (text: string) => {
    let last = 0;
    for (const m of text.matchAll(NUMBER)) {
      if (!m[0] || m[0] === '-' || m[0] === '.' || m.index === undefined) continue;
      if (matches(m[0], allowed)) continue;
      if (m.index > last) pieces.push({ kind: 'text', text: text.slice(last, m.index) });
      pieces.push({ kind: 'unverified', text: m[0] });
      last = m.index + m[0].length;
    }
    if (last < text.length) pieces.push({ kind: 'text', text: text.slice(last) });
  };
  let last = 0;
  for (const m of answer.matchAll(PLACEHOLDER)) {
    if (m.index === undefined) continue;
    if (m.index > last) pushText(answer.slice(last, m.index));
    const value = formatValue(lookUp(data, m[1]));
    pieces.push(value === null ? { kind: 'missing', path: m[1] } : { kind: 'value', text: value, path: m[1] });
    last = m.index + m[0].length;
  }
  if (last < answer.length) pushText(answer.slice(last));
  return pieces;
}

const CAUSAL = /\b(caus(?:e|es|ed|ing)|leads? to|led to|results? in|resulted in|drives)\b/gi;
const NEGATION = /\b(not|never|nothing|none|neither|cannot|can't|cant|no|isn't|aren't|doesn't|don't|didn't|without|nor)\b/i;

/**
 * Whether the answer claims a cause. A causal word with a negation shortly before it ("a
 * pattern is not a cause", "this cannot show what causes it") is allowed: that is the answer
 * doing what it should. A heuristic, so it errs towards refusing.
 */
export function claimsCause(answer: string): boolean {
  for (const m of answer.matchAll(CAUSAL)) {
    if (m.index === undefined) continue;
    const before = answer.slice(Math.max(0, m.index - 40), m.index).split(/[.!?;\n]/).pop() ?? '';
    if (!NEGATION.test(before)) return true;
  }
  return false;
}

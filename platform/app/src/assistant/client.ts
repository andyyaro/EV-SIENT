// The assistant's only network calls: same-origin requests to /api/assistant, which CloudFront
// sends to the assistant's Lambda function (platform/assistant). The CSP's connect-src 'self'
// already allows them. Origin access control signs each request for Lambda, which needs the
// SHA-256 of a POST body in x-amz-content-sha256; the browser computes it here.

import type { Context } from './payload';

export const BASE = '/api/assistant';

export type Status =
  | { state: 'available'; usedShare: number; deeper: boolean }
  | { state: 'paused'; scope: 'month' | 'day' | 'ledger'; resumes?: string; usedShare?: number; message: string }
  | { state: 'off'; message: string };

export type StreamEvent =
  | { t: 'meta'; methodNumbers: number[]; deeper: boolean }
  | { t: 'text'; v: string }
  | { t: 'done'; stop: string }
  | { t: 'error'; error: string; message: string };

export interface Turn { role: 'user' | 'assistant'; text: string }

export interface AskBody {
  v: 1;
  session: string;
  question: string;
  history: Turn[];
  context: Context;
  deeper?: boolean;
}

/** A refusal from the proxy, with its plain message and, when it has one, when it ends. */
export class AssistantRefusal extends Error {
  constructor(readonly code: string, message: string, readonly resumes?: string, readonly scope?: string) {
    super(message);
    this.name = 'AssistantRefusal';
  }
}

async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', bytes as BufferSource);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

export async function fetchStatus(signal?: AbortSignal): Promise<Status> {
  const r = await fetch(`${BASE}/status`, { method: 'GET', cache: 'no-store', credentials: 'omit', signal });
  if (!r.ok) throw new Error(`status ${r.status}`);
  const body = await r.json() as Record<string, unknown>;
  if (body.state === 'available') return { state: 'available', usedShare: Number(body.usedShare) || 0, deeper: !!body.deeper };
  if (body.state === 'paused') {
    return {
      state: 'paused', scope: (body.scope as 'month' | 'day' | 'ledger') ?? 'ledger', message: String(body.message ?? ''),
      resumes: typeof body.resumes === 'string' ? body.resumes : undefined,
      usedShare: typeof body.usedShare === 'number' ? body.usedShare : undefined,
    };
  }
  return { state: 'off', message: String(body.message ?? 'The assistant is switched off.') };
}

/** The exact text that will be sent for a request, so the preview and the request agree. */
export function serialise(body: AskBody): string {
  return JSON.stringify(body);
}

/**
 * Send one question and call `onEvent` for each line of the streamed answer. Throws
 * AssistantRefusal when the proxy refuses before answering.
 */
export async function ask(body: AskBody, onEvent: (e: StreamEvent) => void, signal?: AbortSignal): Promise<void> {
  const text = serialise(body);
  const bytes = new TextEncoder().encode(text);
  const r = await fetch(`${BASE}/ask`, {
    method: 'POST',
    cache: 'no-store',
    credentials: 'omit',
    headers: { 'content-type': 'application/json', 'x-amz-content-sha256': await sha256Hex(bytes) },
    body: bytes,
    signal,
  });
  if (!r.ok || !r.body) {
    let payload: Record<string, unknown> = {};
    try { payload = await r.json(); } catch { /* not JSON: a network or edge error */ }
    throw new AssistantRefusal(
      String(payload.error ?? `http_${r.status}`),
      String(payload.message ?? 'The assistant could not be reached. Everything else in the planner keeps working.'),
      typeof payload.resumes === 'string' ? payload.resumes : undefined,
      typeof payload.scope === 'string' ? payload.scope : undefined,
    );
  }
  const reader = r.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = '';
  for (;;) {
    const { value, done } = await reader.read();
    if (value) buffer += value;
    let nl: number;
    while ((nl = buffer.indexOf('\n')) >= 0) {
      const line = buffer.slice(0, nl).trim();
      buffer = buffer.slice(nl + 1);
      if (!line) continue;
      try { onEvent(JSON.parse(line) as StreamEvent); } catch { /* a broken line is skipped */ }
    }
    if (done) break;
  }
}

/** A random ID for this browser session, used only for the per-session limit. */
export function newSessionId(): string {
  return crypto.randomUUID();
}

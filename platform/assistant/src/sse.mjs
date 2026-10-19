// Server-sent events, parsed with no dependency: the Claude API and the OpenAI Responses API
// both stream their answers this way.

/**
 * Server-sent events from a byte or text stream, one { event, data } per event. Follows the
 * HTML event-stream rules: lines end in CRLF, LF or CR; a blank line ends an event; "data"
 * lines are joined with line breaks; lines starting with ":" are comments. Chunks may split
 * anywhere, even inside a character.
 */
export async function* parseSse(chunks) {
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let event = '';
  let data = [];
  const dispatch = function* () {
    if (data.length) yield { event: event || 'message', data: data.join('\n') };
    event = '';
    data = [];
  };
  const line = function* (l) {
    if (l === '') { yield* dispatch(); return; }
    if (l.startsWith(':')) return;
    const i = l.indexOf(':');
    const field = i === -1 ? l : l.slice(0, i);
    let value = i === -1 ? '' : l.slice(i + 1);
    if (value.startsWith(' ')) value = value.slice(1);
    if (field === 'event') event = value;
    else if (field === 'data') data.push(value);
  };
  for await (const chunk of chunks) {
    buffer += typeof chunk === 'string' ? chunk : decoder.decode(chunk, { stream: true });
    for (;;) {
      const m = /\r\n|\r|\n/.exec(buffer);
      // A CR at the very end may be the first half of a CRLF: wait for the next chunk.
      if (!m || (m[0] === '\r' && m.index === buffer.length - 1)) break;
      const l = buffer.slice(0, m.index);
      buffer = buffer.slice(m.index + m[0].length);
      yield* line(l);
    }
  }
  buffer += decoder.decode();
  if (buffer) yield* line(buffer.replace(/\r$/, ''));
  yield* dispatch();
}

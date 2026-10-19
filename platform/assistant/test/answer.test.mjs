// What the planner reads: placeholders filled from what was sent, unmatched numbers struck
// through, and answers that claim a cause held back (platform/app/src/assistant/answer.ts).
import test from 'node:test';
import assert from 'node:assert/strict';
import { claimsCause, clipChars, lookUp, matches, numbersIn, numbersInText, renderAnswer, visiblePart } from '../../app/src/assistant/answer.ts';
import { LIMITS } from '../src/validate.mjs';
import { methodNumbers } from '../src/prompt.mjs';

const CTX = {
  app: { step: 'results', hasRun: true, engine: 'real', rows: 360, columns: 31 },
  shared: { columns: [{ header: 'heat_risk_0_100', p10: 12, p50: 48, p90: 88, blankShare: 0.23 }], site: { label: 'Site A', score: 61.2 } },
};
const allowed = () => [...numbersIn(CTX), ...methodNumbers()];

test('placeholders are filled from exactly what was sent', () => {
  const pieces = renderAnswer('The middle value is [[shared.columns.0.p50]] across [[app.rows]] rows; [[shared.nope]].', CTX, allowed());
  assert.deepEqual(pieces.filter((p) => p.kind === 'value').map((p) => p.text), ['48', '360']);
  assert.equal(pieces.filter((p) => p.kind === 'missing').length, 1);
  assert.equal(lookUp(CTX, 'shared.columns.0.header'), 'heat_risk_0_100');
  assert.equal(lookUp(CTX, 'constructor'), undefined);
  assert.equal(lookUp(CTX, '__proto__.x'), undefined);
  assert.equal(lookUp(CTX, 'shared.columns.x'), undefined);
});

test('typed numbers must match a sent number, the method or the question; others are struck through', () => {
  const pieces = renderAnswer('Demand is 45% of the score. Site A scores 61.2, about 61. The median is 47.9 and 23% are blank. Its cost is 412,000.', CTX, allowed());
  const unverified = pieces.filter((p) => p.kind === 'unverified').map((p) => p.text);
  assert.deepEqual(unverified, ['47.9', '412,000']);
  assert.equal(matches('2', []), true, 'small whole numbers read as words');
  assert.equal(matches('11', []), false);
  assert.equal(matches('1,234', [1234]), true);
  assert.equal(matches('1200', [1234]), false);
  assert.equal(matches('1.2', [1.234]), true);
  assert.deepEqual(numbersInText('Is 3,500 or 2.5 or -4 better than .5?'), [3500, 2.5, -4, 0.5]);
});

test('causal claims are caught; negated ones are allowed', () => {
  for (const s of [
    'More shade causes more visits.',
    'High heat risk leads to lower scores.',
    'Flood risk drives the ranking.',
    'This resulted in fewer sites.',
    'Opening late caused the change.',
  ]) assert.equal(claimsCause(s), true, s);
  for (const s of [
    'A pattern is not a cause.',
    'This file cannot show what causes it.',
    'Sites with more shade tend to have more visits here, but that does not mean shade causes visits.',
    'The demand part is 45% of the score.',
    'Nothing here shows that heat leads to anything.',
  ]) assert.equal(claimsCause(s), false, s);
});

test('the method numbers include the published weights and thresholds', () => {
  const n = methodNumbers();
  for (const x of [45, 30, 15, 10, 50, 65, 75, 0.1]) assert.ok(n.includes(x), String(x));
});

test('M9: while streaming, only whole sentences show, and a causal sentence never shows', () => {
  const answers = [
    'The demand part is 45% of the score. Shade causes more visits in summer. Ask about another part.',
    'Sites with more shade score higher: shade leads to visitors staying longer.\nThat is all.',
    'A pattern is not a cause. Heat risk and visits move together in [[shared.columns.0.p50]] sites.',
  ];
  for (const full of answers) {
    let everCausal = false;
    for (let n = 0; n <= full.length; n += 1) {
      const { shown, causal } = visiblePart(full.slice(0, n), false);
      assert.ok(full.startsWith(shown), 'what shows is the start of the answer');
      assert.equal(claimsCause(shown), false, `shown at ${n}: ${shown}`);
      if (shown) assert.match(shown, /[.!?:]$|\n$/, 'a whole sentence');
      if (everCausal) assert.equal(causal, true, 'once a cause is claimed, it stays hidden');
      everCausal ||= causal;
    }
    assert.equal(everCausal, claimsCause(full));
    const end = visiblePart(full, true);
    assert.equal(end.causal, claimsCause(full));
    assert.equal(end.shown, end.causal ? '' : full);
  }
  // A sentence still being written is held back, even a word that is about to be causal.
  assert.deepEqual(visiblePart('The demand part is 4', false), { shown: '', causal: false });
  assert.deepEqual(visiblePart('One part. Heat caus', false), { shown: 'One part.', causal: false });
  assert.deepEqual(visiblePart('One part. Heat causes it. Then', false), { shown: '', causal: true });
});

test('M10: answers and questions are cut by code points, never inside a character', () => {
  const emoji = '\u{1F600}';
  assert.equal(clipChars(emoji.repeat(5), 3), emoji.repeat(3));
  assert.equal(clipChars('ab' + emoji, 3), 'ab' + emoji);
  assert.equal(clipChars('ab' + emoji + 'c', 2), 'ab');
  assert.equal(clipChars('short', 100), 'short');
  const long = emoji.repeat(LIMITS.assistantChars + 10);
  const cut = clipChars(long, LIMITS.assistantChars);
  assert.equal([...cut].length, LIMITS.assistantChars);
  assert.ok(!/[\ud800-\udbff](?![\udc00-\udfff])|(?<![\ud800-\udbff])[\udc00-\udfff]/.test(cut), 'no half of a pair');
});

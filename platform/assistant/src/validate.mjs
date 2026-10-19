// What the planner's browser may send, checked field by field (docs/FLEXIBLE_ANALYSIS.md section 5).
//
// Who enforces what. The server (this file) enforces the shape and the limits: every object is
// closed (a key this file does not name is refused, not ignored), labels must already be
// sanitised and short, numbers must be finite and already rounded (percentiles to 2 significant
// figures, everything else to 3), category counts under 10 are refused, identifying headers
// carry no statistics, and every list and the whole request have a size limit. The browser
// (platform/app/src/assistant/payload.ts) enforces the content: that a header is a header and a
// category label is a category, never a cell, a name or a coordinate. A modified client could
// still put a site's name where a label goes; the server cannot tell, and does not claim to.
// Free text is refused everywhere except the planner's own question and the conversation.

export const LIMITS = Object.freeze({
  // The largest consented payload the 360-site fixture produces with every group shared is
  // about 16 KB (platform/assistant/test/payload.test.mjs measures it); a question adds at most
  // 3 KB. The browser drops the oldest turns of the conversation to stay under this.
  bodyBytes: 32 * 1024,
  questionChars: 1000,
  assistantChars: 4000,
  historyTurns: 14, // seven questions before this one: eight per conversation
  labelChars: 64,
  columns: 80,
  categoriesPerColumn: 20,
  minGroup: 10,
  cards: 12,
  cardColumns: 4,
  criteria: 20,
  refusals: 20,
  tiers: 8,
  drivers: 40,
  rows: 1_000_000,
});

export const STEPS = ['start', 'upload', 'map', 'check', 'fill', 'run', 'results', 'explore', 'yourindex', 'report'];
export const ROLES = ['identifier', 'name', 'category', 'ordinal', 'flag', 'count', 'measure', 'score', 'percentage',
  'money', 'date', 'year', 'latitude', 'longitude', 'address', 'text', 'unknown'];
/** Roles whose column never carries statistics or labels: only its header, role and blank share. */
export const HEADER_ONLY_ROLES = ['identifier', 'name', 'latitude', 'longitude', 'address', 'text', 'date', 'unknown'];
/** Roles whose labels may be counted. */
export const CATEGORY_ROLES = ['category', 'ordinal', 'flag'];
/** Roles whose numeric percentiles may be sent. */
export const NUMERIC_ROLES = ['count', 'measure', 'score', 'percentage', 'money', 'year'];
/**
 * Header words that mark a column as identifying whatever role it was given: such a column may
 * carry only its header, role, blank share and distinct bucket. The browser holds the same list
 * (payload.ts SENSITIVE_HEADER_WORDS) and the tests check they agree.
 */
export const SENSITIVE_HEADER_WORDS = [
  'id', 'ids', 'uuid', 'guid', 'key', 'name', 'names', 'lat', 'latitude', 'lon', 'lng', 'long', 'longitude',
  'coord', 'coords', 'coordinate', 'coordinates', 'geometry', 'geom', 'wkt', 'geojson', 'easting', 'northing',
  'address', 'addr', 'street', 'postcode', 'postal', 'zip', 'zipcode', 'email', 'phone', 'tel', 'contact',
  'note', 'notes', 'comment', 'comments', 'description', 'remarks', 'owner', 'parcel', 'apn',
  'x', 'y', 'pointx', 'pointy', 'xcoord', 'ycoord', 'gps', 'location', 'loc', 'geo', 'geopoint', 'fid', 'oid',
  'objectid', 'sitename', 'siteid', 'latdd', 'londd', 'lngdd', 'mail', 'mobile', 'fax', 'dob', 'birth', 'ssn',
  'passport', 'plate', 'vin', 'ip',
];
/** Word endings and beginnings that mark the same: site_id, siteid, sitename, latdd, lon_wgs84. */
export const SENSITIVE_HEADER_SUFFIXES = ['id', 'name', 'address', 'zip', 'postcode', 'phone', 'email'];
export const SENSITIVE_HEADER_PREFIXES = ['lat', 'lon', 'lng'];

/**
 * Whether a header names an identifying column. The header is split into words at anything not
 * a letter or digit and at case changes (siteName, POINT_X, geo_point); each word, and all the
 * words run together, is checked against the list, the endings and the beginnings. It errs
 * towards sharing less: "valid" or "latency" also send only their header.
 */
function headerWords(header) {
  const words = header.normalize('NFKC').replace(/([a-z0-9])([A-Z])/g, '$1 $2').toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
  return words.length > 1 ? [...words, words.join('')] : words;
}

export function sensitiveHeader(header) {
  // The header as written and as it travels (hidden characters removed), so a hidden character
  // can neither split a word apart nor run two together unseen.
  const raw = String(header ?? '');
  const candidates = [...headerWords(raw), ...headerWords(sanitizeLabel(raw)), ...headerWords(raw.replace(HIDDEN, ''))];
  return candidates.some((w) => SENSITIVE_HEADER_WORDS.includes(w)
    || SENSITIVE_HEADER_SUFFIXES.some((s) => w.endsWith(s))
    || SENSITIVE_HEADER_PREFIXES.some((p) => w.startsWith(p)));
}

export const DIRECTIONS = ['higher_better', 'lower_better', 'neither'];
export const CARDINALITY = ['one value', '2 to 5', '6 to 20', '21 to 100', 'over 100'];
export const PARTS = ['demand', 'feasibility', 'safety', 'equity'];
export const CONFIDENCE = ['High', 'Medium', 'Low'];
export const INDEX_KINDS = ['linear', 'threshold', 'target', 'ordinal'];

// Characters nobody can see, removed outright: every default-ignorable code point (zero-width
// characters, variation selectors U+FE00-FE0F and U+E0100-E01EF, the combining grapheme joiner
// U+034F, the Hangul fillers U+115F, U+1160, U+3164 and U+FFA0, bidirectional controls, tag
// characters), every format character (Cf), the braille blank U+2800 and the object
// replacement U+FFFC. Several are used to hide instructions or to split a word such as
// "latitude" so a check does not see it.
const HIDDEN = /[\p{Default_Ignorable_Code_Point}\p{Cf}\u034f\u115f\u1160\u3164\uffa0\ufe00-\ufe0f\u{E0100}-\u{E01EF}\u2800\ufffc]/gu;
// Controls (Cc), private use (Co), surrogates (Cs), unassigned (Cn), line and paragraph
// separators: turned into spaces, then runs of spaces into one.
const SPACING = /[\p{Cc}\p{Co}\p{Cs}\p{Cn}\u2028\u2029]/gu;
const LEADING_FORMULA = /^[\s=+\-@]+/u;

/**
 * A header or label as it may travel: no invisible characters, single spaces, no leading
 * = + - @ (spreadsheet formulas), no [[ ]] (the answer placeholders), no < > (markup), no
 * backticks, at most 64 characters. The browser applies exactly this; the server checks that a
 * label is unchanged by it. Returns '' when nothing is left.
 */
export function sanitizeLabel(raw) {
  let s = String(raw ?? '');
  // Normalising can make a hidden character (U+3164 becomes U+1160) and removing one can leave
  // characters that normalise further, so repeat until nothing changes.
  for (let i = 0, prev = null; i < 4 && s !== prev; i += 1) {
    prev = s;
    s = s.normalize('NFKC').replace(HIDDEN, '').replace(SPACING, ' ');
  }
  s = s.replace(/\[\[|\]\]/g, ' ').replace(/[<>`]/g, ' ');
  s = s.replace(/\s+/gu, ' ').trim();
  let before;
  do { before = s; s = s.replace(LEADING_FORMULA, ''); } while (s !== before);
  if ([...s].length > LIMITS.labelChars) s = [...s].slice(0, LIMITS.labelChars).join('').trim();
  return s;
}

/** x rounded to `digits` significant figures, as a plain number. */
export function roundSig(x, digits) {
  if (!Number.isFinite(x) || x === 0) return x === 0 ? 0 : x;
  return Number(x.toPrecision(digits));
}

export class Invalid extends Error {
  constructor(path, why) {
    super(`${path}: ${why}`);
    this.name = 'Invalid';
    this.path = path;
  }
}

const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

function closed(v, path, required, optional = []) {
  if (!isObject(v)) throw new Invalid(path, 'must be an object');
  const allowed = new Set([...required, ...optional]);
  for (const key of Object.keys(v)) if (!allowed.has(key)) throw new Invalid(`${path}.${key}`, 'is not allowed');
  for (const key of required) if (!(key in v)) throw new Invalid(`${path}.${key}`, 'is required');
}

function int(v, path, min, max) {
  if (!Number.isInteger(v) || v < min || v > max) throw new Invalid(path, `must be a whole number from ${min} to ${max}`);
}

function num(v, path, digits) {
  if (typeof v !== 'number' || !Number.isFinite(v)) throw new Invalid(path, 'must be a finite number');
  if (roundSig(v, digits) !== v) throw new Invalid(path, `must be rounded to ${digits} significant figures`);
}

function share(v, path) {
  if (typeof v !== 'number' || !Number.isFinite(v) || v < 0 || v > 1) throw new Invalid(path, 'must be a share from 0 to 1');
  if (Math.round(v * 100) / 100 !== v) throw new Invalid(path, 'must be rounded to 2 decimal places');
}

function oneOf(v, path, options) {
  if (!options.includes(v)) throw new Invalid(path, 'is not one of the allowed values');
}

function label(v, path) {
  if (typeof v !== 'string' || !v) throw new Invalid(path, 'must be a non-empty label');
  if (sanitizeLabel(v) !== v) throw new Invalid(path, 'must be a sanitised label of at most 64 characters');
}

/** Short machine words from the engine (card kinds, refusal codes): letters, digits, _ and -. */
function slug(v, path) {
  if (typeof v !== 'string' || !/^[a-z][a-z0-9_-]{0,39}$/.test(v)) throw new Invalid(path, 'must be a short code');
}

function list(v, path, max) {
  if (!Array.isArray(v)) throw new Invalid(path, 'must be a list');
  if (v.length > max) throw new Invalid(path, `must have at most ${max} items`);
}

function text(v, path, max) {
  if (typeof v !== 'string') throw new Invalid(path, 'must be text');
  const chars = [...v].length;
  if (!chars || chars > max) throw new Invalid(path, `must be 1 to ${max} characters`);
}

function column(c, path) {
  closed(c, path, ['header', 'role', 'blankShare', 'distinct'], ['unit', 'direction', 'scale', 'p10', 'p50', 'p90', 'categories', 'hiddenCategories']);
  label(c.header, `${path}.header`);
  oneOf(c.role, `${path}.role`, ROLES);
  share(c.blankShare, `${path}.blankShare`);
  oneOf(c.distinct, `${path}.distinct`, CARDINALITY);
  const headerOnly = HEADER_ONLY_ROLES.includes(c.role) || sensitiveHeader(c.header);
  if (headerOnly) {
    for (const k of ['unit', 'direction', 'scale', 'p10', 'p50', 'p90', 'categories', 'hiddenCategories']) {
      if (c[k] !== undefined) throw new Invalid(`${path}.${k}`, 'is not allowed for an identifying column');
    }
  }
  if (c.unit !== undefined && c.unit !== null) label(c.unit, `${path}.unit`);
  if (c.direction !== undefined && c.direction !== null) oneOf(c.direction, `${path}.direction`, DIRECTIONS);
  if (c.scale !== undefined && c.scale !== null) {
    list(c.scale, `${path}.scale`, 2);
    if (c.scale.length !== 2) throw new Invalid(`${path}.scale`, 'must be two numbers');
    c.scale.forEach((x, i) => num(x, `${path}.scale[${i}]`, 3));
  }
  const pcts = ['p10', 'p50', 'p90'].filter((k) => c[k] !== undefined);
  if (pcts.length) {
    if (!NUMERIC_ROLES.includes(c.role)) throw new Invalid(`${path}.${pcts[0]}`, `is not allowed for a ${c.role} column`);
    if (pcts.length !== 3) throw new Invalid(`${path}.p10`, 'p10, p50 and p90 travel together');
    for (const k of pcts) num(c[k], `${path}.${k}`, 2);
    if (!(c.p10 <= c.p50 && c.p50 <= c.p90)) throw new Invalid(`${path}.p50`, 'percentiles must be in order');
  }
  if (c.categories !== undefined) {
    if (headerOnly || !CATEGORY_ROLES.includes(c.role)) throw new Invalid(`${path}.categories`, `is not allowed for a ${c.role} column`);
    list(c.categories, `${path}.categories`, LIMITS.categoriesPerColumn);
    c.categories.forEach((g, i) => {
      const p = `${path}.categories[${i}]`;
      closed(g, p, ['label', 'count']);
      label(g.label, `${p}.label`);
      int(g.count, `${p}.count`, LIMITS.minGroup, LIMITS.rows);
    });
  }
  if (c.hiddenCategories !== undefined) int(c.hiddenCategories, `${path}.hiddenCategories`, 0, LIMITS.rows);
  if (headerOnly && c.unit) throw new Invalid(`${path}.unit`, `is not allowed for a ${c.role} column`);
}

function shared(s, path) {
  closed(s, path, [], ['columns', 'readiness', 'explore', 'index', 'site']);
  if (s.columns !== undefined) {
    list(s.columns, `${path}.columns`, LIMITS.columns);
    s.columns.forEach((c, i) => column(c, `${path}.columns[${i}]`));
  }
  if (s.readiness !== undefined) {
    const r = s.readiness;
    const p = `${path}.readiness`;
    closed(r, p, ['sites', 'tiers'], ['highConfidence', 'starterPorts', 'pathwayPorts']);
    int(r.sites, `${p}.sites`, 0, LIMITS.rows);
    list(r.tiers, `${p}.tiers`, LIMITS.tiers);
    r.tiers.forEach((t, i) => {
      closed(t, `${p}.tiers[${i}]`, ['tier', 'count']);
      label(t.tier, `${p}.tiers[${i}].tier`);
      int(t.count, `${p}.tiers[${i}].count`, 0, LIMITS.rows);
    });
    for (const k of ['highConfidence', 'starterPorts', 'pathwayPorts']) {
      if (r[k] !== undefined && r[k] !== null) int(r[k], `${p}.${k}`, 0, 100 * LIMITS.rows);
    }
  }
  if (s.explore !== undefined) {
    const e = s.explore;
    const p = `${path}.explore`;
    closed(e, p, ['checked', 'passed', 'cards']);
    int(e.checked, `${p}.checked`, 0, 1_000_000);
    int(e.passed, `${p}.passed`, 0, 1_000_000);
    list(e.cards, `${p}.cards`, LIMITS.cards);
    e.cards.forEach((c, i) => {
      const q = `${p}.cards[${i}]`;
      closed(c, q, ['kind', 'columns', 'n', 'reliability'], ['effect', 'q']);
      slug(c.kind, `${q}.kind`);
      list(c.columns, `${q}.columns`, LIMITS.cardColumns);
      c.columns.forEach((h, j) => label(h, `${q}.columns[${j}]`));
      int(c.n, `${q}.n`, 0, LIMITS.rows);
      slug(c.reliability, `${q}.reliability`);
      if (c.q !== undefined && c.q !== null) num(c.q, `${q}.q`, 2);
      if (c.effect !== undefined && c.effect !== null) {
        closed(c.effect, `${q}.effect`, ['name', 'value'], ['low', 'high']);
        slug(c.effect.name, `${q}.effect.name`);
        num(c.effect.value, `${q}.effect.value`, 3);
        for (const k of ['low', 'high']) if (c.effect[k] !== undefined && c.effect[k] !== null) num(c.effect[k], `${q}.effect.${k}`, 3);
      }
    });
  }
  if (s.index !== undefined) {
    const x = s.index;
    const p = `${path}.index`;
    closed(x, p, ['criteria', 'refused'], ['refusals', 'ranked', 'unranked']);
    list(x.criteria, `${p}.criteria`, LIMITS.criteria);
    x.criteria.forEach((c, i) => {
      const q = `${p}.criteria[${i}]`;
      closed(c, q, ['column', 'direction', 'weight', 'kind']);
      label(c.column, `${q}.column`);
      oneOf(c.direction, `${q}.direction`, DIRECTIONS);
      num(c.weight, `${q}.weight`, 3);
      oneOf(c.kind, `${q}.kind`, INDEX_KINDS);
    });
    if (typeof x.refused !== 'boolean') throw new Invalid(`${p}.refused`, 'must be true or false');
    if (x.refusals !== undefined) {
      list(x.refusals, `${p}.refusals`, LIMITS.refusals);
      x.refusals.forEach((r, i) => slug(r, `${p}.refusals[${i}]`));
    }
    for (const k of ['ranked', 'unranked']) if (x[k] !== undefined && x[k] !== null) int(x[k], `${p}.${k}`, 0, LIMITS.rows);
  }
  if (s.site !== undefined) {
    const t = s.site;
    const p = `${path}.site`;
    closed(t, p, ['label', 'score', 'drivers'], ['confidence']);
    if (t.label !== 'Site A') throw new Invalid(`${p}.label`, 'must be "Site A"');
    num(t.score, `${p}.score`, 3);
    if (t.confidence !== undefined && t.confidence !== null) oneOf(t.confidence, `${p}.confidence`, CONFIDENCE);
    list(t.drivers, `${p}.drivers`, LIMITS.drivers);
    t.drivers.forEach((d, i) => {
      const q = `${p}.drivers[${i}]`;
      closed(d, q, ['label', 'part', 'points', 'max', 'missing']);
      label(d.label, `${q}.label`);
      oneOf(d.part, `${q}.part`, PARTS);
      num(d.points, `${q}.points`, 3);
      num(d.max, `${q}.max`, 3);
      if (typeof d.missing !== 'boolean') throw new Invalid(`${q}.missing`, 'must be true or false');
    });
  }
}

/**
 * Check one request body (already parsed). Throws Invalid naming the first problem; returns the
 * same object when everything is allowed. Nothing is repaired: a request that needs repair is
 * one the browser did not build.
 */
export function validateAsk(body) {
  closed(body, 'request', ['v', 'session', 'question', 'history', 'context'], ['deeper']);
  if (body.v !== 1) throw new Invalid('request.v', 'must be 1');
  if (typeof body.session !== 'string' || !/^[A-Za-z0-9_-]{16,64}$/.test(body.session)) throw new Invalid('request.session', 'must be 16 to 64 letters, digits, _ or -');
  text(body.question, 'request.question', LIMITS.questionChars);
  if (body.deeper !== undefined && typeof body.deeper !== 'boolean') throw new Invalid('request.deeper', 'must be true or false');
  list(body.history, 'request.history', LIMITS.historyTurns);
  body.history.forEach((m, i) => {
    const p = `request.history[${i}]`;
    closed(m, p, ['role', 'text']);
    const want = i % 2 === 0 ? 'user' : 'assistant';
    if (m.role !== want) throw new Invalid(`${p}.role`, `must be "${want}" (turns alternate, starting with the planner)`);
    text(m.text, `${p}.text`, want === 'user' ? LIMITS.questionChars : LIMITS.assistantChars);
  });
  if (body.history.length % 2 !== 0) throw new Invalid('request.history', 'must end with an answer');
  const ctx = body.context;
  closed(ctx, 'request.context', ['app'], ['shared']);
  const a = ctx.app;
  closed(a, 'request.context.app', ['step', 'hasRun', 'engine'], ['rows', 'columns']);
  oneOf(a.step, 'request.context.app.step', STEPS);
  if (typeof a.hasRun !== 'boolean') throw new Invalid('request.context.app.hasRun', 'must be true or false');
  oneOf(a.engine, 'request.context.app.engine', ['real', 'stand-in']);
  if (a.rows !== undefined && a.rows !== null) int(a.rows, 'request.context.app.rows', 0, LIMITS.rows);
  if (a.columns !== undefined && a.columns !== null) int(a.columns, 'request.context.app.columns', 0, 10_000);
  if (ctx.shared !== undefined && ctx.shared !== null) shared(ctx.shared, 'request.context.shared');
  return body;
}

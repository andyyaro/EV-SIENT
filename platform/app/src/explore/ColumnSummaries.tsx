// Each of the planner's columns on its own, as the engine summarised it: how many sites have a
// value, the middle half and median of numbers, the size of each group, dates by year and the most
// common words in free text. Descriptive only: nothing here is a test or ranks a site.

import { useId } from 'react';
import { int, plural, roleWords } from './text';

interface Count { level: string | number; count: number; hidden?: boolean }

export interface Summary {
  column: string;
  label: string;
  role: string;
  n?: number;
  missing?: number;
  sentence?: string;
  median?: number | string;
  q1?: number; q3?: number; min?: number; max?: number;
  outliers?: number;
  levels?: Count[];
  counts?: Count[];
  hiddenGroups?: number;
  byYear?: { year: number; count: number }[];
  keywords?: { word: string; sites: number }[];
  duplicates?: number;
  notTested?: string;
  outOfRange?: number;
}

const MAX_BARS = 12;

const short = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 });
const big = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
const numText = (v: number) => (Math.abs(v) >= 1000 ? big.format(v) : short.format(v)).replace(/^-/, '−');

/** The middle half of a number column on its own range, with the median marked. */
function SpreadStrip({ s }: { s: Required<Pick<Summary, 'min' | 'max' | 'q1' | 'q3'>> & { median: number } }) {
  const span = s.max - s.min;
  const at = (v: number) => `${span > 0 ? ((v - s.min) / span) * 100 : 50}%`;
  const words = `Lowest ${numText(s.min)}, middle half from ${numText(s.q1)} to ${numText(s.q3)}, median ${numText(s.median)}, highest ${numText(s.max)}.`;
  return (
    <div className="xp-spread" role="img" aria-label={words}>
      <span className="xp-spread__track" aria-hidden="true">
        <span className="xp-spread__box" style={{ left: at(s.q1), width: `calc(${at(s.q3)} - ${at(s.q1)})` }} />
        <span className="xp-spread__median" style={{ left: at(s.median) }} />
      </span>
      <span className="xp-spread__ends num" aria-hidden="true">
        <span>{numText(s.min)}</span><span>{numText(s.max)}</span>
      </span>
    </div>
  );
}

/** Counts per group or level, longest first for groups, in order for levels. Numbers are always written. */
function Bars({ items, ordered, minGroup }: { items: Count[]; ordered: boolean; minGroup: number }) {
  const list = ordered ? items : [...items].sort((a, b) => b.count - a.count);
  const shown = list.slice(0, MAX_BARS);
  const rest = list.slice(MAX_BARS);
  const top = Math.max(1, ...list.map((c) => c.count));
  return (
    <>
      <ul className="xp-bars" role="list">
        {shown.map((c) => (
          <li className="xp-bar" key={String(c.level)}>
            <span className="xp-bar__label">{String(c.level)}</span>
            <span className="xp-bar__value num">
              {int(c.count)}
              {c.hidden && <span className="xp-bar__hint"> (under {minGroup}, not compared)</span>}
            </span>
            <span className="xp-bar__track" aria-hidden="true">
              <span className="xp-bar__fill" style={{ width: `${(c.count / top) * 100}%` }} />
            </span>
          </li>
        ))}
      </ul>
      {rest.length > 0 && (
        <p className="footnote xp-bars__more">
          And {plural(rest.length, 'more group')} with {plural(rest.reduce((t, c) => t + c.count, 0), 'site')} between them.
        </p>
      )}
    </>
  );
}

function SummaryCard({ s, minGroup }: { s: Summary; minGroup: number }) {
  const titleId = useId();
  const n = s.n ?? 0;
  const missing = s.missing ?? 0;
  const median = typeof s.median === 'number' ? s.median : null;
  const spread = median !== null && [s.min, s.max, s.q1, s.q3].every((v) => typeof v === 'number');
  return (
    <article className="xp-col" aria-labelledby={titleId}>
      <h3 className="xp-col__title" id={titleId}>{s.label}</h3>
      <p className="xp-col__meta">
        <span className="xp-col__name">{s.column}</span>
        <span aria-hidden="true"> · </span>
        <span>{roleWords(s.role)}</span>
      </p>
      <p className="xp-col__count num">
        {plural(n, 'site')} with a value{missing ? `, ${int(missing)} blank or unknown` : ''}.
        {typeof s.duplicates === 'number' && (s.duplicates ? ` ${plural(s.duplicates, 'ID')} repeated.` : ' No ID is repeated.')}
      </p>
      {spread && <SpreadStrip s={{ min: s.min!, max: s.max!, q1: s.q1!, q3: s.q3!, median: median! }} />}
      {s.levels && s.levels.length > 0 && <Bars items={s.levels} ordered minGroup={minGroup} />}
      {s.counts && s.counts.length > 0 && <Bars items={s.counts} ordered={false} minGroup={minGroup} />}
      {s.byYear && s.byYear.length > 0 && !spread && (
        <Bars items={s.byYear.map((y) => ({ level: y.year, count: y.count }))} ordered minGroup={0} />
      )}
      {s.keywords && s.keywords.length > 0 && (
        <p className="xp-col__text">
          Most common words: {s.keywords.slice(0, 8).map((k) => `${k.word} (${plural(k.sites, 'site')})`).join(', ')}.
        </p>
      )}
      {s.sentence && <p className="xp-col__text">{s.sentence}</p>}
      {typeof s.outOfRange === 'number' && s.outOfRange > 0 && (
        <p className="xp-col__text">{plural(s.outOfRange, 'value')} outside the range this column allows.</p>
      )}
      {s.notTested && <p className="footnote">Not compared with other columns: {s.notTested}.</p>}
    </article>
  );
}

export function ColumnSummaries({ summaries, minGroup }: { summaries: Summary[]; minGroup: number }) {
  return (
    <div className="xp-cols">
      {summaries.map((s) => <SummaryCard key={s.column} s={s} minGroup={minGroup} />)}
    </div>
  );
}

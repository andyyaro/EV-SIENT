// How much of the score the planner's file can feed, said plainly on Map Columns and Check: how
// many of the fields the score uses the file provides, and that every other column is carried
// with each site (Your Columns), not scored. When fewer than half are provided, the banner says
// first that the ranking will mostly reflect missing information.

import { plural } from '../lib/fieldText';
import { useSession } from '../state/store';
import { Banner } from './Banner';

export function scoreCoverage(s: ReturnType<typeof useSession.getState>) {
  const scored = (s.fields?.fields ?? []).filter((f) => f.scored).map((f) => f.name);
  const mapping = s.proposal?.mapping ?? {};
  const provided = scored.filter((f) => mapping[f]).length;
  const filled = scored.filter((f) => !mapping[f] && (s.check?.publicFill.filled[f] ?? 0) > 0).length;
  const used = new Set(Object.values(mapping).filter(Boolean));
  const carried = (s.table?.columns ?? []).filter((c) => !used.has(c)).length;
  return { total: scored.length, provided, filled, carried };
}

export function ScoreCoverage() {
  const s = useSession();
  const { total, provided, filled, carried } = scoreCoverage(s);
  if (!total || !s.proposal) return null;
  const thin = (provided + filled) * 2 < total;
  return (
    <Banner tone={thin ? 'warning' : 'info'} title={thin ? 'Most of What the Score Uses Is Missing' : `Your File Provides ${provided} of the ${total} Scored Fields`}>
      {thin && (
        <p><strong>With {provided + filled} of the {total} fields the score uses, the ranking will mostly reflect missing information, not how suitable each site is.</strong></p>
      )}
      <p>
        Your file provides {provided} of the {total} fields the readiness score uses{filled ? `, and public data fills ${plural(filled, 'more')}` : ''}.
        {' '}{carried
          ? `${plural(carried, 'other column')} ${carried === 1 ? 'is' : 'are'} not read by the model. ${carried === 1 ? 'It is' : 'They are'} carried with each site and shown in Results as Your Columns, never scored.`
          : 'Every column in your file is matched to a field.'}
      </p>
      {thin && <p>In Map Columns, match any column that holds a scored field, or add the fields to your spreadsheet. A field left out earns no credit at any site.</p>}
    </Banner>
  );
}

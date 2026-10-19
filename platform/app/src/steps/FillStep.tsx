// Public Data: optional. For fields the planner's file does not have, the public data hub can
// propose a value at each site (DEC-025). Nothing is fetched until the planner asks, every value is
// shown with its source and vintage, and each field is used only if the planner says so. A site
// with no value is shown with the reason, never given a zero.

import { useState } from 'react';
import { Banner } from '../components/Banner';
import { Icon } from '../components/Icon';
import { PageHead } from '../components/PageHead';
import { Progress } from '../components/Progress';
import { StepActions } from '../components/StepActions';
import type { CheckRow, FieldFill } from '../engine/protocol';
import type { HubField } from '../hub/types';
import { fieldLabel, listWords, plural } from '../lib/fieldText';
import { publicNeeds, stepGate, useSession } from '../state/store';

const PAGE = 50;

const megabytes = (bytes: number) => `${(bytes / 1024 / 1024).toFixed(bytes < 1024 * 1024 ? 2 : 1)} MB`;

function formatValue(value: number, decimals: number): string {
  return value.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function NeedsList({ needs, total }: { needs: Record<string, string[]>; total: number }) {
  const s = useSession();
  const absent = new Set(s.check?.absentFromFile ?? []);
  return (
    <ul className="st-plain-list">
      {Object.entries(needs).map(([field, sites]) => (
        <li key={field}>
          <strong>{fieldLabel(s.fields, field)}</strong>
          <span className="st-muted">{absent.has(field) ? ': not in your file' : `: empty at ${plural(sites.length, 'site')} of ${total}`}</span>
        </li>
      ))}
    </ul>
  );
}

function InUse({ fills }: { fills: FieldFill[] }) {
  const fields = useSession((s) => s.fields);
  return (
    <ul className="st-plain-list">
      {fills.map((f) => (
        <li key={f.field}>
          <strong>{fieldLabel(fields, f.field)}</strong>: {plural(Object.keys(f.values).length, 'site')}, from {f.source.title} ({f.source.vintage}), public data release {f.source.hubVersion}.
        </li>
      ))}
    </ul>
  );
}

function FieldCard({ field, spec, sites }: { field: string; spec: HubField; sites: CheckRow[] }) {
  const s = useSession();
  const [limit, setLimit] = useState(PAGE);
  const proposed = s.hub!.proposals[field] ?? {};
  const withValue = sites.filter((r) => 'value' in (proposed[r.siteId] ?? {})).length;
  const choice = s.publicChoice[field];
  const label = fieldLabel(s.fields, field);
  const titleId = `fill-${field}`;
  const shown = sites.slice(0, limit);
  const busy = s.busy === 'fill';
  const choose = (c: 'use' | 'skip') => { void s.choosePublicData(field, c); };
  return (
    <section className="card st-fill" aria-labelledby={titleId}>
      <div className="st-fill__head">
        <div className="st-fill__text">
          <h3 id={titleId} className="st-subtitle">{label}</h3>
          <p className="st-fill__source"><Icon name="globe" size={15} /> {spec.sourceLabel}{spec.sourceLabel.includes(spec.vintage) ? '' : ` · ${spec.vintage}`}</p>
        </div>
        <div className="st-fill__choice" role="group" aria-label={`Use public values for ${label}`}>
          <button type="button" aria-pressed={choice === 'use'} disabled={busy || !withValue}
            className={`hig-button hig-button--ios hig-button--medium hig-focus ${choice === 'use' ? 'hig-button--bordered-prominent' : 'hig-button--bordered'}`}
            onClick={() => choose('use')}>
            {choice === 'use' && <Icon name="checkmark" size={15} strokeWidth={2.4} />}
            <span className="hig-button__label">Use These Values</span>
          </button>
          <button type="button" aria-pressed={choice === 'skip'} disabled={busy}
            className={`hig-button hig-button--ios hig-button--medium hig-focus ${choice === 'skip' ? 'hig-button--bordered-prominent' : 'hig-button--bordered'}`}
            onClick={() => choose('skip')}>
            {choice === 'skip' && <Icon name="checkmark" size={15} strokeWidth={2.4} />}
            <span className="hig-button__label">Do Not Use</span>
          </button>
        </div>
      </div>
      <p className="st-fill__method">{spec.method}</p>
      <p className="footnote">
        {withValue === sites.length
          ? `A value for every one of the ${plural(sites.length, 'site')} without one.`
          : `A value for ${withValue} of the ${plural(sites.length, 'site')} without one; the rest stay empty, for the reason given.`}
        {' '}Licence: {spec.licence}
      </p>
      <div className="st-table-wrap st-gap-top" role="region" aria-label={`${label}: proposed values`} tabIndex={0}>
        <table className="st-table">
          <caption className="hig-visually-hidden">{`Public values proposed for ${label}, by site.`}</caption>
          <thead>
            <tr>
              <th scope="col">Site ID</th>
              <th scope="col">Site Name</th>
              <th scope="col" className="st-fill__value">Proposed Value</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((r) => {
              const p = proposed[r.siteId];
              return (
                <tr key={r.siteId}>
                  <td className="st-mono">{r.siteId}</td>
                  <td>{r.siteName || <span className="st-blank">none</span>}</td>
                  {p && 'value' in p
                    ? <td className="st-fill__value num">{formatValue(p.value, spec.decimals)}</td>
                    : <td className="st-wrap st-muted">None. {p?.reason ?? 'Not looked up.'}</td>}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {sites.length > shown.length && (
        <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--bordered hig-focus st-gap-top" onClick={() => setLimit(limit + PAGE)}>
          Show {Math.min(PAGE, sites.length - shown.length)} More of {sites.length - shown.length}
        </button>
      )}
    </section>
  );
}

export function FillStep() {
  const s = useSession();
  const gate = stepGate(s, 'fill');
  const needs = publicNeeds(s);
  const hasNeeds = Object.keys(needs).length > 0;

  if (!gate.open) {
    return (
      <div className="page st-page">
        <PageHead title="Public Data" lede={gate.reason} />
        <StepActions onBack={() => s.go('check')} />
      </div>
    );
  }

  const check = s.check!;
  const hub = s.hub;
  const looking = s.busy === 'hub';
  const rowsById = new Map(check.rows.map((r) => [r.siteId, r]));
  const offered = hub ? Object.keys(needs).filter((f) => hub.manifest.fields[f]) : [];
  const notYet = hub ? Object.keys(needs).filter((f) => !hub.manifest.fields[f]) : [];

  return (
    <div className="page st-page">
      <PageHead
        title="Public Data"
        lede="Optional. Where your file has no value, public data can propose one for each site. You see every value and where it came from, and nothing is used unless you choose it."
      />

      <div className="st-principle">
        <Icon name="info.circle" size={20} className="st-principle__icon" />
        <p><strong>Your own values always win.</strong> Public data only fills a field your file does not have, or a cell it left empty. Each value is recorded with its source and date, and data confidence treats it as public data, not as your own.</p>
      </div>

      {!hasNeeds && !s.publicFills.length && (
        <Banner tone="info" title="Nothing to Fill">
          <p>Your file has a value at every site for each field public data can fill: {listWords(check.publicFill.fields.map((f) => fieldLabel(s.fields, f)))}.</p>
        </Banner>
      )}

      {hasNeeds && (
        <section className="section" aria-labelledby="fill-needs-title">
          <h2 id="fill-needs-title" className="section__title">What Public Data Could Fill</h2>
          <div className="card">
            <NeedsList needs={needs} total={check.counts.total} />
          </div>
        </section>
      )}

      {s.publicFills.length > 0 && !hub && (
        <section className="section" aria-labelledby="fill-inuse-title">
          <h2 id="fill-inuse-title" className="section__title">Public Values in Use</h2>
          <div className="card"><InUse fills={s.publicFills} /></div>
        </section>
      )}

      {hasNeeds && (
        <section className="section" aria-labelledby="fill-look-title">
          <h2 id="fill-look-title" className="section__title">{hub ? 'Looked Up' : 'Look Up Public Data'}</h2>
          {!hub && (
            <p className="section__intro">
              This downloads public data files from this site for the counties around your sites. Your file and your sites are not sent anywhere: the requests name counties, not sites, and every value is worked out on this device. The hub covers Virginia so far.
            </p>
          )}
          {hub && (
            <p className="st-coverage num">
              Public data release {hub.manifest.hubVersion} · {plural(hub.counties.length, 'county file', 'county files')} · {megabytes(hub.bytes)}
            </p>
          )}
          <div role="status" aria-live="polite" className="st-inline-status">
            {looking && (
              <Progress
                label="Looking up public data"
                fraction={s.hubProgress && s.hubProgress.total ? s.hubProgress.done / s.hubProgress.total : undefined}
                detail={s.hubProgress ? `${s.hubProgress.done} of ${plural(s.hubProgress.total, 'county file')} read and checked.` : 'Reading the hub release.'}
              />
            )}
          </div>
          {!looking && (
            <button type="button" className={`hig-button hig-button--ios hig-button--large hig-focus st-gap-top ${hub ? 'hig-button--bordered' : 'hig-button--bordered-prominent'}`}
              onClick={() => void s.lookUpPublicData()} disabled={!!s.busy}>
              <Icon name={hub ? 'arrow.clockwise' : 'globe'} size={17} />
              <span className="hig-button__label">{hub ? 'Look Up Again' : 'Look Up Public Data'}</span>
            </button>
          )}
        </section>
      )}

      {hub && offered.length > 0 && (
        <section className="section" aria-labelledby="fill-proposed-title">
          <h2 id="fill-proposed-title" className="section__title">Proposed Values</h2>
          <p className="section__intro">Choose for each field. A value is used only at sites where your file has none.</p>
          <div className="st-fill-list">
            {offered.map((f) => (
              <FieldCard key={f} field={f} spec={hub.manifest.fields[f]} sites={needs[f].map((id) => rowsById.get(id)!).filter(Boolean)} />
            ))}
          </div>
        </section>
      )}

      {hub && notYet.length > 0 && (
        <section className="section" aria-labelledby="fill-notyet-title">
          <h2 id="fill-notyet-title" className="section__title">Not in the Hub Yet</h2>
          <div className="card">
            <ul className="st-finding-list">
              {notYet.map((f) => (
                <li key={f} className="st-finding">
                  <p className="st-finding__field">{fieldLabel(s.fields, f)}</p>
                  <p className="st-finding__text">{hub.manifest.notYet[f] ?? 'Not in this release.'} These sites stay without a value and earn no credit for it.</p>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      <StepActions
        onBack={() => s.go('check')}
        onNext={() => s.go('run')}
        nextLabel="Continue to Run"
        busy={looking || s.busy === 'fill'}
      />
    </div>
  );
}

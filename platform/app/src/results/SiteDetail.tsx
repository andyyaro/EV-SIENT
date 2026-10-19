// One site in full: score and subscores, the Explain card, the port plan and its horizons, data
// confidence by group, operations and the capacity evidence. Every number is the engine's.

import { forwardRef } from 'react';
import { Icon } from '../components/Icon';
import type { FieldCatalog, OutputFiles, RunResult, SiteResult } from '../engine/protocol';
import { ExplainCard } from './ExplainCard';
import {
  CAPACITY_LADDER, ladderRung, readCapacity, useExplain, type Loadable,
} from './data';
import {
  CONFIDENCE_CUTOFFS, caseLabel, fmt, isNumber, sentence, siteTypeLabel, SUBSCORE_KEYS, subscoreLabel, tierKey, tierLong,
} from './format';

interface Props {
  run: RunResult;
  site: SiteResult;
  fields: FieldCatalog | null;
  files: Loadable<OutputFiles>;
  inCompare: boolean;
  compareFull: boolean;
  onToggleCompare(): void;
  onBack?(): void;
}

export const SiteDetail = forwardRef<HTMLHeadingElement, Props>(function SiteDetail(
  { run, site, fields, files, inCompare, compareFull, onToggleCompare, onBack }, titleRef,
) {
  const explain = useExplain(run, site.siteId);
  const total = run.sites.length;
  const tk = tierKey(site.tier);
  const horizons = run.horizons.filter((h) => h.siteId === site.siteId);
  const fieldLabel = (name: string) => fields?.fields.find((f) => f.name === name)?.label ?? sentence(name);
  const groupLabel = (g: string) => fields?.groups[g] ?? sentence(g);

  return (
    <article className="sd" aria-labelledby="sd-title">
      {onBack && (
        <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--borderless hig-focus sd-back" onClick={onBack}>
          <Icon name="chevron.up" size={16} strokeWidth={2.2} /><span className="hig-button__label">Back to Ranked Sites</span>
        </button>
      )}
      <header className="sd-head">
        <p className="sd-eyebrow num">{site.siteId} · Rank {site.rank} of {total}</p>
        <h2 className="sd-title" id="sd-title" tabIndex={-1} ref={titleRef}>{site.name}</h2>
        <p className="sd-sub">{siteTypeLabel(site.type)}{isNumber(site.lat) && isNumber(site.lon) ? '' : ' · Not on the map (no coordinates)'}</p>
        <div className="sd-tier"><span className={`tier tier--${tk} tier--pill`}><span className="tier__mark" aria-hidden="true" />{tierLong(site.tier)}</span></div>
        <button
          type="button"
          className={'hig-button hig-button--ios hig-button--small hig-focus hig-pressable sd-compare ' + (inCompare ? 'hig-button--bordered-prominent' : 'hig-button--bordered')}
          aria-pressed={inCompare}
          disabled={!inCompare && compareFull}
          onClick={onToggleCompare}
        >
          <Icon name={inCompare ? 'checkmark' : 'plus'} size={16} strokeWidth={2.2} />
          <span className="hig-button__label">{inCompare ? 'In Compare' : compareFull ? 'Compare Is Full (3)' : 'Add to Compare'}</span>
        </button>
      </header>

      <section className="sd-card" aria-labelledby="sd-ready">
        <h3 className="sd-card__title" id="sd-ready">Readiness</h3>
        <div className="sd-ready">
          <p className="sd-ready__score"><span className="num">{fmt.score(site.score)}</span><span className="sd-ready__of"> of 100</span></p>
          <dl className="sd-subs">
            {SUBSCORE_KEYS.map((k) => (
              <div className="sd-subs__item" key={k}>
                <dt>{subscoreLabel(k)}</dt>
                <dd className="num">{fmt.one(site.subscores[k])}</dd>
              </div>
            ))}
          </dl>
        </div>
        <p className="footnote">Subscores run from 0 to 100. The score weights them {SUBSCORE_KEYS.map((k) => `${subscoreLabel(k)} ${fmt.weight(run.subscoreWeights[`${k}_subscore`])}`).join(', ')}.</p>
      </section>

      <section className="sd-card" aria-labelledby="sd-why">
        <h3 className="sd-card__title" id="sd-why">Why This Score</h3>
        {explain.status === 'loading' && <p className="sd-loading" role="status">Reading the engine's breakdown</p>}
        {explain.status === 'error' && <p className="sd-error" role="alert">The breakdown could not be read: {explain.message}</p>}
        {explain.status === 'ready' && <ExplainCard e={explain.value} total={total} />}
        {site.absentFields.length > 0 && (
          <p className="footnote sd-absent">Not recorded for this site: {site.absentFields.map(fieldLabel).join(', ')}. Missing values never raise a score.</p>
        )}
      </section>

      <section className="sd-card" aria-labelledby="sd-ports">
        <h3 className="sd-card__title" id="sd-ports">Port Plan</h3>
        <PortPips now={site.portsNow} pathway={site.pathwayPorts} cap={site.capacityCap} />
        <dl className="sd-facts">
          <Fact label="Ports Now" value={fmt.int(site.portsNow)} />
          <Fact label="Pathway Ports" value={fmt.int(site.pathwayPorts)} />
          <Fact label="Capacity Cap" value={fmt.int(site.capacityCap)} />
        </dl>
        {site.plan && <p className="sd-plan">{site.plan}</p>}
        {horizons.length > 0 && (
          <div className="sd-scroll hig-table hig-table--ios rs-table" role="region" aria-labelledby="sd-hz-cap" tabIndex={0}>
            {/* Explicit roles: on narrow screens each horizon is a stacked row (results.css). */}
            <table className="hig-table__grid sd-hz" role="table">
              <caption id="sd-hz-cap" className="sd-caption">Ports by Horizon and Scenario</caption>
              <thead role="rowgroup">
                <tr role="row">
                  <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--leading"><span className="hig-table__heading-label">Year</span></th>
                  <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--leading"><span className="hig-table__heading-label">Scenario</span></th>
                  <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--trailing"><span className="hig-table__heading-label">Active</span></th>
                  <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--trailing"><span className="hig-table__heading-label">Pathway</span></th>
                  <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--trailing"><span className="hig-table__heading-label">Cap</span></th>
                  <th scope="col" role="columnheader" className="hig-table__heading hig-table__cell--leading"><span className="hig-table__heading-label">Strategy</span></th>
                </tr>
              </thead>
              <tbody role="rowgroup">
                {horizons.map((h) => (
                  <tr role="row" className="hig-table__row" key={`${h.year}-${h.case}`}>
                    <th scope="row" role="rowheader" className="hig-table__cell hig-table__cell--leading num sd-hz__year">{h.year}</th>
                    <td role="cell" className="hig-table__cell hig-table__cell--leading sd-hz__case">{caseLabel(h.case)}</td>
                    <td role="cell" className="hig-table__cell hig-table__cell--trailing num sd-hz__n sd-hz__active"><span className="rs-cell-label" aria-hidden="true">Active </span>{fmt.int(h.portsActive)}</td>
                    <td role="cell" className="hig-table__cell hig-table__cell--trailing num sd-hz__n sd-hz__pathway"><span className="rs-cell-label" aria-hidden="true">Pathway </span>{fmt.int(h.portsPathway)}</td>
                    <td role="cell" className="hig-table__cell hig-table__cell--trailing num sd-hz__n sd-hz__cap"><span className="rs-cell-label" aria-hidden="true">Cap </span>{fmt.int(h.capacityCap)}</td>
                    <td role="cell" className="hig-table__cell hig-table__cell--leading rs-wrap sd-hz__strategy">{sentence(h.strategy)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="sd-card" aria-labelledby="sd-ops">
        <h3 className="sd-card__title" id="sd-ops">Operations and Cost</h3>
        <dl className="sd-facts">
          <Fact label="Expected Sessions per Day" value={fmt.one(site.expectedSessionsDay)} />
          <Fact label="Utilization" value={fmt.pct(site.utilization)} />
          <Fact label="Mean Wait" value={fmt.minutes(site.meanWaitMin)} />
          {isNumber(site.installCostUsd) && <Fact label="Install Cost (Screening)" value={fmt.usd(site.installCostUsd)} />}
          <Fact label="Electrical Risk" value={site.electricalRisk ? sentence(site.electricalRisk) : 'Not recorded'} />
        </dl>
        {!isNumber(site.installCostUsd) && <p className="footnote">The engine gives no install cost for this site: an input it needs is missing.</p>}
      </section>

      <section className="sd-card" aria-labelledby="sd-conf">
        <h3 className="sd-card__title" id="sd-conf">Data Confidence</h3>
        <p className="sd-conf__level">
          <span className="sd-conf__word">{site.confidence.level ?? 'Not recorded'}</span>
          {isNumber(site.confidence.score) && <span className="num"> · {fmt.one(site.confidence.score)} of 100</span>}
        </p>
        <ul className="sd-bars" role="list">
          {Object.entries(site.confidence.breakdown).map(([g, v]) => (
            <li className="sd-bar" key={g}>
              <span className="sd-bar__label">{groupLabel(g)}</span>
              <span className="sd-bar__value num">{fmt.one(v)}</span>
              <span className="sd-bar__track" aria-hidden="true"><span className="sd-bar__fill" style={{ width: `${Math.max(0, Math.min(100, v))}%` }} /></span>
            </li>
          ))}
        </ul>
        <p className="footnote">How well each group of fields is sourced, out of 100. {CONFIDENCE_CUTOFFS}</p>
      </section>

      <section className="sd-card" aria-labelledby="sd-cap">
        <h3 className="sd-card__title" id="sd-cap">Capacity Evidence</h3>
        <CapacityLadder siteId={site.siteId} files={files} />
      </section>
    </article>
  );
});

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="sd-fact">
      <dt>{label}</dt>
      <dd className="num">{value}</dd>
    </div>
  );
}

/** One tile per port: solid for now, dashed for the pathway beyond it. Decorative; the numbers sit beside it. */
function PortPips({ now, pathway, cap }: { now: number | null; pathway: number | null; cap: number | null }) {
  if (!isNumber(now)) return null;
  const extra = isNumber(pathway) ? Math.max(0, pathway - now) : 0;
  const room = isNumber(cap) && isNumber(pathway) ? Math.max(0, cap - pathway) : 0;
  const pips = [
    ...Array.from({ length: Math.min(now, 40) }, () => 'now'),
    ...Array.from({ length: Math.min(extra, 40) }, () => 'pathway'),
    ...Array.from({ length: Math.min(room, 40) }, () => 'room'),
  ];
  return (
    <div className="sd-pips-wrap" aria-hidden="true">
      <span className="sd-pips">
        {pips.map((k, i) => <span key={i} className={`sd-pip sd-pip--${k}`}>{k === 'now' && <Icon name="bolt" size={14} strokeWidth={2} />}</span>)}
      </span>
      <span className="sd-pips__key">
        <span><span className="sd-key sd-key--now" />Now</span>
        <span><span className="sd-key sd-key--pathway" />Pathway</span>
        {room > 0 && <span><span className="sd-key sd-key--room" />Up to the cap</span>}
      </span>
    </div>
  );
}

function CapacityLadder({ siteId, files }: { siteId: string; files: Loadable<OutputFiles> }) {
  if (files.status === 'loading') return <p className="sd-loading" role="status">Reading the capacity evidence</p>;
  if (files.status === 'error') return <p className="sd-error" role="alert">The capacity evidence could not be read: {files.message}</p>;
  const ev = readCapacity(files.value).get(siteId);
  if (!ev) return <p className="footnote">The engine's scenario table has no capacity row for this site.</p>;
  const rung = ladderRung(ev.basis);
  return (
    <>
      <ol className="sd-ladder" aria-label="Capacity evidence, strongest first">
        {CAPACITY_LADDER.map((r, i) => (
          <li key={r.key} className={'sd-ladder__rung' + (i === rung ? ' is-current' : '')} aria-current={i === rung ? 'step' : undefined}>
            <span className="sd-ladder__mark" aria-hidden="true">{i === rung && <Icon name="checkmark" size={14} strokeWidth={2.6} />}</span>
            <span className="sd-ladder__label">{r.label}</span>
            {i === rung && <span className="sd-ladder__here">This site</span>}
          </li>
        ))}
      </ol>
      <p className="sd-capline">
        The engine records this site's capacity basis as <strong>{sentence(ev.basis || 'unknown')}</strong>
        {ev.confidence ? <>, with {ev.confidence === 'none' ? 'no' : sentence(ev.confidence).toLowerCase()} capacity confidence</> : null}.
        {ev.source ? <> Source: {ev.source}.</> : null}
      </p>
    </>
  );
}

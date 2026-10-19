// The report: a decision summary, then nine fixed sections (summary, ranked sites, site locations,
// site profiles, methods, assumptions, data sources, limitations, reproducibility). Static markup
// filled only from engine outputs, so the same DOM is the preview, the printout and the .html file.
// When the planner's file has columns the model does not read, a tenth section lists them and each
// profile shows the site's values, every time labelled as not in the score.

import type { Driver, Explanation, SiteResult } from '../engine/protocol';
import { accessSentence, explainSummary } from '../results/explainText';
import {
  CONFIDENCE_CUTOFFS, TIER_ORDER, andList, caseLabel, dateTime, fmt, isNumber, longDate, plural, sentence, siteTypeLabel,
  SUBSCORE_KEYS, subscoreLabel, tierKey, tierLong, tierShort,
} from '../results/format';
import { CAPACITY_LADDER, ladderRung } from '../results/data';
import { carriedNumber, carriedText, showCarried, type CarriedColumns } from '../results/carried';
import { fieldLabel, groupLabel, type ReportModel } from './reportModel';

/** A table that may scroll sideways on a narrow screen: focusable and named, so a keyboard user can scroll it. */
const scrollRegion = (label: string) => ({ role: 'region', 'aria-label': label, tabIndex: 0 }) as const;

const SECTIONS = [
  ['rp-summary', 'Summary'],
  ['rp-ranked', 'Ranked Sites'],
  ['rp-locations', 'Site Locations'],
  ['rp-profiles', 'Site Profiles'],
  ['rp-methods', 'Methods'],
  ['rp-assumptions', 'Assumptions'],
  ['rp-sources', 'Data Sources'],
  ['rp-limitations', 'Limitations'],
  ['rp-repro', 'Reproducibility'],
] as const;

const YOURS_SECTION = ['rp-yours', 'Your Columns (Not in the Score)'] as const;

function Tier({ tier, long }: { tier: string; long?: boolean }) {
  return <span className={`rp-tier rp-tier--${tierKey(tier)}`}><span className="rp-tier__mark" aria-hidden="true" />{long ? tierLong(tier) : tierShort(tier)}</span>;
}

/** A small bar drawn in SVG so it prints even when the browser leaves out background colors. */
function Bar({ value, max, scale = max, absent = false }: { value: number; max: number; scale?: number; absent?: boolean }) {
  const W = 96;
  const track = scale > 0 ? (max / scale) * W : 0;
  const fill = max > 0 ? Math.max(0, Math.min(1, value / max)) * track : 0;
  return (
    <svg className="rp-bar" width={W} height={10} viewBox={`0 0 ${W} 10`} aria-hidden="true" focusable="false">
      <rect className={absent ? 'rp-bar__track rp-bar__track--absent' : 'rp-bar__track'} x={0.5} y={0.5} width={Math.max(0, track - 1)} height={9} rx={2} />
      {!absent && fill > 0 && <rect className="rp-bar__fill" x={0.5} y={0.5} width={Math.max(0, fill - 1)} height={9} rx={2} />}
    </svg>
  );
}

function tierCounts(sites: SiteResult[]): string {
  const counts = new Map<string, { label: string; n: number }>();
  for (const k of TIER_ORDER) for (const s of sites) {
    if (tierKey(s.tier) !== k) continue;
    const c = counts.get(k) ?? { label: tierShort(s.tier), n: 0 };
    c.n += 1;
    counts.set(k, c);
  }
  return andList([...counts.values()].map((c) => `${c.n} ${c.label}`));
}

export function ReportDocument({ m }: { m: ReportModel }) {
  const { run } = m;
  const N = run.sites.length;
  const top = run.sites[0];
  const verified = [...m.capacity.values()].filter((c) => c.basis.startsWith('verified')).length;
  const hasCapacity = m.capacity.size > 0;

  return (
    <article className="rp" aria-labelledby="rp-title" lang="en">
      <header className="rp-cover">
        <p className="rp-eyebrow">EV Charging Site Readiness Report</p>
        <h1 className="rp-title" id="rp-title">{m.place}</h1>
        <p className="rp-meta">
          {plural(N, 'candidate site')} · data confidence judged as of {longDate(run.asOf)} · run {run.runId}
        </p>
      </header>

      <section className="rp-decision" aria-labelledby="rp-decision-title">
        <h2 className="rp-decision__title" id="rp-decision-title">Decision Summary</h2>
        <ul className="rp-decision__list">
          {top && <li>{top.name} ranks first of {N} with a readiness score of {fmt.score(top.score)} of 100 ({tierLong(top.tier)}).</li>}
          <li>By tier: {tierCounts(run.sites)}.</li>
          <li>The plan installs {plural(run.totals.starterPorts2026, 'starter port')} now and prepares {plural(run.totals.pathwayPorts, 'pathway port')} for later growth.</li>
          <li>Data confidence is High at {run.totals.highConfidenceSites} of {N} sites.</li>
          {hasCapacity && <li>Electrical capacity is confirmed by a utility or facility at {verified} of {N} sites; elsewhere it is a placeholder or proxy.</li>}
        </ul>
        <p className="rp-claims"><strong>What these numbers are:</strong> {run.claims}</p>
      </section>

      <nav className="rp-toc" aria-label="Report sections">
        <h2 className="rp-toc__title">Contents</h2>
        <ol>{[...SECTIONS, ...(m.carried ? [YOURS_SECTION] : [])].map(([id, label]) => <li key={id}><a href={`#${id}`}>{label}</a></li>)}</ol>
      </nav>

      <Summary m={m} />
      <Ranked m={m} />
      <Locations m={m} />
      <Profiles m={m} />
      <Methods m={m} />
      <Assumptions m={m} />
      <Sources m={m} />
      <Limitations m={m} verified={verified} />
      <Repro m={m} />
      {m.carried && <YourColumns m={m} carried={m.carried} />}

      <footer className="rp-foot">
        <p>Made with the EV-SIENT Planner, which ran the model on the planner's own device. Planning support, not engineering, permitting or budget advice.</p>
      </footer>
    </article>
  );
}

function H2({ n, id, children }: { n: number; id: string; children: string }) {
  return <h2 className="rp-h2" id={id}><span className="rp-h2__n">{n}.</span> {children}</h2>;
}

function Summary({ m }: { m: ReportModel }) {
  const { run } = m;
  const t = run.totals;
  return (
    <section className="rp-section" aria-labelledby="rp-summary">
      <H2 n={1} id="rp-summary">Summary</H2>
      <dl className="rp-totals">
        <div><dt>Sites Ranked</dt><dd>{fmt.int(t.sites)}</dd></div>
        <div><dt>Starter Ports Now</dt><dd>{fmt.int(t.starterPorts2026)}</dd></div>
        <div><dt>Pathway Ports</dt><dd>{fmt.int(t.pathwayPorts)}</dd></div>
        <div><dt>High-Confidence Sites</dt><dd>{fmt.int(t.highConfidenceSites)} of {fmt.int(t.sites)}</dd></div>
      </dl>
      <p>
        The EV-SIENT model ranked {plural(t.sites, 'site')} by a readiness score from 0 to 100, built from four subscores:{' '}
        {andList(SUBSCORE_KEYS.map((k) => `${subscoreLabel(k).toLowerCase()} (${fmt.weight(run.subscoreWeights[`${k}_subscore`])})`))}.
        Scores run from {fmt.score(run.sites[0]?.score)} at rank 1 to {fmt.score(run.sites[run.sites.length - 1]?.score)} at rank {run.sites.length}.
      </p>
    </section>
  );
}

function Ranked({ m }: { m: ReportModel }) {
  return (
    <section className="rp-section" aria-labelledby="rp-ranked">
      <H2 n={2} id="rp-ranked">Ranked Sites</H2>
      <div className="rp-tablewrap" {...scrollRegion('Ranked sites table')}>
        <table className="rp-table">
          <caption>All sites in rank order. Subscores and data confidence run from 0 to 100.</caption>
          <thead>
            <tr>
              <th scope="col" className="rp-num">Rank</th>
              <th scope="col">Site</th>
              <th scope="col" className="rp-num">Score</th>
              <th scope="col">Tier</th>
              {SUBSCORE_KEYS.map((k) => <th scope="col" className="rp-num" key={k}>{subscoreLabel(k)}</th>)}
              <th scope="col">Data Confidence</th>
              <th scope="col" className="rp-num">Ports Now</th>
              <th scope="col" className="rp-num">Pathway</th>
            </tr>
          </thead>
          <tbody>
            {m.run.sites.map((s) => (
              <tr key={s.siteId}>
                <td className="rp-num">{s.rank}</td>
                <th scope="row"><span className="rp-site">{s.name}</span><span className="rp-id">{s.siteId}</span></th>
                <td className="rp-num rp-strong">{fmt.score(s.score)}</td>
                <td><Tier tier={s.tier} /></td>
                {SUBSCORE_KEYS.map((k) => <td className="rp-num" key={k}>{fmt.one(s.subscores[k])}</td>)}
                <td>{s.confidence.level ?? 'Not recorded'}{isNumber(s.confidence.score) ? ` (${fmt.one(s.confidence.score)})` : ''}</td>
                <td className="rp-num">{fmt.int(s.portsNow)}</td>
                <td className="rp-num">{fmt.int(s.pathwayPorts)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="rp-note">Tier marks: a circle is Tier 1, a square Tier 2, a bar Tier 3, a diamond High Review and a triangle Special Use.</p>
    </section>
  );
}

function Locations({ m }: { m: ReportModel }) {
  const pts = m.run.sites.filter((s) => isNumber(s.lat) && isNumber(s.lon));
  const missing = m.run.sites.filter((s) => !(isNumber(s.lat) && isNumber(s.lon)));
  const W = 640, H = 380, P = 36;
  let plot = null;
  if (pts.length) {
    const meanLat = pts.reduce((a, s) => a + s.lat!, 0) / pts.length;
    const k = Math.cos((meanLat * Math.PI) / 180);
    const xs = pts.map((s) => s.lon! * k), ys = pts.map((s) => s.lat!);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    const span = Math.max(x1 - x0, y1 - y0, 1e-6);
    const scale = Math.min((W - 2 * P) / Math.max(x1 - x0, span * 0.01), (H - 2 * P) / Math.max(y1 - y0, span * 0.01));
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    const px = (s: SiteResult) => W / 2 + (s.lon! * k - cx) * scale;
    const py = (s: SiteResult) => H / 2 - (s.lat! - cy) * scale;
    const kmAcross = ((W / scale) * 111.32);
    plot = (
      <svg className="rp-plot" viewBox={`0 0 ${W} ${H}`} role="img" aria-labelledby="rp-plot-cap" focusable="false">
        <rect className="rp-plot__frame" x={0.5} y={0.5} width={W - 1} height={H - 1} rx={6} />
        {[...pts].reverse().map((s) => (
          <g key={s.siteId} className="rp-plot__pt">
            <circle cx={px(s)} cy={py(s)} r={12} />
            <text x={px(s)} y={py(s)} dy="0.35em" textAnchor="middle">{s.rank}</text>
          </g>
        ))}
        <text className="rp-plot__note" x={12} y={H - 12}>North is up · about {fmt.one(kmAcross)} km across</text>
      </svg>
    );
  }
  return (
    <section className="rp-section" aria-labelledby="rp-locations">
      <H2 n={3} id="rp-locations">Site Locations</H2>
      {plot ? (
        <figure className="rp-figure">
          {plot}
          <figcaption id="rp-plot-cap">
            Sites plotted by their recorded latitude and longitude, numbered by rank, with no basemap. {plural(pts.length, 'site')} plotted
            {missing.length ? `; ${plural(missing.length, 'site')} without coordinates ${missing.length === 1 ? 'is' : 'are'} listed below` : ''}. The table gives each position.
          </figcaption>
        </figure>
      ) : <p>No site has coordinates, so there is nothing to plot.</p>}
      <div className="rp-tablewrap" {...scrollRegion('Site locations table')}>
        <table className="rp-table rp-table--compact">
          <caption>Site positions (WGS84 decimal degrees).</caption>
          <thead><tr><th scope="col" className="rp-num">Rank</th><th scope="col">Site</th><th scope="col">Type</th><th scope="col" className="rp-num">Latitude</th><th scope="col" className="rp-num">Longitude</th></tr></thead>
          <tbody>
            {m.run.sites.map((s) => (
              <tr key={s.siteId}>
                <td className="rp-num">{s.rank}</td>
                <th scope="row">{s.name}</th>
                <td>{siteTypeLabel(s.type)}</td>
                <td className="rp-num">{isNumber(s.lat) ? s.lat.toFixed(5) : 'Not recorded'}</td>
                <td className="rp-num">{isNumber(s.lon) ? s.lon.toFixed(5) : 'Not recorded'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function DriverRows({ e }: { e: Explanation }) {
  const scale = Math.max(...e.drivers.map((d) => d.max), 1);
  const note = (d: Driver) => (d.absent ? 'Not recorded: earns no credit' : d.inverted ? 'Lower is better' : '');
  return (
    <table className="rp-table rp-table--compact rp-drivers">
      <caption>Readiness points by driver. Each driver's points against the most it can add; the drivers add up to the score.</caption>
      <thead>
        <tr><th scope="col">Driver</th><th scope="col" className="rp-num">Points</th><th scope="col" className="rp-num">Possible</th><th scope="col"><span className="hig-visually-hidden">Bar</span></th><th scope="col">Note</th></tr>
      </thead>
      {e.subscores.map((sub) => (
        <tbody key={sub.key}>
          <tr className="rp-group">
            <th scope="rowgroup" colSpan={5}>{sub.label}: {fmt.points(sub.points)} of {fmt.points(sub.max)} points (weight {fmt.weight(sub.weight)})</th>
          </tr>
          {e.drivers.filter((d) => d.subscore === sub.key).map((d) => (
            <tr key={d.key}>
              <th scope="row">{d.label}</th>
              <td className="rp-num">{d.absent ? '0.0' : fmt.signed(d.points)}</td>
              <td className="rp-num">{fmt.points(d.max)}</td>
              <td><Bar value={d.points} max={d.max} scale={scale} absent={d.absent} /></td>
              <td>{note(d)}</td>
            </tr>
          ))}
        </tbody>
      ))}
    </table>
  );
}

function Profiles({ m }: { m: ReportModel }) {
  const N = m.run.sites.length;
  return (
    <section className="rp-section" aria-labelledby="rp-profiles">
      <H2 n={4} id="rp-profiles">Site Profiles</H2>
      <p>One profile per site, in rank order. Every number is the engine's.</p>
      {m.run.sites.map((s) => {
        const e = m.explains.get(s.siteId);
        const hz = m.run.horizons.filter((h) => h.siteId === s.siteId);
        const strategies = [...new Set(hz.map((h) => h.strategy))];
        const cap = m.capacity.get(s.siteId);
        const hid = `rp-site-${s.siteId}`;
        return (
          <section className="rp-profile" key={s.siteId} aria-labelledby={hid}>
            <h3 className="rp-h3" id={hid}>{s.rank}. {s.name}</h3>
            <p className="rp-profile__meta">{s.siteId} · {siteTypeLabel(s.type)} · <Tier tier={s.tier} long /></p>
            {e ? (
              <>
                <p className="rp-lead">{explainSummary(e, N).sentences.join(' ')}</p>
                {accessSentence(e) && <p className="rp-callout">{accessSentence(e)}</p>}
                <div className="rp-tablewrap" {...scrollRegion(`Score breakdown table for ${s.name}`)}><DriverRows e={e} /></div>
              </>
            ) : <p>The engine's breakdown for this site was not available.</p>}
            {s.absentFields.length > 0 && <p className="rp-note">Not recorded for this site: {s.absentFields.map((f) => fieldLabel(m, f)).join(', ')}. Missing values never raise a score.</p>}

            <h4 className="rp-h4">Port Plan</h4>
            <p>{fmt.int(s.portsNow)} ports now, {fmt.int(s.pathwayPorts)} on the pathway, capacity cap {fmt.int(s.capacityCap)}.{s.plan ? ` ${s.plan}` : ''}</p>
            {hz.length > 0 && (
              <div className="rp-tablewrap" {...scrollRegion(`Port plan table for ${s.name}`)}>
                <table className="rp-table rp-table--compact">
                  <caption>Ports by horizon and scenario.{strategies.length === 1 ? ` Strategy in every row: ${sentence(strategies[0])}.` : ''}</caption>
                  <thead>
                    <tr><th scope="col">Year</th><th scope="col">Scenario</th><th scope="col" className="rp-num">Active</th><th scope="col" className="rp-num">Pathway</th><th scope="col" className="rp-num">Cap</th>{strategies.length > 1 && <th scope="col">Strategy</th>}</tr>
                  </thead>
                  <tbody>
                    {hz.map((h) => (
                      <tr key={`${h.year}-${h.case}`}>
                        <th scope="row">{h.year}</th><td>{caseLabel(h.case)}</td>
                        <td className="rp-num">{fmt.int(h.portsActive)}</td><td className="rp-num">{fmt.int(h.portsPathway)}</td><td className="rp-num">{fmt.int(h.capacityCap)}</td>
                        {strategies.length > 1 && <td>{sentence(h.strategy)}</td>}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="rp-cols">
              <div>
                <h4 className="rp-h4">Operations and Cost</h4>
                <dl className="rp-dl">
                  <div><dt>Expected sessions per day</dt><dd>{fmt.one(s.expectedSessionsDay)}</dd></div>
                  <div><dt>Utilization</dt><dd>{fmt.pct(s.utilization)}</dd></div>
                  <div><dt>Mean wait</dt><dd>{fmt.minutes(s.meanWaitMin)}</dd></div>
                  <div><dt>Install cost (screening)</dt><dd>{isNumber(s.installCostUsd) ? fmt.usd(s.installCostUsd) : 'Not given: an input is missing'}</dd></div>
                  <div><dt>Electrical risk</dt><dd>{s.electricalRisk ? sentence(s.electricalRisk) : 'Not recorded'}</dd></div>
                </dl>
              </div>
              <div>
                <h4 className="rp-h4">Data Confidence: {s.confidence.level ?? 'Not recorded'}{isNumber(s.confidence.score) ? ` (${fmt.one(s.confidence.score)} of 100)` : ''}</h4>
                <dl className="rp-dl">
                  {Object.entries(s.confidence.breakdown).map(([g, v]) => (
                    <div key={g}><dt>{groupLabel(m, g)}</dt><dd>{fmt.one(v)} <Bar value={v} max={100} /></dd></div>
                  ))}
                </dl>
              </div>
            </div>

            <h4 className="rp-h4">Capacity Evidence</h4>
            {cap ? (
              <p>
                {CAPACITY_LADDER[ladderRung(cap.basis)].label}: rung {ladderRung(cap.basis) + 1} of {CAPACITY_LADDER.length} ({andList(CAPACITY_LADDER.map((r) => r.label))}, strongest first).
                The engine records the capacity basis as {sentence(cap.basis || 'unknown').toLowerCase()}{cap.confidence ? `, capacity confidence ${cap.confidence}` : ''}.{cap.source ? ` Source: ${cap.source}.` : ''}
              </p>
            ) : <p>The scenario table has no capacity row for this site.</p>}

            {m.carried && (
              <>
                <h4 className="rp-h4">Your Columns (Not in the Score)</h4>
                <p className="rp-note">From the planner's file, as written. The model does not read these, so they played no part in this site's score, rank or port plan.</p>
                <dl className="rp-dl rp-dl--yours">
                  {m.carried.columns.map((c, k) => <div key={c.name}><dt>{c.name}</dt><dd>{showCarried(c, carriedText(m.carried!, s.siteId, k))}</dd></div>)}
                </dl>
              </>
            )}
          </section>
        );
      })}
    </section>
  );
}

function Methods({ m }: { m: ReportModel }) {
  const any = m.explains.values().next().value as Explanation | undefined;
  return (
    <section className="rp-section" aria-labelledby="rp-methods">
      <H2 n={5} id="rp-methods">Methods</H2>
      <p>
        The readiness score is the weighted sum of four subscores, each from 0 to 100. Each subscore is built from drivers: values from the
        planner's file, scaled against a fixed set of anchors (for a lower-is-better driver, the scale is turned around). A driver adds its subscore weight
        times 100 times its own weight times its credit, so the drivers add up to the score. A value nobody recorded earns no credit; it is never filled in.
        A site not recorded as open to the public has its demand counted at 65%.
      </p>
      <div className="rp-tablewrap" {...scrollRegion('Subscore weights table')}>
        <table className="rp-table">
          <caption>Subscore weights and what each subscore measures.</caption>
          <thead><tr><th scope="col">Subscore</th><th scope="col" className="rp-num">Weight</th><th scope="col">What it measures (share of the whole score)</th></tr></thead>
          <tbody>
            {Object.entries(m.run.subscoreWeights).map(([k, w]) => {
              const key = k.replace(/_subscore$/, '');
              const drivers = any?.drivers.filter((d) => d.subscore === key) ?? [];
              return (
                <tr key={k}>
                  <th scope="row">{subscoreLabel(k)}</th>
                  <td className="rp-num">{fmt.weight(w)}</td>
                  <td>{drivers.length ? drivers.map((d) => `${d.label} (${fmt.one(d.weight * 100)}%)${d.inverted ? ', lower is better' : ''}`).join('; ') : 'See the engine documentation.'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p>
        Data confidence scores how well each group of fields is sourced, from 0 to 100, weighted by group. {CONFIDENCE_CUTOFFS}{' '}
        The port plan sizes starter ports for today and a future-ready pathway for the {andList((m.manifest?.conventions?.horizons ?? []).map(String)) || 'later'} horizons,
        under the scenarios {andList((m.manifest?.conventions?.cases ?? []).map(caseLabel)) || 'the engine reports'}.
      </p>
    </section>
  );
}

function Assumptions({ m }: { m: ReportModel }) {
  const { run } = m;
  const a = m.assumptions;
  const rows: [string, string][] = [];
  if (a?.economics?.tariff_usd_per_kwh !== undefined) rows.push(['Electricity tariff (screening)', `${fmt.two(a.economics.tariff_usd_per_kwh)} USD per kWh`]);
  if (a?.economics?.hardware_usd_per_port !== undefined) rows.push(['Hardware per port (screening)', fmt.usd(a.economics.hardware_usd_per_port)]);
  if (a?.economics?.discount_rate_real !== undefined) rows.push(['Real discount rate', fmt.pct(a.economics.discount_rate_real)]);
  if (a?.energy_per_session_kwh?.value !== undefined) rows.push(['Energy per session', `${fmt.one(a.energy_per_session_kwh.value)} kWh${a.energy_per_session_kwh.label ? ` (${a.energy_per_session_kwh.label})` : ''}`]);
  if (a?.emissions?.grid_factor_value !== undefined) rows.push(['Grid emission factor', `${fmt.one(a.emissions.grid_factor_value)} ${a.emissions.grid_factor_units ?? ''}${a.emissions.grid_factor_source ? `, ${a.emissions.grid_factor_source}` : ''}`]);
  if (a?.demand_model?.status) rows.push(['Demand model status', sentence(a.demand_model.status)]);
  if (a?.growth_multipliers) rows.push(['Growth multipliers', Object.entries(a.growth_multipliers).map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`).join('; ')]);
  if (a?.trigger_policy?.policy_status) rows.push(['Expansion trigger policy', `${sentence(a.trigger_policy.policy_status)}${a.trigger_policy.utilization_threshold !== undefined ? `; utilization ${fmt.pct(a.trigger_policy.utilization_threshold)}` : ''}${a.trigger_policy.wait_threshold_min !== undefined ? `, wait ${fmt.minutes(a.trigger_policy.wait_threshold_min)}` : ''}`]);
  if (a?.capacity) rows.push(['Electrical capacity', a.capacity]);
  return (
    <section className="rp-section" aria-labelledby="rp-assumptions">
      <H2 n={6} id="rp-assumptions">Assumptions</H2>
      <p className="rp-claims"><strong>The engine's statement:</strong> {run.claims}</p>
      <h3 className="rp-h3">Defaults the Engine Applied</h3>
      {run.defaults.length ? <ul>{run.defaults.map((d, i) => <li key={i}>{d}</li>)}</ul> : <p>None: every optional input was supplied.</p>}
      <h3 className="rp-h3">Notes</h3>
      {run.notes.length ? <ul>{run.notes.map((d, i) => <li key={i}>{d}</li>)}</ul> : <p>None.</p>}
      <h3 className="rp-h3">Costs Withheld for Missing Inputs</h3>
      {run.costsWithheld.length ? <ul>{run.costsWithheld.map((d, i) => <li key={i}>{d}</li>)}</ul> : <p>None.</p>}
      {rows.length > 0 && (
        <>
          <h3 className="rp-h3">Constants a Reviewer May Challenge</h3>
          <div className="rp-tablewrap" {...scrollRegion('Constants table')}>
            <table className="rp-table rp-table--compact">
              <caption>From the run's assumptions file (results/contract/assumptions.json).</caption>
              <thead><tr><th scope="col">Assumption</th><th scope="col">Value</th></tr></thead>
              <tbody>{rows.map(([k, v]) => <tr key={k}><th scope="row">{k}</th><td>{v}</td></tr>)}</tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}

function Sources({ m }: { m: ReportModel }) {
  const c = m.cohort;
  const g = m.manifest?.grid_factor;
  return (
    <section className="rp-section" aria-labelledby="rp-sources">
      <H2 n={7} id="rp-sources">Data Sources</H2>
      <div className="rp-tablewrap" {...scrollRegion('Data sources table')}>
        <table className="rp-table rp-table--compact">
          <caption>Where the inputs came from, as the planner recorded them when the file was accepted.</caption>
          <thead><tr><th scope="col">Source</th><th scope="col">Organisation</th><th scope="col">Date</th><th scope="col">Detail</th></tr></thead>
          <tbody>
            <tr>
              <th scope="row">{c?.source_file || m.table?.fileName || 'The planner\'s file'}</th>
              <td>{c?.source_org ? sentence(c.source_org) : m.details.sourceOrg || 'Not stated'}</td>
              <td>{c?.source_date || m.details.sourceDate || 'Not stated'}</td>
              <td className="rp-break">{c?.source_sha256 ? `SHA-256 ${c.source_sha256}` : ''}{c?.accepted_utc ? `; accepted ${dateTime(c.accepted_utc)}` : ''}</td>
            </tr>
            {g?.source && (
              <tr>
                <th scope="row">Grid emission factor</th>
                <td>{g.source.split(' ')[0]}</td>
                <td>{g.vintage ?? ''}</td>
                <td>{g.source}{isNumber(g.value_lb_per_mwh) ? `; ${fmt.one(g.value_lb_per_mwh)} lb CO2e per MWh` : ''}</td>
              </tr>
            )}
            {m.publicSources.map((p) => (
              <tr key={`${p.hubVersion}-${p.title}`}>
                <th scope="row">{p.title}</th>
                <td>EV-SIENT public data hub, release {p.hubVersion}</td>
                <td>{p.sourceDate}</td>
                <td>{`${p.cells} ${p.cells === 1 ? 'value' : 'values'} the planner accepted for ${p.fields.map((f) => fieldLabel(m, f)).join(', ')}; vintage ${p.vintage}. ${p.licence}`}</td>
              </tr>
            ))}
            {Object.keys(m.manifest?.inputs ?? {}).filter((f) => f.startsWith('anchor_set')).map((f) => (
              <tr key={f}><th scope="row">{f}</th><td>EV-SIENT reference study</td><td>Fixed with the engine</td><td>The anchors every score is scaled against.</td></tr>
            ))}
          </tbody>
        </table>
      </div>
      {m.details.reviewer && <p>Reviewed by {m.details.reviewer}.</p>}
      <p className="rp-note">Field-by-field provenance is in inputs/provenance.csv in the model outputs download.{m.publicSources.length > 0 && ' Every value filled from public data, with its source and method, is in inputs/public_data_fills.csv.'}</p>
    </section>
  );
}

function Limitations({ m, verified }: { m: ReportModel; verified: number }) {
  const { run } = m;
  const N = run.sites.length;
  const withAbsent = run.sites.filter((s) => s.absentFields.length > 0).length;
  const unlocated = run.sites.filter((s) => !(isNumber(s.lat) && isNumber(s.lon))).length;
  const noCost = run.sites.filter((s) => !isNumber(s.installCostUsd)).length;
  return (
    <section className="rp-section" aria-labelledby="rp-limitations">
      <H2 n={8} id="rp-limitations">Limitations</H2>
      <ul>
        <li>These are planning-support screening results. Nothing in this report is an engineering, permitting, budget or procurement value, and nothing has been approved.</li>
        {m.capacity.size > 0 && <li>Electrical capacity is confirmed by a utility or facility at {verified} of {N} sites. Where it is not, the port plan's capacity is a placeholder until confirmed.</li>}
        {m.assumptions?.demand_model?.status && <li>The demand model's status is "{sentence(m.assumptions.demand_model.status).toLowerCase()}": expected sessions, utilization and waits are estimates, not observations.</li>}
        <li>Data confidence is High at {run.totals.highConfidenceSites} of {N} sites. {CONFIDENCE_CUTOFFS}</li>
        <li>{withAbsent ? `${plural(withAbsent, 'site')} ${withAbsent === 1 ? 'has' : 'have'} at least one scored field not recorded; those drivers earn no credit, so the score may understate them.` : 'Every site has every scored field recorded.'}</li>
        {unlocated > 0 && <li>{plural(unlocated, 'site')} {unlocated === 1 ? 'has' : 'have'} no coordinates and {unlocated === 1 ? 'is' : 'are'} not plotted.</li>}
        {noCost > 0 && <li>{plural(noCost, 'site')} {noCost === 1 ? 'has' : 'have'} no install cost because an input the cost needs is missing.</li>}
        <li>Tier 1 is relative to this set of sites: the same score can earn a different tier in another run.</li>
      </ul>
    </section>
  );
}

function Repro({ m }: { m: ReportModel }) {
  const { run, info, manifest } = m;
  const rows: [string, string][] = [
    ['Run ID', run.runId],
    ['Model mode', run.mode],
    ['Generated', dateTime(run.generatedAt)],
    ['Data confidence judged as of', run.asOf],
    ['Engine version', info ? info.engine.version : 'Not available'],
    ['Engine SHA-256', info?.engine.sha256 || 'Not available'],
    ['Engine protocol', info ? String(info.protocol) : 'Not available'],
    ['Python runtime', info ? `Pyodide ${info.pyodide}, Python ${info.python}` : 'Not available'],
    ['Python packages', info ? Object.entries(info.packages).map(([k, v]) => `${k} ${v}`).join(', ') : 'Not available'],
  ];
  if (manifest?.model_version) rows.push(['Model version', manifest.model_version]);
  if (manifest?.contract_version) rows.push(['Data contract version', manifest.contract_version]);
  const hashes = [
    ...Object.entries(manifest?.inputs ?? {}).map(([f, h]) => [`inputs/${f}`, h]),
    ...Object.entries(manifest?.tables ?? {}).map(([f, h]) => [`results/contract/${f}`, h]),
  ];
  return (
    <section className="rp-section" aria-labelledby="rp-repro">
      <H2 n={9} id="rp-repro">Reproducibility</H2>
      <p>To re-run this result, open the project file in the EV-SIENT Planner, or run the same engine version on the same inputs with the same as-of date, then compare the hashes below.</p>
      <dl className="rp-dl rp-dl--wide">
        {rows.map(([k, v]) => <div key={k}><dt>{k}</dt><dd className="rp-break">{v}</dd></div>)}
      </dl>
      {hashes.length > 0 && (
        <div className="rp-tablewrap" {...scrollRegion('File hashes table')}>
          <table className="rp-table rp-table--compact rp-hashes">
            <caption>File hashes from the run's contract manifest (results/contract/contract_manifest.json).</caption>
            <thead><tr><th scope="col">File</th><th scope="col">SHA-256</th></tr></thead>
            <tbody>{hashes.map(([f, h]) => <tr key={f}><th scope="row">{f}</th><td className="rp-mono rp-break">{h}</td></tr>)}</tbody>
          </table>
        </div>
      )}
    </section>
  );
}

/** What each of Your Columns holds: its range, or its most common values. */
function columnSummary(c: CarriedColumns, k: number, ids: string[]): string {
  const col = c.columns[k];
  const values = ids.map((id) => carriedText(c, id, k)).filter(Boolean);
  if (!values.length) return 'Blank at every site';
  if (col.numeric) {
    const nums = values.map((v) => [carriedNumber(v)!, v] as const).sort((a, b) => a[0] - b[0]);
    return `${showCarried(col, nums[0][1])} to ${showCarried(col, nums[nums.length - 1][1])}`;
  }
  const tally = new Map<string, number>();
  for (const v of values) tally.set(v, (tally.get(v) ?? 0) + 1);
  if (tally.size > 12) return `${tally.size} different values`;
  const top = [...tally.entries()].sort((a, b) => b[1] - a[1]);
  return top.slice(0, 4).map(([v, n]) => `${v} (${n})`).join(', ') + (top.length > 4 ? `, and ${top.length - 4} more` : '');
}

function YourColumns({ m, carried }: { m: ReportModel; carried: CarriedColumns }) {
  const ids = m.run.sites.map((s) => s.siteId);
  const N = ids.length;
  return (
    <section className="rp-section" aria-labelledby={YOURS_SECTION[0]}>
      <H2 n={SECTIONS.length + 1} id={YOURS_SECTION[0]}>{YOURS_SECTION[1]}</H2>
      <p>
        The planner's file has {plural(carried.columns.length, 'column')} the model does not read. {carried.columns.length === 1 ? 'It is' : 'They are'} kept
        with each site by its site ID and shown as written, in each site profile above. <strong>{carried.columns.length === 1 ? 'It is' : 'They are'} not in the score:</strong> no
        score, rank, tier or port plan in this report used {carried.columns.length === 1 ? 'it' : 'them'}.
      </p>
      <div className="rp-tablewrap" {...scrollRegion('Your columns table')}>
        <table className="rp-table rp-table--compact">
          <caption>Your columns, not in the score, in the order of the file.</caption>
          <thead><tr><th scope="col">Column</th><th scope="col">Holds</th><th scope="col" className="rp-num">Sites With a Value</th><th scope="col">Values</th></tr></thead>
          <tbody>
            {carried.columns.map((c, k) => (
              <tr key={c.name}>
                <th scope="row">{c.name}</th>
                <td>{c.numeric ? 'Numbers' : 'Text'}</td>
                <td className="rp-num">{ids.filter((id) => carriedText(carried, id, k)).length} of {N}</td>
                <td>{columnSummary(carried, k, ids)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="rp-note">Every value, site by site, is in the Ranked Sites download (.csv) and on the Your Columns sheet of the Excel workbook.</p>
    </section>
  );
}

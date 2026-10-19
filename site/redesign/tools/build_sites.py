"""Write www/data/sites.json from the authoritative canonical data contract, data/contract/v3.

Usage: PYTHONPATH=src python3 site/redesign/tools/build_sites.py [--check]

Contract v3 (DEC-027) gives every published figure it carries: site names, places and types,
install-now and future-ready ports, peak waits, data confidence, plan notes, active ports by
horizon and scenario, the staged and overbuild lifecycle costs, avoided overbuild cost and avoided
CO2e. Three things the public pages show are not contract fields, so they come from the model
itself, never typed in:

- rank, readiness score and tier: the canonical milestone2_v3 results
  (tests/fixture_milestone2_v3_site_results.csv, the same results build_scoring.py reads);
- mean wait: fcf_m2.peak_wait.simulate_waits (seeded) at the contract's install-now ports (the
  peak wait is recomputed the same way so it is rounded once, and must match the contract's);
- the deferred (DEF) lifecycle cost: fcf_m2.economics.compare_cases on the contract's port plan.
  The same call's staged and overbuild costs must equal the contract's, site by site, or nothing
  is written.

Photos and their credits are page presentation, not model output, and are carried over from the
current sites.json.

Only outputs are written (DEC-016). With --check it writes nothing and exits 1 if the file on disk
differs from what it would write.
"""
import csv
import json
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src'))

from fcf_m2 import economics, peak_wait, workflow  # noqa: E402
from fcf_m2.config import BASELINE_YEAR, V3_HORIZONS  # noqa: E402

CHECK = '--check' in sys.argv
CONTRACT = os.path.join(REPO, 'data', 'contract', 'v3')
RESULTS = os.path.join(REPO, 'tests', 'fixture_milestone2_v3_site_results.csv')
OUT = os.path.join(REPO, 'site', 'redesign', 'www', 'data', 'sites.json')

JURISDICTION = {'fairfax': 'Fairfax', 'pwc': 'Prince William'}
TIER_KEY = {
    'Tier 1 - advance to site screening': 'tier1',
    'High-review candidate': 'high-review',
    'Tier 2 - promising candidate, refine data': 'tier2',
    'Tier 3 - lower priority / monitor': 'tier3',
    'Low public-priority / special-use': 'special',
}
SCENARIOS = ['baseline', 'base', 'high', 'stress_combined']
CASES = ['DEF', 'OVB', 'STG']
NOTE = 'Avoided CO2e: higher is better. Costs are screening-class planning estimates. Capacity is an unverified placeholder at all twelve sites.'


def rows(name):
    with open(os.path.join(CONTRACT, name), encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def one_value(values, what):
    values = set(values)
    if len(values) != 1:
        raise SystemExit(f'contract v3: expected one {what}, found {sorted(values)}')
    return values.pop()


def main():
    manifest = json.load(open(os.path.join(CONTRACT, 'contract_manifest.json'), encoding='utf-8'))
    if not manifest.get('authoritative'):
        raise SystemExit('contract v3 is not marked authoritative')
    scen = rows('scenario_table.csv')
    site_table = {r['site_id']: r for r in rows('site_table.csv')}
    with open(RESULTS, encoding='utf-8', newline='') as f:
        results = {r['site_id']: r for r in csv.DictReader(f)}
    if set(results) != set(site_table):
        raise SystemExit('the canonical results and contract v3 name different sites')
    current = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {'sites': []}
    photos = {s['id']: (s.get('image'), s.get('imageCredit')) for s in current.get('sites', [])}

    by = {}
    for r in scen:
        by[(r['site_id'], int(r['horizon_year']), r['scenario_name'])] = r

    sites, def_total, case_totals = [], {}, {}
    for sid, res in results.items():
        st = site_table[sid]
        base = by[(sid, BASELINE_YEAR, 'baseline')]
        starter = int(base['ports_active'])
        pathway = int(one_value((r['ports_pathway_capacity'] for r in scen if r['site_id'] == sid), f'{sid} pathway'))

        # Mean wait: the model's seeded simulation at the contract's install-now ports. Peak wait: the
        # model's peak-window figure, which the contract stores to 2 decimals; it is recomputed so the
        # 1-decimal value is not rounded twice, and must agree with the contract.
        dwell_min = float(res['avg_dwell_min'])
        dwell_hr = dwell_min / 60 if dwell_min > 0 else 2
        sim = peak_wait.simulate_waits(float(res['expected_sessions_day']), dwell_hr, float(res['hours_open']), starter)
        peak, _ = peak_wait.peak_window_wait(float(res['expected_sessions_day']), dwell_hr, float(res['hours_open']), starter)
        if abs(round(peak, 2) - float(base['peak_wait_minutes'])) > 1e-9:
            raise SystemExit(f'{sid}: model peak wait {peak} differs from contract v3 {base["peak_wait_minutes"]}')

        # Lifecycle costs on the contract's plan; staged and overbuild must match the contract.
        staged = {hy: int(by[(sid, hy, 'base')]['ports_active']) for hy in V3_HORIZONS}
        inputs = economics.SiteCostInputs(
            site_id=sid, ports_now=starter, ports_pathway=pathway, staged_targets=staged,
            trenching_ft=float(res['trenching_ft']), trench_cost_per_ft=float(res['trench_cost_per_ft']),
            service_upgrade_cost_usd=float(res['service_upgrade_cost_usd']),
            sessions_day_by_year=workflow._sessions_by_year(float(res['expected_sessions_day']), 'base'))
        for c in economics.compare_cases(inputs, 'base').to_dict('records'):
            hy, case = int(c['horizon_year']), c['cost_case']
            row = by[(sid, hy, 'base')]
            if row['lifecycle_cost_npv_usd'] == '':
                continue  # a site the contract withholds costs for is left out of every case
            npv, avoided = float(row['lifecycle_cost_npv_usd']), float(row['avoided_overbuild_cost_usd'])
            want = {'STG': npv, 'OVB': npv + avoided}.get(case)
            if want is not None and abs(want - c['lifecycle_cost_npv_usd']) > 0.5:
                raise SystemExit(f'{sid} {hy} {case}: model gives {c["lifecycle_cost_npv_usd"]}, contract v3 gives {want}')
            if case == 'STG' and abs(avoided - c['avoided_overbuild_cost_usd']) > 0.5:
                raise SystemExit(f'{sid} {hy}: avoided cost differs from contract v3')
            t = case_totals.setdefault((hy, case), [0.0, 0.0])
            t[0] += c['lifecycle_cost_npv_usd']
            t[1] += c['avoided_overbuild_cost_usd']

        tier = res['recommendation_tier']
        if tier not in TIER_KEY:
            raise SystemExit(f'{sid}: unknown tier {tier!r}')
        image, credit = photos.get(sid, (None, None))
        sites.append({
            'id': sid,
            'name': st['site_name_display'],
            'jurisdiction': JURISDICTION[st['jurisdiction']],
            'type': st['site_type'],
            'lat': float(st['lat']),
            'lon': float(st['lon']),
            'rank': int(res['model_rank']),
            'score': round(float(res['readiness_score']), 1),
            'tier': tier,
            'tierKey': TIER_KEY[tier],
            'confidence': base['data_confidence'],
            'starter': starter,
            'pathway': pathway,
            'waitMean': round(sim.mean_wait_min, 1),
            'waitPeak': round(peak, 1),
            'note': base['notes'],
            'image': image,
            'imageCredit': credit,
        })
    sites.sort(key=lambda s: s['rank'])

    horizons, emissions = [], []
    keys = sorted({(int(r['horizon_year']), r['scenario_name']) for r in scen}, key=lambda k: (k[0], SCENARIOS.index(k[1])))
    for year, name in keys:
        sel = [r for r in scen if int(r['horizon_year']) == year and r['scenario_name'] == name]
        horizons.append({'year': year, 'scenario': name, 'active': sum(int(r['ports_active']) for r in sel),
                         'pathway': sum(int(r['ports_pathway_capacity']) for r in sel)})
        emissions.append({'year': year, 'scenario': name, 'tonnes': round(sum(float(r['net_co2e_kg']) for r in sel) / 1000, 3)})
    costs = [{'year': hy, 'case': case, 'npv': round(case_totals[(hy, case)][0], 0), 'avoided': round(case_totals[(hy, case)][1], 0)}
             for hy in V3_HORIZONS for case in CASES]

    official = manifest['reference_totals']['official']
    starter_total, pathway_total = sum(s['starter'] for s in sites), sum(s['pathway'] for s in sites)
    if (starter_total, pathway_total) != (official['starter'], official['pathway']):
        raise SystemExit(f'site totals {starter_total}/{pathway_total} differ from the contract reference totals')
    # versions.json says which plan is official and keeps the earlier result; it must agree with the contract.
    versions = json.load(open(os.path.join(os.path.dirname(OUT), 'versions.json'), encoding='utf-8'))
    earlier = manifest['reference_totals']['earlier_legacy_v2']
    if versions['official']['portPlanBasis'] != official['model_mode']:
        raise SystemExit(f'versions.json official.portPlanBasis is not {official["model_mode"]}')
    if (versions['earlier']['starter'], versions['earlier']['pathway']) != (earlier['starter'], earlier['pathway']):
        raise SystemExit('versions.json earlier totals differ from the contract\'s earlier legacy_v2 totals')

    gf = manifest['grid_factor']
    region = re.search(r', (\w+) subregion', gf['source']).group(1)
    accessed = re.search(r'accessed (\d{4}-\d{2}-\d{2})', gf['vintage']).group(1)
    generated = datetime.fromisoformat(manifest['generated_utc']).astimezone(ZoneInfo('America/New_York')).date().isoformat()
    doc = {
        'meta': {
            'contract': manifest['contract_version'],
            'generated': generated,
            'inputs': one_value((r['source_date'] for r in scen), 'source date'),
            'mode': one_value((r['model_mode'] for r in scen), 'model mode'),
            'emissions': f'{gf["source"].split(" (")[0]}, {region}, {gf["value_lb_per_mwh"]} lb CO2e/MWh (accessed {accessed}; refreshed annually)',
            'note': NOTE,
            'source': 'Generated by site/redesign/tools/build_sites.py from data/contract/v3 (DEC-027). Do not edit by hand.',
        },
        'sites': sites,
        'horizons': horizons,
        'costs': costs,
        'emissions': emissions,
    }
    text = json.dumps(doc, indent=1, ensure_ascii=False) + '\n'
    if '\u2014' in text:
        raise SystemExit('the contract text carries an em dash; the public site does not allow them')
    if CHECK:
        on_disk = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        if on_disk != text:
            raise SystemExit(f'{OUT} is out of date: run build_sites.py to regenerate it')
        print(f'{OUT} is up to date')
        return
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'wrote {OUT}: {len(sites)} sites, {starter_total} install-now and {pathway_total} future-ready ports')


if __name__ == '__main__':
    main()

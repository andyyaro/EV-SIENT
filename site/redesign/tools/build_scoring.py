"""Write www/data/scoring.json: the published weights and each site's score broken into its four parts.

Usage: PYTHONPATH=src python3 site/redesign/tools/build_scoring.py [--check] [RESULTS_CSV] [OUT_JSON]

With --check it writes nothing and exits 1 if the file on disk differs from what it would write.

The weights are imported from src/fcf_m2/scoring.py, so the page can never show weights the model
does not use. The per-site subscores come from the canonical milestone2_v3 site results (by default
tests/fixture_milestone2_v3_site_results.csv, which the model reproduces exactly). Each part's
points are its subscore times its weight; they are rounded with the largest-remainder method so the
four parts add up to exactly the published score. The script refuses to write if any recomputed
score disagrees with www/data/sites.json.

Only outputs are written: subscores scaled to points, never the inputs behind them (DEC-016).
"""
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src'))

from fcf_m2.scoring import DRIVER_WEIGHTS, INVERTED_DRIVERS, SUBSCORE_WEIGHTS  # noqa: E402

CHECK = '--check' in sys.argv
ARGS = [a for a in sys.argv[1:] if a != '--check']
RESULTS = ARGS[0] if len(ARGS) > 0 else os.path.join(REPO, 'tests', 'fixture_milestone2_v3_site_results.csv')
OUT = ARGS[1] if len(ARGS) > 1 else os.path.join(REPO, 'site', 'redesign', 'www', 'data', 'scoring.json')
SITES = os.path.join(REPO, 'site', 'redesign', 'www', 'data', 'sites.json')

PARTS = [
    ('demand', 'demand_subscore', 'Demand',
     'Whether the site is likely to attract enough public charging: the people, jobs, traffic and destinations around it, '
     'how long and how often people visit, and how much charging is already nearby.'),
    ('feasibility', 'feasibility_subscore', 'Feasibility',
     'How hard and costly the electrical work looks: spare capacity, how far chargers would sit from the electrical service, '
     'the estimated installation cost and the length of trenching.'),
    ('safety', 'safety_subscore', 'Safety',
     'Whether an accessible (ADA) layout and fire access are possible, whether chargers would sit in an enclosed garage, '
     'whether the emergency disconnect would be visible, and stormwater risk.'),
    ('equity', 'equity_subscore', 'Equity',
     'How underserved the surrounding area is for charging, from a 0 to 1 equity gap index.'),
]

DRIVERS = {
    'nearby_households_1mi_n': ('Households within 1 mile', None),
    'nearby_jobs_1mi_n': ('Jobs within 1 mile', None),
    'aadt_nearest_n': ('Traffic on the nearest main road', 'Average daily traffic count.'),
    'amenities_count_0_5mi_n': ('Shops and services within half a mile', None),
    'parking_spaces_n': ('Parking spaces', None),
    'hours_open_n': ('Hours open each day', None),
    'ev_share_local_n': ('Local share of electric vehicles', 'Full credit at a 10 percent share or more.'),
    'avg_dwell_min_n': ('Average visit length', None),
    'existing_ports_total_n': ('Charging already nearby', 'Level 2 ports within 1 mile plus fast-charging ports within 3 miles. Fewer earns more.'),
    'spare_capacity_kw_n': ('Spare electrical capacity', 'An unverified placeholder at all 12 sites.'),
    'distance_to_service_ft_n': ('Distance to the electrical service', 'Shorter earns more.'),
    'install_cost_est_usd_n': ('Estimated installation cost', 'Trenching cost plus any service upgrade. Lower earns more.'),
    'trenching_ft_n': ('Length of trenching', 'Shorter earns more.'),
    'ada_layout_possible': ('Accessible (ADA) layout possible', None),
    'fire_access_ok': ('Fire access', None),
    'garage_enclosed': ('Not in an enclosed garage', 'An enclosed garage earns nothing here and also triggers high review.'),
    'emergency_disconnect_visible': ('Emergency disconnect visible', None),
    'stormwater_risk': ('No stormwater risk', None),
    'equity_gap_index_n': ('Equity gap index', '0 means least underserved, 1 most.'),
}


def largest_remainder(values, total_tenths):
    """Round to tenths so the parts add up to total_tenths/10 exactly."""
    raw = [v * 10 for v in values]
    floors = [math.floor(x) for x in raw]
    short = total_tenths - sum(floors)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - floors[i], reverse=True)
    if short < 0 or short > len(raw):
        raise SystemExit(f'cannot reconcile parts {values} with total {total_tenths / 10}')
    for i in order[:short]:
        floors[i] += 1
    return [f / 10 for f in floors]


def main():
    published = {s['id']: s for s in json.load(open(SITES, encoding='utf-8'))['sites']}
    rows = list(csv.DictReader(open(RESULTS, encoding='utf-8')))
    out_sites = []
    for r in rows:
        sid = r['site_id']
        exact = [SUBSCORE_WEIGHTS[col] * float(r[col]) for _, col, _, _ in PARTS]
        score = round(sum(exact), 1)
        if sid not in published:
            raise SystemExit(f'{sid} is in the results but not in sites.json')
        if abs(score - published[sid]['score']) > 1e-9 or abs(score - float(r['readiness_score'])) > 1e-9:
            raise SystemExit(f'{sid}: recomputed score {score} does not match sites.json {published[sid]["score"]}')
        points = largest_remainder(exact, int(round(score * 10)))
        site = {'id': sid, 'score': score, 'parts': {key: p for (key, _, _, _), p in zip(PARTS, points)}}
        if float(r['readiness_access_adjustment']) < 1:
            site['demandAccessFactor'] = float(r['readiness_access_adjustment'])
        out_sites.append(site)
    if set(published) != {s['id'] for s in out_sites}:
        raise SystemExit('sites.json and the results list different sites')
    out_sites.sort(key=lambda s: published[s['id']]['rank'])

    parts = []
    for key, col, name, text in PARTS:
        w = SUBSCORE_WEIGHTS[col]
        drivers = []
        for field, dw in sorted(DRIVER_WEIGHTS[col].items(), key=lambda kv: -kv[1]):
            label, note = DRIVERS[field]
            d = {'name': label, 'share': round(dw * 100), 'points': round(w * dw * 100, 2)}
            # The two yes/no hazards are labelled as their absence, so they read the right way round.
            if field in INVERTED_DRIVERS and field not in ('garage_enclosed', 'stormwater_risk'):
                d['lowerIsBetter'] = True
            if note:
                d['note'] = note
            drivers.append(d)
        parts.append({'key': key, 'name': name, 'weight': round(w * 100), 'text': text, 'drivers': drivers})

    doc = {
        'meta': {
            'mode': rows[0]['scoring_mode'],
            'source': 'Weights from src/fcf_m2/scoring.py; subscores from the canonical milestone2_v3 site results. '
                      'Generated by site/redesign/tools/build_scoring.py.',
            'rounding': 'Each part is its subscore times its weight, rounded to 0.1 so the parts add up to the published score.',
            'accessFactor': 0.65,
        },
        'parts': parts,
        'sites': out_sites,
    }
    text = json.dumps(doc, indent=1, ensure_ascii=False) + '\n'
    if CHECK:
        current = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        if current != text:
            raise SystemExit(f'{OUT} is out of date: run build_scoring.py to regenerate it')
        print(f'{OUT} is up to date')
        return
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'wrote {OUT}: {len(parts)} parts, {len(out_sites)} sites')


if __name__ == '__main__':
    main()

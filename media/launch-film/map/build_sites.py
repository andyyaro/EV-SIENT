"""The twelve sites the map flight lights up, taken from the public site's own data.

python3 -I map/build_sites.py      -> map/sites.json (id, rank, lat, lon, name), read by map/flight.html

The ranks are the official milestone2_v3 ranks that futurecity.andyyaro.com shows (DEC-027).
The file is generated, not tracked, so the film can never disagree with the site it points to.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT.parent.parent / "site" / "redesign" / "www" / "data" / "sites.json"

sites = json.loads(SRC.read_text())["sites"]
out = [{"id": s["id"], "rank": s["rank"], "lat": s["lat"], "lon": s["lon"], "name": s["name"]}
       for s in sorted(sites, key=lambda s: s["rank"])]
(ROOT / "map" / "sites.json").write_text(json.dumps(out, indent=1) + "\n")
print(f"{len(out)} sites -> map/sites.json")

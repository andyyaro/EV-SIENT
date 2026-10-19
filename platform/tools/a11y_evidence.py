"""Write the evidence summaries for docs/accessibility/ from the QA scripts' raw findings.

The raw outputs (a11y_audit.py's a11y.json, matrix.py's matrix.json, offline_check.py's --json file
and wcag_checks.py's wcag.json) are large and hold screenshots' paths and per-node detail. This keeps
what the Accessibility Conformance Report cites: counts and verdicts per screen, theme and window
size, every finding in full, and nothing that identifies the machine it ran on.

Usage:
  python platform/tools/a11y_evidence.py --a11y /tmp/qa/a11y/a11y.json --matrix /tmp/qa/matrix/matrix.json \
      --offline /tmp/qa/offline.json --wcag /tmp/qa/wcag/wcag.json --commit <sha> --out docs/accessibility/evidence
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path


def axe_summary(path: Path) -> dict:
    d = json.loads(path.read_text())
    runs = [r for r in d["axe"] if "screen" in r]
    out = {"runs": len(runs), "violationNodes": 0, "byRun": [], "incomplete": {}, "keyboard": d.get("keyboard")}
    inc = collections.defaultdict(lambda: {"nodes": 0, "screens": set(), "reasons": collections.Counter(), "examples": set()})
    for r in runs:
        n = sum(len(v["nodes"]) for v in r["violations"])
        out["violationNodes"] += n
        out["byRun"].append({"browser": r["browser"], "size": r["size"], "theme": r["theme"], "screen": r["screen"],
                             "violations": [f"{v['id']} x{len(v['nodes'])}" for v in r["violations"]]})
        for v in r["incomplete"]:
            e = inc[v["id"]]
            e["nodes"] += len(v["nodes"])
            e["screens"].add(r["screen"])
            for node in v["nodes"]:
                e["reasons"][(node.get("data") or {}).get("messageKey") or "none"] += 1
                if len(e["examples"]) < 12:
                    e["examples"].add(re.sub(r":nth-child\(\d+\)", "", node["target"]))
    out["incomplete"] = {k: {"nodes": v["nodes"], "screens": sorted(v["screens"]), "reasons": dict(v["reasons"]),
                             "examples": sorted(v["examples"])} for k, v in inc.items()}
    out["browsers"] = sorted({r["browser"] for r in runs})
    out["consoleErrors"] = [r.get("consoleErrors") for r in d["axe"] if "consoleErrors" in r]
    return out


def matrix_summary(path: Path) -> dict:
    every = json.loads(path.read_text())
    rows = [r for r in every if "size" in r]
    runs = [r for r in every if "size" not in r]  # one per browser: timing, requests to other sites, errors
    failing = [r for r in rows if not r.get("ok")]
    return {"checks": len(rows), "failing": failing, "perBrowser": runs,
            "browsers": sorted({r["browser"] for r in rows}), "sizes": sorted({r["size"] for r in rows}),
            "themes": sorted({r["theme"] for r in rows}), "screens": sorted({r["screen"] for r in rows})}


def offline_summary(path: Path) -> dict:
    d = json.loads(path.read_text())
    return d


def wcag_summary(path: Path) -> dict:
    d = json.loads(path.read_text())
    screens = dict(d["screens"])
    if d.get("yourIndexRanked", {}).get("screen"):
        screens["yourindex-ranked"] = d["yourIndexRanked"]["screen"]
    if d.get("yourIndexRanked", {}).get("exploreScreen"):
        screens["explore-twelve"] = d["yourIndexRanked"]["exploreScreen"]
    out: dict = {"browser": d.get("browser"), "setup": {k: v for k, v in d.get("setup", {}).items()}, "screens": {}}
    for name, r in screens.items():
        st = r["structure"]
        s: dict = {
            "title": st["title"], "lang": st["lang"], "h1": st["h1"], "headingSkips": st["skips"],
            "headings": [f"h{h['level']} {h['text']}" for h in st["headings"]][:60],
            "landmarks": st["landmarks"], "tables": st["tables"], "states": st.get("states"),
            "unnamedImages": st["unnamedImages"], "unlabelledControls": st["unlabelled"], "labelInNameMismatches": st["labelInName"],
            "liveRegions": st["live"], "nativeTooltips": st["titles"], "inputs": st["autocomplete"],
        }
        if r.get("focus"):
            s["focus"] = {}
            for theme, f in r["focus"].items():
                s["focus"][theme] = {k: f[k] for k in ("count", "ended", "noIndicator", "weakByStyle", "weakByPixels", "entirelyHidden", "partlyCovered")}
            s["focusOrder"] = r["focus"]["light"]["order"]
            raw = r["focus"]["light"].get("raw", [])
            ratios = [max([g["vsOutside"] or 0 for g in x["rings"]] + [0]) for x in raw if x["rings"]]
            px = [x["pixels"]["ringCssPxAt3to1"] for x in raw if x.get("pixels") and x["pixels"].get("ringCssPxAt3to1") is not None]
            s["focusRingLight"] = {"stops": len(raw), "minRingContrastByStyle": min(ratios) if ratios else None,
                                   "minRingWidthAt3to1CssPx": min(px) if px else None}
        if r.get("focus390"):
            f = r["focus390"]
            s["focus390"] = {k: f[k] for k in ("count", "ended", "noIndicator", "entirelyHidden", "partlyCovered")}
        if r.get("nontext"):
            s["nonTextContrast"] = {theme: {"measured": len(items), "min": min([i["ratio"] for i in items] or [None]),
                                            "below3": [i for i in items if i["ratio"] < 3],
                                            "byKind": {k: min(i["ratio"] for i in items if i["kind"] == k) for k in sorted({i["kind"] for i in items})}}
                                    for theme, items in r["nontext"].items()}
        for key in ("undecidedText", "undecidedText390"):
            if r.get(key):
                s[key] = {theme: {"measured": len(items), "min": min([i["ratio"] for i in items] or [None]),
                                  "below4.5": [i for i in items if i["ratio"] < 4.5]} for theme, items in r[key].items()}
        if r.get("placeholders"):
            s["placeholders"] = {theme: items for theme, items in r["placeholders"].items()}
        for key in ("textSpacing1440", "textSpacing390"):
            if r.get(key):
                s[key] = r[key]
        if r.get("zoom"):
            s["zoom"] = {label: {"pageWidth": z["pageWidth"], "clipped": z["clipped"], "fixedBars": z["fixed"], "focus": z.get("focus")}
                         for label, z in r["zoom"].items()}
        if r.get("axe"):
            s["axe"] = {run: {"violations": [f"{v['id']} x{len(v['nodes'])}" for v in a["violations"]],
                              "incomplete": sorted({v["id"] for v in a["incomplete"]})} for run, a in r["axe"].items()}
        s["smallTargets1440"] = r.get("targets1440")
        s["smallTargets390"] = r.get("targets390")
        out["screens"][name] = s
    for k in ("hoverReveals", "dialog", "stepMenu", "consoleErrors", "offsite", "errors", "documents"):
        out[k] = d.get(k)
    yi = d.get("yourIndexRanked") or {}
    out["yourIndexErrors"] = yi.get("errors")
    live = []
    for x in (d.get("liveLog") or []) + (yi.get("liveLog") or []):
        live.append(f"[action] {x['mark']}" if x.get("mark") else f"{x['role']}{'[' + x['live'] + ']' if x.get('live') else ''}: {x['text']}")
    out["statusMessages"] = live
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a11y")
    ap.add_argument("--matrix")
    ap.add_argument("--offline")
    ap.add_argument("--wcag")
    ap.add_argument("--commit", required=True)
    ap.add_argument("--date", default="2026-10-18")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    meta = {"assessedCommit": args.commit, "date": args.date}
    if args.a11y:
        (out / "axe-and-keyboard.json").write_text(json.dumps({**meta, **axe_summary(Path(args.a11y))}, indent=1) + "\n")
    if args.matrix:
        (out / "layout-matrix.json").write_text(json.dumps({**meta, **matrix_summary(Path(args.matrix))}, indent=1) + "\n")
    if args.offline:
        (out / "offline.json").write_text(json.dumps({**meta, "result": offline_summary(Path(args.offline))}, indent=1) + "\n")
    if args.wcag:
        w = wcag_summary(Path(args.wcag))
        docs = w.pop("documents", None)
        (out / "wcag-checks.json").write_text(json.dumps({**meta, **w}, indent=1) + "\n")
        if docs:
            (out / "documents.json").write_text(json.dumps({**meta, **docs}, indent=1) + "\n")
    print(f"Wrote {sorted(p.name for p in out.glob('*.json'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

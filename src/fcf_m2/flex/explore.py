"""Explore: automatic findings about a visitor's own columns that count their own tests.

What this is for
----------------
A visitor's file carries columns the readiness model never reads: heat risk, flood risk,
programme focus, partner names. Explore describes them and looks for patterns between them,
so a planner can see what their own data says. It never ranks sites, and it never touches the
readiness model's numbers. The contract is docs/FLEXIBLE_ANALYSIS.md, section 2.

The failure this guards against
-------------------------------
An automatic scan is a multiple-comparisons machine. In a controlled study, over 60% of the
"insights" people reported from a visual analysis tool were false (Zgraggen et al., CHI 2018).
A scan of 30 columns runs hundreds of comparisons, and some of them will look striking by luck.
So every finding here passes eight rules before it reaches a card:

1. **Every test counts**, shown or not, and Benjamini-Hochberg runs across the whole scan at
   q = 0.10. The panel prints "N checked, K passed".
2. **Rank by effect size**, each with a seeded bootstrap 95% interval. The p-value only gates.
3. **Small groups are hidden** (under 10 sites) and anything under 30 is marked "few sites".
4. **Fixed, non-causal wording.** Sentences come from `TEMPLATES` and computed values only.
5. **Ordinal columns stay ordinal**: medians as levels, rank tests, never means of codes.
6. **"Unknown" is missing**, with a check of whether missingness differs by group.
7. **By-construction pairs are suppressed**: |rho| > 0.98, or one category nested in another.
8. **Within-country beside pooled**: a pooled result that reverses or vanishes inside
   countries is shown next to its within-country version.

What it deliberately will not do
--------------------------------
**It will not load SciPy.** Every test here is rank-based and written in numpy, with the two
distribution tails it needs (Student t and chi-square) computed by continued fractions below,
so the default panel costs no download beyond pandas. **It will not run spatial statistics**:
pooled across countries they mostly detect climate, and doing them properly is its own piece
of work. **It will not use the clock**: dates are judged against the `asOf` the caller passes,
or the latest date in the column, so the same file always gives the same JSON.
"""

from __future__ import annotations

import json
import math
import re
import zlib
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

#: The panel's statistical defaults, owner decisions of 2026-10-18.
FDR = 0.10
MIN_GROUP = 10
FEW_SITES = 30

#: Two rankable columns whose |Spearman rho| exceeds this are taken to be computed from each
#: other. Their correlation says nothing, so the pair is suppressed and the second column is
#: not tested again (its findings would repeat the first's).
CONSTRUCTION_RHO = 0.98

#: How completely one category must fix another (city within region within country) to count
#: as nested: Goodman and Kruskal's lambda, the share of the errors made guessing the coarser
#: column's most common group that knowing the finer one removes. Lambda, not the raw share of
#: rows, so that a column where nearly every site is in one group is not "fixed" by everything.
NESTED_LAMBDA = 0.98

BOOTSTRAP = 1000
PERMUTATIONS = 1999
PERMUTATION_BATCH = 100
STOP_AFTER = 20

#: A category with more groups of 10+ sites than this is not compared group by group: no
#: chart can show it and the test spreads thin. It is listed as skipped, with the reason.
MAX_GROUPS = 20

ROLES_RANKABLE = {"count", "measure", "score", "percentage", "money", "year", "ordinal"}
ROLES_NOMINAL = {"category", "flag"}
ROLES_LOGGABLE = {"count", "measure", "money"}

#: Missing markers a typed frame may still carry as text. The dictionary's own list
#: (docs/FLEXIBLE_ANALYSIS.md, section 1); "NA" is not here because it is Namibia.
MISSING_MARKERS = ("", "n/a", "N/A", "NULL", "null", "none", "-", "Unknown", "unknown", "TBD",
                   "To be confirmed")

#: Every sentence a card can carry. Nothing else writes prose, so no number appears that the
#: scan did not compute, and no verb implies a cause.
TEMPLATES = {
    "assoc_up": "Sites with higher {x} tend to have higher {y}.",
    "assoc_down": "Sites with higher {x} tend to have lower {y}.",
    "crosstab": "Sites where {x} is {a} more often have {y} {b} ({p1}% against {p0}% of other sites).",
    "group_two": ("Sites where {x} is {a} tend to have higher {y} than sites where it is {b} "
                  "(median {ma} against {mb})."),
    "group_many": ("{y} tends to differ by {x}: the median is {ma} where it is {a} and {mb} where "
                   "it is {b}."),
    "missing": ("{y} is missing more often for some {x} groups: {p1}% where it is {a}, against "
                "{p0}% where it is {b}."),
    "within_reverses": "Within each {s}, the pattern reverses: {inner}",
    "within_group": "sites where {x} is {a} tend to have higher {y} than sites where it is {b}.",
    "within_vanishes": ("Within each {s}, the pattern vanishes: the within-{s} {measure} is {v} "
                        "(95% interval {lo} to {hi})."),
    "suppressed": ("{x} and {y} move almost in step ({measure} = {v}), so one is probably computed "
                   "from the other. Not shown as a finding."),
    "nested": "{x} sits inside {y}, so the two go together by construction. Not shown as a finding.",
    "same": ("{x} and {y} split the sites into the same groups, so {y} is tested through {x}. "
             "Not shown as a finding."),
    "footer": "Association, not cause. Pattern {k} of {n} checked.",
    "footer_within": "Association, not cause. Within-{s} view of pattern {k} of {n} checked.",
}

#: Words no template may contain: each one claims a cause the scan cannot see.
BANNED_WORDS = ("drives", "driven", "causes", "caused", "leads to", "because", "due to",
                "results in", "impact")

_GEO = (re.compile(r"country|nation"), re.compile(r"region|state|province|county|district"),
        re.compile(r"city|municipality|town"))

_STOPWORDS = set("""about above after again against also among and another any are around
because been before being below between both but can could does doing down during each every
for from further had has have having her here hers him his how into its itself just more most
much must near need next not now off once only other our ours out over own per same should
some such than that the their theirs them then there these they this those through too under
until upon very was were what when where which while who whom why will with within would you
your yours site sites""".split())


# ---------- distribution tails (no SciPy) ----------

def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the regularised incomplete beta (modified Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = tiny if abs(d) < tiny else d
    d = 1.0 / d
    h = d
    for m in range(1, 400):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                     + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def _t_two_sided(t: float, df: float) -> float:
    """Two-sided p-value of Student's t."""
    if not math.isfinite(t):
        return 0.0
    return min(1.0, _betainc(df / 2.0, 0.5, df / (df + t * t)))


def _chi2_sf(x: float, df: float) -> float:
    """Upper tail of chi-square: the regularised upper incomplete gamma Q(df/2, x/2)."""
    if x <= 0.0:
        return 1.0
    a, z = df / 2.0, x / 2.0
    lead = a * math.log(z) - z - math.lgamma(a)
    if z < a + 1.0:  # series for P, then Q = 1 - P
        term = total = 1.0 / a
        ap = a
        for _ in range(1000):
            ap += 1.0
            term *= z / ap
            total += term
            if abs(term) < abs(total) * 1e-16:
                break
        return max(0.0, 1.0 - total * math.exp(lead))
    tiny = 1e-300
    b = z + 1.0 - a
    c, d = 1.0 / tiny, 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d = tiny if abs(d) < tiny else d
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return min(1.0, math.exp(lead) * h)


# ---------- rank statistics ----------

def _ties(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sort order, the start of each tie group in it, and each value's tie group."""
    order = np.argsort(x, kind="mergesort")
    xs = x[order]
    new = np.ones(len(x), dtype=bool)
    new[1:] = xs[1:] != xs[:-1]
    starts = np.flatnonzero(new)
    group = np.empty(len(x), dtype=np.int64)
    group[order] = np.cumsum(new) - 1
    return order, starts, group


def _ranks(x: np.ndarray) -> np.ndarray:
    """Average ranks, ties sharing the mean of their positions (1-based)."""
    _, starts, group = _ties(x)
    ends = np.append(starts[1:], len(x))
    return ((starts + ends - 1) / 2.0 + 1.0)[group]


def _boot_ranks(counts: np.ndarray, ties: tuple) -> np.ndarray:
    """Average ranks inside each bootstrap resample, from how often each value was drawn.

    `counts[b, i]` is how many times observation i was drawn in resample b. Ranks follow from
    cumulative counts over the sorted tie groups, so no resample is ever sorted.
    """
    order, starts, group = ties
    per_group = np.add.reduceat(counts[:, order], starts, axis=1)
    below = np.cumsum(per_group, axis=1) - per_group
    return (below + (per_group + 1) / 2.0)[:, group]


def _wcorr(counts: np.ndarray, rx: np.ndarray, ry: np.ndarray) -> np.ndarray:
    """Pearson correlation of ranks, each observation weighted by its bootstrap count."""
    total = counts.sum(axis=1, keepdims=True)
    mx = (counts * rx).sum(axis=1, keepdims=True) / total
    my = (counts * ry).sum(axis=1, keepdims=True) / total
    dx, dy = rx - mx, ry - my
    sxy = (counts * dx * dy).sum(axis=1)
    sxx = (counts * dx * dx).sum(axis=1)
    syy = (counts * dy * dy).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return sxy / np.sqrt(sxx * syy)


def _spearman(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Spearman's rho and its two-sided p-value (t approximation, n - 2 degrees of freedom)."""
    n = len(x)
    rx, ry = _ranks(x), _ranks(y)
    dx, dy = rx - rx.mean(), ry - ry.mean()
    den = math.sqrt(float((dx * dx).sum() * (dy * dy).sum()))
    if den == 0.0:
        return float("nan"), 1.0
    rho = float((dx * dy).sum() / den)
    rho = max(-1.0, min(1.0, rho))
    if abs(rho) >= 1.0:
        return rho, 0.0
    t = rho * math.sqrt((n - 2) / (1.0 - rho * rho))
    return rho, _t_two_sided(t, n - 2)


def _kruskal(y: np.ndarray, g: np.ndarray, k: int) -> tuple[float, float, float]:
    """Kruskal-Wallis H (tie-corrected), its p-value and epsilon squared, H / (n - 1).

    Epsilon squared equals the squared correlation ratio computed on ranks, so it is also the
    association matrix's value for a category against a number.
    """
    n = len(y)
    r = _ranks(y)
    ni = np.bincount(g, minlength=k).astype(float)
    ri = np.bincount(g, weights=r, minlength=k)
    mean = (n + 1) / 2.0
    ss_total = float(((r - mean) ** 2).sum())
    if ss_total == 0.0:
        return 0.0, 1.0, 0.0
    ss_between = float((ri * ri / ni).sum() - n * mean * mean)
    eps2 = max(0.0, ss_between / ss_total)
    h = (n - 1) * eps2
    return h, _chi2_sf(h, k - 1), eps2


def _cliffs_delta(y: np.ndarray, g: np.ndarray) -> float:
    """Cliff's delta of group 0 against group 1: P(y0 > y1) - P(y0 < y1), from rank sums."""
    r = _ranks(y)
    n0, n1 = int((g == 0).sum()), int((g == 1).sum())
    u0 = float(r[g == 0].sum()) - n0 * (n0 + 1) / 2.0
    return 2.0 * u0 / (n0 * n1) - 1.0


def _chi2_table(table: np.ndarray) -> tuple[float, int, np.ndarray]:
    n = table.sum()
    expected = np.outer(table.sum(axis=1), table.sum(axis=0)) / n
    keep = expected > 0
    stat = float((((table - expected) ** 2)[keep] / expected[keep]).sum())
    r = int((table.sum(axis=1) > 0).sum())
    c = int((table.sum(axis=0) > 0).sum())
    return stat, (r - 1) * (c - 1), expected


def _cramers_v(stat: np.ndarray, n: np.ndarray, r: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Bias-corrected Cramer's V (Bergsma 2013), elementwise."""
    phi2 = stat / n
    phi2c = np.maximum(0.0, phi2 - (c - 1) * (r - 1) / (n - 1))
    rc = r - (r - 1) ** 2 / (n - 1)
    cc = c - (c - 1) ** 2 / (n - 1)
    den = np.minimum(cc - 1, rc - 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, np.sqrt(phi2c / np.where(den > 0, den, 1.0)), 0.0)


def _bh(pvalues: list[float]) -> list[float]:
    """Benjamini-Hochberg adjusted p-values (q-values), in the order given."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: (pvalues[i], i))
    q = [1.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, pvalues[i] * m / rank)
        q[i] = min(1.0, running)
    return q


def _rng(seed: int, key: str) -> np.random.Generator:
    """One generator per card, so a card's interval does not depend on which cards came first."""
    return np.random.default_rng([int(seed), zlib.crc32(key.encode("utf-8"))])


def _draw_counts(rng: np.random.Generator, n: int, boot: int,
                 groups: list[np.ndarray] | None = None) -> np.ndarray:
    """How often each observation is drawn in each resample, shape (boot, n).

    With `groups`, each group is resampled within itself, so group sizes stay fixed.
    Indices come from uniform doubles, whose stream numpy keeps stable across platforms.
    """
    if groups is None:
        idx = (rng.random((boot, n)) * n).astype(np.int64)
    else:
        parts = [g[(rng.random((boot, len(g))) * len(g)).astype(np.int64)] for g in groups]
        idx = np.concatenate(parts, axis=1)
    offsets = (np.arange(boot, dtype=np.int64) * n)[:, None]
    return np.bincount((idx + offsets).ravel(), minlength=boot * n).reshape(boot, n).astype(float)


def _interval(values: np.ndarray) -> tuple[float | None, float | None]:
    values = values[np.isfinite(values)]
    if len(values) < 20:
        return None, None
    lo, hi = np.quantile(values, [0.025, 0.975])
    return float(lo), float(hi)


# ---------- columns ----------

@dataclass
class _Col:
    name: str
    role: str
    label: str
    entry: dict
    present: np.ndarray                 # bool, row has a usable value
    values: np.ndarray | None = None    # float, rankable columns
    codes: np.ndarray | None = None     # int, nominal columns, -1 when missing
    levels: list[str] = field(default_factory=list)
    shown: list[int] = field(default_factory=list)   # codes of groups with min_group+ sites
    hidden: int = 0                                  # groups under min_group
    kind: str = "other"                 # rank | nominal | other
    skip: str | None = None             # why the column is not tested


def _label(entry: dict) -> str:
    """A readable name: the entry's own title, else the header without units or ranges."""
    for key in ("title", "evsient:label"):
        if entry.get(key):
            return str(entry[key])
    name = str(entry["name"])
    name = re.sub(r"^custom_", "", name)
    name = re.sub(r"_\d+_\d+$", "", name)
    name = re.sub(r"_(kw|kwh|kw_h|m2|m|km|ft|usd|eur|gbp|pct|percent)$", "", name, flags=re.I)
    words = [w for w in re.split(r"[_\s]+", name) if w]
    return " ".join(w if w.isupper() else w.capitalize() for w in words) or str(entry["name"])


def _missing_mask(series: pd.Series, entry: dict) -> np.ndarray:
    markers = set(MISSING_MARKERS) | {str(v) for v in (entry.get("missingValues") or [])}
    missing = series.isna().to_numpy()
    text = series.astype(object).map(lambda v: isinstance(v, str) and v.strip() in markers)
    return missing | text.to_numpy(dtype=bool)


def _ordinal_labels(entry: dict, codes: np.ndarray) -> tuple[list[str], int]:
    """Level names and the code of the first level (0, or 1 if the codes count from one)."""
    cats = [str(c) for c in (entry.get("categories") or [])]
    if not len(codes):
        return cats, 0
    lo, hi = int(codes.min()), int(codes.max())
    base = 1 if cats and lo >= 1 and hi == len(cats) else 0
    top = max(hi - base + 1, len(cats))
    return cats + [f"level {i + base}" for i in range(len(cats), top)], base


def _prepare(typed: pd.DataFrame, entries: list[dict], min_group: int) -> list[_Col]:
    by_name = {str(e["name"]): e for e in entries if "name" in e}
    cols = []
    for name in map(str, typed.columns):
        entry = by_name.get(name, {"name": name})
        role = str(entry.get("evsient:role") or "unknown")
        series = typed[name]
        miss = _missing_mask(series, entry)
        col = _Col(name=name, role=role, label=_label(entry), entry=entry, present=~miss)
        if role in ROLES_RANKABLE:
            vals = pd.to_numeric(series.where(~pd.Series(miss, index=series.index)),
                                 errors="coerce").to_numpy(dtype=float, copy=True)
            vals[~np.isfinite(vals)] = np.nan
            col.values, col.present, col.kind = vals, np.isfinite(vals), "rank"
            if role == "ordinal":
                present = vals[np.isfinite(vals)]
                col.levels, base = _ordinal_labels(entry, present.astype(int) if len(present) else present)
                col.entry = {**entry, "_base": base}
        elif role in ROLES_NOMINAL:
            col.kind = "nominal"
            if role == "flag":
                vals = pd.to_numeric(series.where(~pd.Series(miss, index=series.index)),
                                     errors="coerce").to_numpy(dtype=float, copy=True)
                codes = np.full(len(vals), -1, dtype=np.int64)
                codes[vals == 1.0] = 0
                codes[vals == 0.0] = 1
                col.levels = ["Yes", "No"]
            else:
                # Plain lists: pandas' string dtype would turn a missing cell back into NaN.
                text = [None if m else str(v).strip() for v, m in zip(series.astype(object), miss)]
                counts: dict[str, int] = {}
                for v in text:
                    if v is not None:
                        counts[v] = counts.get(v, 0) + 1
                ordered = sorted(counts, key=lambda v: (-counts[v], v))
                if entry.get("categoriesOrdered") and entry.get("categories"):
                    rank = {str(c): i for i, c in enumerate(entry["categories"])}
                    ordered = sorted(ordered, key=lambda v: (rank.get(v, len(rank)), v))
                lookup = {v: i for i, v in enumerate(ordered)}
                codes = np.array([-1 if v is None else lookup[v] for v in text], dtype=np.int64)
                col.levels = ordered
            col.codes, col.present = codes, codes >= 0
            sizes = np.bincount(codes[codes >= 0], minlength=len(col.levels))
            col.shown = [i for i in range(len(col.levels)) if sizes[i] >= min_group]
            col.hidden = int(((sizes > 0) & (sizes < min_group)).sum())
        cols.append(col)

    for col in cols:
        n = int(col.present.sum())
        if col.kind == "rank":
            if n < min_group:
                col.skip = f"fewer than {min_group} sites have a value"
            elif len(np.unique(col.values[col.present])) < 2:
                col.skip = "every site has the same value"
        elif col.kind == "nominal":
            distinct = len(col.levels)
            if col.role == "category" and n and distinct > 0.5 * n:
                col.skip = "almost every site has its own value, so there are no groups to compare"
            elif len(col.shown) < 2:
                col.skip = f"fewer than two groups have {min_group} or more sites"
            elif len(col.shown) > MAX_GROUPS:
                col.skip = f"more than {MAX_GROUPS} groups have {min_group} or more sites"
    return cols


def _site_ids(typed: pd.DataFrame, cols: list[_Col]) -> list[str]:
    for col in cols:
        if col.role == "identifier":
            ids = typed[col.name].astype(object)
            text = [None if (v is None or (isinstance(v, float) and math.isnan(v))) else str(v).strip()
                    for v in ids]
            if all(text) and len(set(text)) == len(text):
                return text
    return [f"row {i + 1}" for i in range(len(typed))]


# ---------- formatting ----------

def _num(x: float, unit: str | None = None) -> str:
    if x is None or not math.isfinite(x):
        return "n/a"
    ax = abs(x)
    if ax >= 1000:
        s = f"{x:,.0f}"
    elif ax >= 10:
        s = f"{x:.1f}".rstrip("0").rstrip(".")
    elif ax == 0:
        s = "0"
    else:
        s = f"{x:.3g}"
    return f"{s} {unit}" if unit else s


def _level(col: _Col, value: float) -> str:
    """An ordinal value as its level name, never as a code."""
    base = int(col.entry.get("_base", 0))
    i = int(math.floor(value)) - base
    return col.levels[i] if 0 <= i < len(col.levels) else _num(value)


def _median_text(col: _Col, values: np.ndarray) -> str:
    if col.role == "ordinal":
        # The lower median, so the answer is always a level the column has.
        s = np.sort(values)
        return f"'{_level(col, float(s[(len(s) - 1) // 2]))}'"
    if col.role == "year":
        return f"{float(np.median(values)):.0f}"
    unit = col.entry.get("evsient:unit")
    return _num(float(np.median(values)), unit if isinstance(unit, str) else None)


def _pct(x: float) -> str:
    return f"{100.0 * x:.0f}"


def _r(x: float | None, digits: int = 4) -> float | None:
    if x is None or not math.isfinite(x):
        return None
    return round(float(x), digits)


def _q(x: float) -> float:
    return float(f"{x:.4g}")


def _reliability(n: int, smallest: int | None = None) -> str:
    small = n if smallest is None else min(n, smallest)
    return "few sites" if small < FEW_SITES else "solid"


# ---------- per-role summaries (descriptive, not tests) ----------

def _skew(v: np.ndarray) -> float | None:
    n = len(v)
    if n < 3:
        return None
    d = v - v.mean()
    m2, m3 = float((d ** 2).mean()), float((d ** 3).mean())
    if m2 == 0:
        return 0.0
    return math.sqrt(n * (n - 1)) / (n - 2) * m3 / m2 ** 1.5


def _summary_rank(col: _Col, ids: list[str], options: dict) -> dict:
    v = col.values[col.present]
    out: dict[str, Any] = {"n": int(len(v)), "missing": int((~col.present).sum())}
    if not len(v):
        return out
    if col.role == "ordinal":
        base = int(col.entry.get("_base", 0))
        counts = np.bincount((v.astype(int) - base).clip(0), minlength=len(col.levels))
        out["levels"] = [{"level": lvl, "count": int(c)} for lvl, c in zip(col.levels, counts)]
        out["median"] = _median_text(col, v).strip("'")
        out["sentence"] = f"Median level {_median_text(col, v)}, from {len(v)} sites with a value."
        return out
    q1, med, q3 = (float(x) for x in np.quantile(v, [0.25, 0.5, 0.75]))
    iqr = q3 - q1
    skew = _skew(v)
    lo_f, hi_f = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    rows = np.flatnonzero(col.present)
    out_mask = (v < lo_f) | (v > hi_f)
    extremity = np.abs(v - med)
    worst = sorted(np.flatnonzero(out_mask), key=lambda i: (-extremity[i], i))
    out.update({"median": _r(med, 6), "q1": _r(q1, 6), "q3": _r(q3, 6), "iqr": _r(iqr, 6),
                "min": _r(float(v.min()), 6), "max": _r(float(v.max()), 6),
                "skew": _r(skew), "zeros": int((v == 0).sum()), "outliers": int(out_mask.sum()),
                "outlierSites": [ids[rows[i]] for i in worst[:20]]})
    out["logSuggested"] = bool(col.role in ROLES_LOGGABLE and v.min() >= 0 and skew is not None
                               and skew > 1.0 and iqr > 0)
    rng = col.entry.get("evsient:range")
    if isinstance(rng, (list, tuple)) and len(rng) == 2 and all(isinstance(x, (int, float)) for x in rng):
        out["outOfRange"] = int(((v < rng[0]) | (v > rng[1])).sum())
    threshold = (options.get("thresholds") or {}).get(col.name)
    if isinstance(threshold, (int, float)):
        out["threshold"] = threshold
        out["shareAbove"] = _r(float((v > threshold).mean()))
    if col.role == "year":
        years, counts = np.unique(v.astype(int), return_counts=True)
        out["byYear"] = [{"year": int(y), "count": int(c), "cumulative": int(s)}
                         for y, c, s in zip(years, counts, np.cumsum(counts))]
        as_of = _as_of_year(options)
        if as_of is not None:
            out["afterAsOf"] = int((v > as_of).sum())
    unit = col.entry.get("evsient:unit")
    unit = unit if isinstance(unit, str) else None
    fmt = (lambda x: f"{x:.0f}") if col.role == "year" else (lambda x: _num(x, unit))
    out["sentence"] = (f"Median {fmt(med)}; the middle half of sites lie between {fmt(q1)} and "
                       f"{fmt(q3)}. {_odd_sites(int(out_mask.sum()))}")
    return out


def _odd_sites(n: int) -> str:
    if n == 0:
        return "No site is unusually high or low."
    return "1 site is unusually high or low." if n == 1 else f"{n} sites are unusually high or low."


def _as_of_year(options: dict) -> int | None:
    as_of = options.get("asOf")
    if not as_of:
        return None
    ts = pd.to_datetime(str(as_of), errors="coerce")
    return None if pd.isna(ts) else int(ts.year)


def _summary_nominal(col: _Col, min_group: int) -> dict:
    codes = col.codes[col.present]
    counts = np.bincount(codes, minlength=len(col.levels))
    n = int(len(codes))
    out: dict[str, Any] = {"n": n, "missing": int((~col.present).sum()),
                           "groups": len(col.levels), "shownGroups": len(col.shown),
                           "hiddenGroups": col.hidden}
    out["counts"] = [{"level": lvl, "count": int(c), "hidden": bool(c < min_group)}
                     for lvl, c in zip(col.levels, counts)]
    if n and len(col.levels) >= 3 and not col.skip:
        share = np.cumsum(np.sort(counts)[::-1]) / n
        top = int(np.searchsorted(share, 0.5) + 1)
        out["concentration"] = {"top": top, "share": _r(float(share[top - 1]))}
        if top <= len(col.levels) / 3:
            out["sentence"] = (f"{top} of {len(col.levels)} groups hold "
                               f"{_pct(float(share[top - 1]))}% of sites with a value.")
    return out


def _summary_date(series: pd.Series, entry: dict, ids: list[str], options: dict) -> dict:
    miss = _missing_mask(series, entry)
    if pd.api.types.is_datetime64_any_dtype(series):
        ts = series
    else:
        ts = pd.to_datetime(series.astype(object).where(~pd.Series(miss, index=series.index)),
                            errors="coerce", format="ISO8601")
    ok = ts.notna().to_numpy()
    out: dict[str, Any] = {"n": int(ok.sum()), "missing": int((~ok).sum())}
    if not ok.any():
        return out
    valid = ts[ok]
    years, counts = np.unique(valid.dt.year.to_numpy(), return_counts=True)
    out["byYear"] = [{"year": int(y), "count": int(c), "cumulative": int(s)}
                     for y, c, s in zip(years, counts, np.cumsum(counts))]
    as_of = pd.to_datetime(str(options["asOf"]), errors="coerce") if options.get("asOf") else None
    if as_of is None or pd.isna(as_of):
        as_of = valid.max()
        out["asOfFrom"] = "latest date in the column"
    else:
        out["asOfFrom"] = "the date the planner gave"
    stale_years = int(options.get("staleYears", 3))
    cutoff = as_of - pd.DateOffset(years=stale_years)
    stale = (ts < cutoff).fillna(False).to_numpy(dtype=bool)
    out.update({"asOf": as_of.strftime("%Y-%m-%d"), "staleYears": stale_years,
                "stale": int(stale.sum()), "staleSites": [ids[i] for i in np.flatnonzero(stale)][:50],
                "afterAsOf": int((ts > as_of).fillna(False).to_numpy(dtype=bool).sum()),
                "earliest": valid.min().strftime("%Y-%m-%d"), "latest": valid.max().strftime("%Y-%m-%d")})
    out["sentence"] = (f"{int(stale.sum())} of {int(ok.sum())} dates are more than {stale_years} "
                       f"years before {out['asOf']}.")
    return out


def _summary_text(series: pd.Series, entry: dict) -> dict:
    miss = _missing_mask(series, entry)
    texts = [str(v) for v, m in zip(series.astype(object), miss) if not m]
    counts: dict[str, int] = {}
    for t in texts:
        for w in set(re.findall(r"[a-z][a-z'-]{3,}", t.lower())):
            if w not in _STOPWORDS:
                counts[w] = counts.get(w, 0) + 1
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    return {"n": len(texts), "missing": int(miss.sum()),
            "keywords": [{"word": w, "sites": c} for w, c in top]}


def _summaries(typed: pd.DataFrame, cols: list[_Col], ids: list[str], options: dict,
               min_group: int) -> list[dict]:
    out = []
    for col in cols:
        base = {"column": col.name, "label": col.label, "role": col.role}
        if col.kind == "rank":
            base.update(_summary_rank(col, ids, options))
        elif col.kind == "nominal":
            base.update(_summary_nominal(col, min_group))
        elif col.role == "date":
            base.update(_summary_date(typed[col.name], col.entry, ids, options))
        elif col.role == "text":
            base.update(_summary_text(typed[col.name], col.entry))
        else:
            miss = _missing_mask(typed[col.name], col.entry)
            base.update({"n": int((~miss).sum()), "missing": int(miss.sum())})
            if col.role == "identifier":
                vals = typed[col.name][~miss].astype(str)
                base["duplicates"] = int(vals.duplicated().sum())
        if col.skip:
            base["notTested"] = col.skip
        out.append(base)
    return out


# ---------- the tests ----------

@dataclass
class _Test:
    id: str
    kind: str                   # association | group | missingness
    measure: str
    columns: list[str]
    n: int
    p: float
    value: float                # the effect as computed on the whole sample
    data: dict = field(default_factory=dict)
    q: float = 1.0


def _pair_rank(a: _Col, b: _Col, min_group: int) -> _Test | None:
    both = a.present & b.present
    n = int(both.sum())
    if n < min_group:
        return None
    x, y = a.values[both], b.values[both]
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        return None
    rho, p = _spearman(x, y)
    if not math.isfinite(rho):
        return None
    return _Test(id=f"assoc:{a.name}:{b.name}", kind="association", measure="spearman_rho",
                 columns=[a.name, b.name], n=n, p=p, value=rho, data={"rows": np.flatnonzero(both)})


def _restrict(col: _Col) -> np.ndarray:
    """Rows in one of the column's shown groups (10 or more sites)."""
    return np.isin(col.codes, col.shown)


def _pair_group(g: _Col, y: _Col, min_group: int) -> _Test | None:
    rows = np.flatnonzero(_restrict(g) & y.present)
    codes = g.codes[rows]
    # A group can fall under the floor once sites missing the other column drop out.
    present = [c for c in g.shown if (codes == c).sum() >= min_group]
    rows = rows[np.isin(codes, present)]
    if len(present) < 2:
        return None
    hidden = len(set(codes.tolist()) - set(present)) + g.hidden
    remap = {c: i for i, c in enumerate(present)}
    k = len(present)
    gi = np.array([remap[c] for c in g.codes[rows]], dtype=np.int64)
    vals = y.values[rows]
    if np.ptp(vals) == 0:
        return None
    h, p, eps2 = _kruskal(vals, gi, k)
    sizes = np.bincount(gi, minlength=k)
    data = {"rows": rows, "groups": gi, "present": present, "sizes": sizes, "hidden": hidden}
    if k == 2:
        delta = _cliffs_delta(vals, gi)
        return _Test(id=f"group:{g.name}:{y.name}", kind="group", measure="cliffs_delta",
                     columns=[g.name, y.name], n=len(rows), p=p, value=delta, data=data)
    return _Test(id=f"group:{g.name}:{y.name}", kind="group", measure="epsilon_squared",
                 columns=[g.name, y.name], n=len(rows), p=p, value=eps2, data=data)


def _crosstab_rows(a: _Col, b: _Col, min_group: int) -> tuple:
    keep_a, keep_b = list(a.shown), list(b.shown)
    for _ in range(5):  # drop groups that fall under the floor inside the pair, until none do
        rows = np.flatnonzero(np.isin(a.codes, keep_a) & np.isin(b.codes, keep_b))
        ca, cb = a.codes[rows], b.codes[rows]
        new_a = [c for c in keep_a if (ca == c).sum() >= min_group]
        new_b = [c for c in keep_b if (cb == c).sum() >= min_group]
        if new_a == keep_a and new_b == keep_b:
            break
        keep_a, keep_b = new_a, new_b
    rows = np.flatnonzero(np.isin(a.codes, keep_a) & np.isin(b.codes, keep_b))
    la, lb = sorted(set(a.codes[rows])), sorted(set(b.codes[rows]))
    ia = np.searchsorted(la, a.codes[rows])
    ib = np.searchsorted(lb, b.codes[rows])
    both = a.present & b.present
    hidden = (len(set(a.codes[both].tolist()) - set(la)) + len(set(b.codes[both].tolist()) - set(lb)))
    return rows, ia, ib, la, lb, hidden


def _table(ia: np.ndarray, ib: np.ndarray, ka: int, kb: int) -> np.ndarray:
    return np.bincount(ia * kb + ib, minlength=ka * kb).reshape(ka, kb).astype(float)


def _cochran_ok(expected: np.ndarray) -> bool:
    """Cochran's rule: every expected count at least 1 and no more than a fifth under 5."""
    return bool(expected.min() >= 1.0 and (expected < 5.0).mean() <= 0.2)


def _perm_p(ia: np.ndarray, ib: np.ndarray, ka: int, kb: int, stat: float,
            rng: np.random.Generator) -> float:
    """Permutation p-value for a sparse table, stopping early once the answer is clear.

    Besag and Clifford's sequential rule (1991): draw permutations in batches and stop at the
    STOP_AFTER-th one at least as extreme as the data, giving p = h / L. A table far from
    significant stops after a few dozen draws; one that might pass runs all PERMUTATIONS and
    gets (1 + h) / (B + 1). Both are valid p-values. Margins are fixed under permutation, so
    the expected counts are the observed table's.
    """
    n = len(ia)
    expected = np.outer(np.bincount(ia, minlength=ka), np.bincount(ib, minlength=kb)).astype(float) / n
    keep = (expected > 0).ravel()
    inv = 1.0 / expected.ravel()[keep]
    exp_flat = expected.ravel()[keep]
    floor = stat - 1e-9 * max(1.0, stat)
    seen = drawn = 0
    while drawn < PERMUTATIONS:
        size = min(PERMUTATION_BATCH, PERMUTATIONS - drawn)
        perms = np.argsort(rng.random((size, n)), axis=1, kind="stable")
        cells = ia[None, :] * kb + ib[perms]
        offsets = (np.arange(size, dtype=np.int64) * ka * kb)[:, None]
        tables = np.bincount((cells + offsets).ravel(), minlength=size * ka * kb).reshape(size, ka * kb)
        stats = (((tables[:, keep] - exp_flat) ** 2) * inv).sum(axis=1)
        hits = np.cumsum(stats >= floor)
        if seen + hits[-1] >= STOP_AFTER:
            at = int(np.searchsorted(hits, STOP_AFTER - seen))  # index of the h-th hit
            return STOP_AFTER / (drawn + at + 1)
        seen += int(hits[-1])
        drawn += size
    return (1 + seen) / (PERMUTATIONS + 1)


def _chi2_test(ia, ib, ka, kb, key: str, seed: int) -> tuple[float, float, float, str]:
    table = _table(ia, ib, ka, kb)
    stat, df, expected = _chi2_table(table)
    n = float(table.sum())
    v = float(_cramers_v(np.array(stat), np.array(n), np.array(float(ka)), np.array(float(kb))))
    if df <= 0:
        return stat, 1.0, v, "none"
    if _cochran_ok(expected):
        return stat, _chi2_sf(stat, df), v, "chi-square"
    return stat, _perm_p(ia, ib, ka, kb, stat, _rng(seed, "perm:" + key)), v, "permutation"


def _pair_nominal(a: _Col, b: _Col, seed: int, min_group: int) -> _Test | None:
    rows, ia, ib, la, lb, hidden = _crosstab_rows(a, b, min_group)
    if len(la) < 2 or len(lb) < 2 or len(rows) < min_group:
        return None
    key = f"assoc:{a.name}:{b.name}"
    stat, p, v, method = _chi2_test(ia, ib, len(la), len(lb), key, seed)
    return _Test(id=key, kind="association", measure="cramers_v", columns=[a.name, b.name],
                 n=len(rows), p=p, value=v,
                 data={"rows": rows, "ia": ia, "ib": ib, "la": la, "lb": lb, "method": method,
                       "hidden": hidden})


def _missingness(y: _Col, g: _Col, seed: int) -> _Test | None:
    rows = np.flatnonzero(_restrict(g))
    miss = (~y.present[rows]).astype(np.int64)
    if miss.sum() < 5 or (1 - miss).sum() < 5:
        return None
    la = sorted(set(g.codes[rows]))
    ia = np.searchsorted(la, g.codes[rows])
    key = f"missing:{y.name}:{g.name}"
    stat, p, v, method = _chi2_test(ia, miss, len(la), 2, key, seed)
    return _Test(id=key, kind="missingness", measure="cramers_v", columns=[y.name, g.name],
                 n=len(rows), p=p, value=v,
                 data={"rows": rows, "ia": ia, "ib": miss, "la": la, "method": method,
                       "hidden": g.hidden})


def _nested(a: _Col, b: _Col, min_group: int) -> tuple[_Col, bool] | None:
    """(the finer column, whether the two are the same grouping) if one category fixes the
    other (lambda of NESTED_LAMBDA or more), else None."""
    both = a.present & b.present
    if both.sum() < min_group:
        return None
    ca, cb = a.codes[both], b.codes[both]
    fixes = []
    for f, c, kf, kc in ((ca, cb, len(a.levels), len(b.levels)), (cb, ca, len(b.levels), len(a.levels))):
        table = np.bincount(f * kc + c, minlength=kf * kc).reshape(kf, kc)
        baseline = int(table.sum(axis=0).max())
        errors = len(f) - baseline
        fixes.append(bool(errors > 0 and (table.max(axis=1).sum() - baseline) >= NESTED_LAMBDA * errors))
    if fixes[0] and fixes[1]:
        return a, True
    if fixes[0]:
        return a, False
    if fixes[1]:
        return b, False
    return None


# ---------- cards ----------

def _bootstrap(test: _Test, cols: dict[str, _Col], seed: int, boot: int) -> tuple:
    rng = _rng(seed, test.id)
    d = test.data
    if test.measure == "spearman_rho":
        a, b = (cols[c] for c in test.columns)
        x, y = a.values[d["rows"]], b.values[d["rows"]]
        counts = _draw_counts(rng, len(x), boot)
        reps = _wcorr(counts, _boot_ranks(counts, _ties(x)), _boot_ranks(counts, _ties(y)))
        return _interval(reps)
    if test.kind == "group":
        y = cols[test.columns[1]]
        vals = y.values[d["rows"]]
        gi, k = d["groups"], len(d["present"])
        members = [np.flatnonzero(gi == i) for i in range(k)]
        counts = _draw_counts(rng, len(vals), boot, members)
        ranks = _boot_ranks(counts, _ties(vals))
        onehot = np.eye(k)[gi]
        rsum = (counts * ranks) @ onehot
        sizes = np.bincount(gi, minlength=k).astype(float)
        n = len(vals)
        if test.measure == "cliffs_delta":
            u0 = rsum[:, 0] - sizes[0] * (sizes[0] + 1) / 2.0
            return _interval(2.0 * u0 / (sizes[0] * sizes[1]) - 1.0)
        mean = (n + 1) / 2.0
        ss_total = (counts * (ranks - mean) ** 2).sum(axis=1)
        ss_between = (rsum ** 2 / sizes).sum(axis=1) - n * mean * mean
        with np.errstate(invalid="ignore", divide="ignore"):
            return _interval(np.maximum(0.0, ss_between / ss_total))
    # Cramer's V, for a pair of categories or a category against missingness.
    ia, ib = d["ia"], d["ib"]
    ka = len(d["la"])
    kb = len(d["lb"]) if "lb" in d else 2
    counts = _draw_counts(rng, len(ia), boot)
    onehot = np.eye(ka * kb)[ia * kb + ib]
    tables = (counts @ onehot).reshape(boot, ka, kb)
    n = float(len(ia))
    rows, colsum = tables.sum(axis=2), tables.sum(axis=1)
    expected = rows[:, :, None] * colsum[:, None, :] / n
    with np.errstate(invalid="ignore", divide="ignore"):
        stats = np.where(expected > 0, (tables - expected) ** 2 / np.where(expected > 0, expected, 1), 0)
    stat = stats.sum(axis=(1, 2))
    r = (rows > 0).sum(axis=1).astype(float)
    c = (colsum > 0).sum(axis=1).astype(float)
    return _interval(_cramers_v(stat, np.full(boot, n), r, c))


def _sentence(test: _Test, cols: dict[str, _Col]) -> tuple[str, dict, list[str]]:
    """The card's sentence, chart and highlighted sites, all from computed values."""
    d = test.data
    if test.measure == "spearman_rho":
        a, b = (cols[c] for c in test.columns)
        key = "assoc_up" if test.value > 0 else "assoc_down"
        ords = [c.name for c in (a, b) if c.role == "ordinal"]
        if len(ords) == 2:
            chart = {"type": "heatmap", "x": a.name, "y": b.name}
        elif ords:
            other = b.name if ords[0] == a.name else a.name
            chart = {"type": "box", "x": ords[0], "y": other}
        else:
            chart = {"type": "scatter", "x": a.name, "y": b.name}
        return TEMPLATES[key].format(x=a.label, y=b.label), chart, []
    if test.kind == "group":
        g, y = (cols[c] for c in test.columns)
        vals = y.values[d["rows"]]
        gi, present = d["groups"], d["present"]
        ranks = _ranks(vals)
        mean_rank = [float(ranks[gi == i].mean()) for i in range(len(present))]
        hi = max(range(len(present)), key=lambda i: (mean_rank[i], -i))
        lo = min(range(len(present)), key=lambda i: (mean_rank[i], i))
        chart = {"type": "box", "x": g.name, "y": y.name}
        fill = dict(x=g.label, y=y.label, a=g.levels[present[hi]], b=g.levels[present[lo]],
                    ma=_median_text(y, vals[gi == hi]), mb=_median_text(y, vals[gi == lo]))
        key = "group_two" if len(present) == 2 else "group_many"
        return TEMPLATES[key].format(**fill), chart, []
    if test.kind == "missingness":
        y, g = (cols[c] for c in test.columns)
        ia, miss, la = d["ia"], d["ib"], d["la"]
        share = [float(miss[ia == i].mean()) for i in range(len(la))]
        hi = max(range(len(la)), key=lambda i: (share[i], -i))
        lo = min(range(len(la)), key=lambda i: (share[i], i))
        sites = [int(r) for r in d["rows"][miss == 1]]
        return (TEMPLATES["missing"].format(y=y.label, x=g.label, a=g.levels[la[hi]], b=g.levels[la[lo]],
                                            p1=_pct(share[hi]), p0=_pct(share[lo])),
                {"type": "bar", "x": g.name, "y": "missing share", "of": y.name}, sites)
    a, b = (cols[c] for c in test.columns)
    ia, ib, la, lb = d["ia"], d["ib"], d["la"], d["lb"]
    table = _table(ia, ib, len(la), len(lb))
    n = table.sum()
    expected = np.outer(table.sum(axis=1), table.sum(axis=0)) / n
    with np.errstate(invalid="ignore", divide="ignore"):
        resid = np.where(expected > 0, (table - expected) / np.sqrt(np.where(expected > 0, expected, 1)), 0)
    i, j = divmod(int(np.argmax(resid)), len(lb))
    in_a = table[i].sum()
    p1 = table[i, j] / in_a
    p0 = (table[:, j].sum() - table[i, j]) / max(1.0, n - in_a)
    return (TEMPLATES["crosstab"].format(x=a.label, a=a.levels[la[i]], y=b.label, b=b.levels[lb[j]],
                                         p1=_pct(p1), p0=_pct(p0)),
            {"type": "heatmap", "x": a.name, "y": b.name}, [])


def _detail(measure: str, value: float, lo: float | None, hi: float | None, n: int) -> str:
    names = {"spearman_rho": "rho", "cramers_v": "Cramer's V", "cliffs_delta": "Cliff's delta",
             "epsilon_squared": "epsilon squared"}
    interval = (f", 95% interval {lo:.2f} to {hi:.2f}" if lo is not None and hi is not None else "")
    return f"{names[measure]} = {value:.2f}{interval}, n = {n}; association only."


def _strength(measure: str, value: float) -> float:
    """One scale for ranking cards of different kinds: a correlation-like size in [0, 1]."""
    if measure == "epsilon_squared":
        return math.sqrt(max(0.0, value))
    return abs(value)


# ---------- within-stratum (Simpson) ----------

def _choose_stratum(cols: list[_Col], option: Any, min_group: int) -> _Col | None:
    usable = [c for c in cols if c.role == "category" and c.skip is None and len(c.shown) >= 3]
    if option in (None, False, "none"):
        return None
    if isinstance(option, str) and option != "auto":
        named = [c for c in usable if c.name == option]
        return named[0] if named else None
    for pattern in _GEO:
        for col in usable:
            if pattern.search(col.name.lower()):
                return col
    return None


def _within(test: _Test, cols: dict[str, _Col], stratum: _Col, seed: int, boot: int,
            min_group: int) -> dict | None:
    """The pooled effect recomputed inside each stratum and combined, with its interval."""
    if stratum.name in test.columns:
        return None
    d = test.data
    rows = d["rows"]
    scodes = stratum.codes[rows]
    rng = _rng(seed, "within:" + test.id)
    parts, weights, reps = [], [], []
    if test.measure == "spearman_rho":
        a, b = (cols[c] for c in test.columns)
        for s in stratum.shown:
            sel = np.flatnonzero(scodes == s)
            if len(sel) < min_group:
                continue
            x, y = a.values[rows[sel]], b.values[rows[sel]]
            if np.ptp(x) == 0 or np.ptp(y) == 0:
                continue
            rho, _ = _spearman(x, y)
            counts = _draw_counts(rng, len(x), boot)
            parts.append(rho)
            weights.append(float(len(sel)))
            reps.append(_wcorr(counts, _boot_ranks(counts, _ties(x)), _boot_ranks(counts, _ties(y))))
    elif test.measure == "cliffs_delta":
        y = cols[test.columns[1]]
        gi = d["groups"]
        for s in stratum.shown:
            sel = np.flatnonzero(scodes == s)
            g_s = gi[sel]
            n0, n1 = int((g_s == 0).sum()), int((g_s == 1).sum())
            if len(sel) < min_group or n0 < 2 or n1 < 2:
                continue
            vals = y.values[rows[sel]]
            parts.append(_cliffs_delta(vals, g_s))
            weights.append(float(n0 * n1))
            members = [np.flatnonzero(g_s == 0), np.flatnonzero(g_s == 1)]
            counts = _draw_counts(rng, len(vals), boot, members)
            ranks = _boot_ranks(counts, _ties(vals))
            u0 = (counts * ranks)[:, members[0]].sum(axis=1) - n0 * (n0 + 1) / 2.0
            reps.append(2.0 * u0 / (n0 * n1) - 1.0)
    else:
        return None
    if len(parts) < 2:
        return None
    w = np.array(weights) / sum(weights)
    value = float(np.dot(w, parts))
    # A resample in which any stratum is undefined (no spread) is dropped, not patched.
    lo, hi = _interval((np.stack(reps, axis=1) * w[None, :]).sum(axis=1))
    if lo is None:
        return None
    pooled = test.value
    if (pooled > 0 and hi < 0) or (pooled < 0 and lo > 0):
        verdict = "reverses"
    elif lo <= 0 <= hi:
        verdict = "vanishes"
    else:
        verdict = "holds"
    return {"column": stratum.name, "groups": len(parts), "value": value, "low": lo, "high": hi,
            "verdict": verdict}


def _within_card(pooled: dict, test: _Test, within: dict, cols: dict[str, _Col], stratum: _Col) -> dict:
    names = {"spearman_rho": "rho", "cliffs_delta": "Cliff's delta"}
    if within["verdict"] == "reverses":
        if test.measure == "spearman_rho":
            a, b = (cols[c] for c in test.columns)
            key = "assoc_up" if within["value"] > 0 else "assoc_down"
            inner = TEMPLATES[key].format(x=a.label, y=b.label)
            inner = inner[0].lower() + inner[1:]
        else:
            g, y = (cols[c] for c in test.columns)
            present = test.data["present"]
            first, second = (0, 1) if within["value"] > 0 else (1, 0)
            inner = TEMPLATES["within_group"].format(x=g.label, a=g.levels[present[first]], y=y.label,
                                                     b=g.levels[present[second]])
        sentence = TEMPLATES["within_reverses"].format(s=stratum.label, inner=inner)
    else:
        sentence = TEMPLATES["within_vanishes"].format(
            s=stratum.label, measure=names[test.measure], v=f"{within['value']:.2f}",
            lo=f"{within['low']:.2f}", hi=f"{within['high']:.2f}")
    return {
        "id": f"within:{stratum.name}:{test.id}",
        "kind": "within",
        "columns": list(test.columns),
        "sentence": sentence,
        "detail": _detail(test.measure, within["value"], within["low"], within["high"], test.n),
        "effect": {"name": test.measure, "value": _r(within["value"]), "low": _r(within["low"]),
                   "high": _r(within["high"])},
        "n": test.n, "q": None, "reliability": pooled["reliability"],
        "stratum": {"column": stratum.name, "groups": within["groups"], "verdict": within["verdict"],
                    "of": test.id},
        "chart": {**pooled["chart"], "facet": stratum.name},
        "siteIds": [],
        "footer": "",
    }


# ---------- Pareto and similar sites ----------

def _pareto(cols: list[_Col], ids: list[str], options: dict) -> dict:
    chosen = options.get("paretoColumns")
    directed = [c for c in cols if c.kind in ("rank", "nominal") and c.skip is None
                and c.entry.get("evsient:provenance") == "confirmed_by_user"
                and c.entry.get("evsient:direction") in ("higher_better", "lower_better")
                and (c.kind == "rank" or c.role == "flag")
                and (not chosen or c.name in chosen)]
    if len(directed) < 2:
        return {"columns": [], "note": ("Confirm whether higher or lower is better for at least two "
                                        "columns to see the sites no other site beats on all of them.")}
    mats = []
    for c in directed:
        if c.kind == "rank":
            v = c.values.copy()
        else:  # flag: Yes is 1, No is 0
            v = np.where(c.codes == 0, 1.0, np.where(c.codes == 1, 0.0, np.nan))
        mats.append(v if c.entry["evsient:direction"] == "higher_better" else -v)
    m = np.stack(mats, axis=1)
    complete = np.flatnonzero(np.isfinite(m).all(axis=1))
    v = m[complete]
    n = len(v)
    dominated_by = np.full(n, -1, dtype=np.int64)
    for start in range(0, n, 256):
        block = v[start:start + 256]
        ge = (v[None, :, :] >= block[:, None, :]).all(axis=2)
        gt = (v[None, :, :] > block[:, None, :]).any(axis=2)
        dom = ge & gt
        has = dom.any(axis=1)
        first = np.argmax(dom, axis=1)
        dominated_by[start:start + len(block)] = np.where(has, first, -1)
    front = [ids[complete[i]] for i in range(n) if dominated_by[i] < 0]
    return {
        "columns": [c.name for c in directed],
        "directions": {c.name: c.entry["evsient:direction"] for c in directed},
        "n": int(n), "excluded": int(len(ids) - n),
        "front": front,
        "dominatedBy": {ids[complete[i]]: ids[complete[int(dominated_by[i])]]
                        for i in range(n) if dominated_by[i] >= 0},
        "note": ("Sites no other site beats on every chosen column. No weights are used, and "
                 "sites missing any chosen column are left out."),
    }


def _similar(cols: list[_Col], ids: list[str], k: int, dropped: set) -> dict:
    """Each site's k nearest sites by Gower distance, with the columns that make them alike."""
    use = [c for c in cols if c.skip is None and c.kind in ("rank", "nominal") and c.name not in dropped]
    n = len(ids)
    if not use or n < 2 or k <= 0:
        return {"columns": [], "k": k, "sites": []}
    # One (n, columns) matrix: numbers scaled to [0, 1] by their range, groups as codes.
    norm = np.zeros((n, len(use)))
    present = np.zeros((n, len(use)), dtype=bool)
    nominal = np.array([c.kind == "nominal" for c in use])
    for j, c in enumerate(use):
        if c.kind == "rank":
            lo, hi = np.nanmin(c.values), np.nanmax(c.values)
            norm[:, j] = np.where(c.present, (c.values - lo) / (hi - lo), 0.0)
        else:
            norm[:, j] = c.codes
        present[:, j] = c.present
    need = math.ceil(len(use) / 2)
    k = min(k, n - 1)
    nearest = np.zeros((n, k), dtype=np.int64)
    found = np.zeros((n, k))
    for start in range(0, n, 256):
        stop = min(n, start + 256)
        num = np.zeros((stop - start, n))
        den = np.zeros((stop - start, n))
        for j in range(len(use)):
            both = present[start:stop, j, None] & present[None, :, j]
            a, b = norm[start:stop, j, None], norm[None, :, j]
            dist = (a != b).astype(float) if nominal[j] else np.abs(a - b)
            num += np.where(both, dist, 0.0)
            den += both
        with np.errstate(invalid="ignore", divide="ignore"):
            d = np.where(den >= need, num / np.where(den > 0, den, 1), np.inf)
        d[np.arange(stop - start), np.arange(start, stop)] = np.inf
        d = np.round(d, 12)
        # The k smallest per row, ties to the earlier site, without sorting whole rows.
        kth = np.partition(d, k - 1, axis=1)[:, k - 1:k]
        below = d < kth
        tied = (d == kth) & (np.cumsum(d == kth, axis=1) <= k - below.sum(axis=1, keepdims=True))
        picks = np.nonzero(below | tied)[1].reshape(stop - start, k)
        order = np.argsort(np.take_along_axis(d, picks, axis=1), axis=1, kind="stable")
        nearest[start:stop] = np.take_along_axis(picks, order, axis=1)
        found[start:stop] = np.take_along_axis(d, nearest[start:stop], axis=1)
    i = np.repeat(np.arange(n), k)
    j = nearest.ravel()
    both = present[i] & present[j]
    per = np.where(nominal[None, :], (norm[i] != norm[j]).astype(float), np.abs(norm[i] - norm[j]))
    close = np.argsort(np.where(both, per, np.inf), axis=1, kind="stable")[:, :3]
    far = np.argsort(np.where(both, -per, np.inf), axis=1, kind="stable")[:, :2]
    names = [c.name for c in use]
    out = []
    for site in range(n):
        like = []
        for m in range(k):
            row = site * k + m
            if not math.isfinite(found[site, m]):
                continue
            like.append({"site": ids[int(j[row])], "distance": _r(float(found[site, m])),
                         "closeOn": [names[c] for c in close[row] if both[row, c]],
                         "differsOn": [names[c] for c in far[row] if both[row, c] and per[row, c] > 0.25]})
        out.append({"site": ids[site], "like": like})
    return {"columns": names, "k": k, "sites": out,
            "note": ("Gower distance over the columns listed: numbers scaled by their range, "
                     "groups compared as same or different, missing values skipped.")}


# ---------- the scan ----------

def scan(typed: pd.DataFrame, entries: list[dict], *, fdr: float = FDR, min_group: int = MIN_GROUP,
         seed: int = 1, stratum: Any = "auto", as_of: str | None = None, stale_years: int = 3,
         thresholds: dict | None = None, neighbours: int = 5, bootstrap: int = BOOTSTRAP,
         pareto_columns: list[str] | None = None) -> dict:
    """Describe the visitor's columns and return every pattern that survives the eight rules.

    `typed` holds one column per dictionary entry: numbers as floats, ordinals as integer codes
    in the order of the entry's `categories`, flags as 1.0 / 0.0, categories as text, and NaN
    for missing. Returns the shape in docs/FLEXIBLE_ANALYSIS.md, section 2.
    """
    options = {"asOf": as_of, "staleYears": stale_years, "thresholds": thresholds or {},
               "paretoColumns": pareto_columns}
    typed = typed.reset_index(drop=True)
    cols = _prepare(typed, entries, min_group)
    by_name = {c.name: c for c in cols}
    ids = _site_ids(typed, cols)

    rankable = [c for c in cols if c.kind == "rank" and c.skip is None]
    nominal = [c for c in cols if c.kind == "nominal" and c.skip is None]

    # Rule 7: pairs related by construction are screened out before any test is counted.
    suppressed, dropped = [], set()
    for i, a in enumerate(rankable):
        for b in rankable[i + 1:]:
            if a.name in dropped or b.name in dropped:
                continue
            both = a.present & b.present
            if both.sum() < min_group:
                continue
            rho, _ = _spearman(a.values[both], b.values[both])
            if math.isfinite(rho) and abs(rho) > CONSTRUCTION_RHO:
                dropped.add(b.name)
                suppressed.append({"columns": [a.name, b.name], "measure": "spearman_rho",
                                   "value": _r(rho), "kept": a.name,
                                   "note": TEMPLATES["suppressed"].format(
                                       x=a.label, y=b.label, measure="rho", v=f"{rho:.2f}")})
    nested_pairs = set()
    for i, a in enumerate(nominal):
        for b in nominal[i + 1:]:
            if a.name in dropped or b.name in dropped:
                continue
            found = _nested(a, b, min_group)
            if found is None:
                continue
            fine, same = found
            coarse = b if fine is a else a
            nested_pairs.add((a.name, b.name))
            if same:  # the same grouping under two names: test it once
                dropped.add(b.name)
            suppressed.append({"columns": [a.name, b.name], "measure": "same" if same else "nested",
                               "value": None, "kept": a.name if same else None,
                               "note": TEMPLATES["same" if same else "nested"].format(
                                   x=fine.label, y=coarse.label)})

    # Rule 1: every test the scan runs is in this list, shown or not.
    tests: list[_Test] = []
    tested = [c for c in cols if c.skip is None and c.name not in dropped and c.kind in ("rank", "nominal")]
    for i, a in enumerate(tested):
        for b in tested[i + 1:]:
            if a.kind == "rank" and b.kind == "rank":
                t = _pair_rank(a, b, min_group)
            elif a.kind == "nominal" and b.kind == "nominal":
                t = None if (a.name, b.name) in nested_pairs else _pair_nominal(a, b, seed, min_group)
            else:
                g, y = (a, b) if a.kind == "nominal" else (b, a)
                t = _pair_group(g, y, min_group)
            if t is not None:
                tests.append(t)
    # Rule 6: "Unknown" is missing, and whether it is missing more in some groups is a test too.
    for y in cols:
        if y.kind not in ("rank", "nominal") or y.name in dropped:
            continue
        for g in (g for g in nominal if g.name not in dropped):
            if g.name == y.name:
                continue
            t = _missingness(y, g, seed)
            if t is not None:
                tests.append(t)

    # Rule 1, continued: Benjamini-Hochberg across the whole scan.
    for t, q in zip(tests, _bh([t.p for t in tests])):
        t.q = q
    passed = [t for t in tests if t.q <= fdr]

    strat = _choose_stratum(cols, stratum, min_group)
    summaries = _summaries(typed, cols, ids, options, min_group)
    log_cols = {s["column"] for s in summaries if s.get("logSuggested")}
    pooled_cards = []
    for t in passed:
        lo, hi = _bootstrap(t, by_name, seed, bootstrap)
        sentence, chart, site_rows = _sentence(t, by_name)
        for axis in ("x", "y"):
            if chart.get(axis) in log_cols:
                chart[f"log{axis.upper()}"] = True
        smallest = None
        if t.kind == "group":
            smallest = int(t.data["sizes"].min())
        # Rule 3: groups under min_group never reach a card; under FEW_SITES the card says so.
        hidden = int(t.data.get("hidden", 0))
        card = {
            "id": t.id, "kind": t.kind, "columns": list(t.columns), "sentence": sentence,
            "detail": _detail(t.measure, t.value, lo, hi, t.n),
            "effect": {"name": t.measure, "value": _r(t.value), "low": _r(lo), "high": _r(hi)},
            "n": t.n, "q": _q(t.q), "reliability": _reliability(t.n, smallest),
            "stratum": None, "chart": chart, "siteIds": [ids[r] for r in site_rows],
            "footer": "",
        }
        if hidden:
            card["hiddenGroups"] = hidden
        if t.kind in ("association", "missingness") and t.measure == "cramers_v":
            card["method"] = t.data.get("method")
        # Rule 8: the within-country version, shown beside a pooled result it reverses or erases.
        within = _within(t, by_name, strat, seed, bootstrap, min_group) if strat else None
        companion = None
        if within:
            card["within"] = {k: (_r(v) if isinstance(v, float) else v) for k, v in within.items()}
            if within["verdict"] in ("reverses", "vanishes"):
                companion = _within_card(card, t, within, by_name, strat)
        pooled_cards.append((_strength(t.measure, t.value), t.id, card, companion))

    # Rule 2: rank by effect size (rounded so platforms agree on ties), then by id.
    pooled_cards.sort(key=lambda e: (-round(e[0], 9), e[1]))
    cards = []
    for k, (_, _, card, companion) in enumerate(pooled_cards, start=1):
        card["footer"] = TEMPLATES["footer"].format(k=k, n=len(tests))
        cards.append(card)
        if companion:
            companion["footer"] = TEMPLATES["footer_within"].format(s=strat.label, k=k, n=len(tests))
            cards.append(companion)

    described_roles = ROLES_RANKABLE | ROLES_NOMINAL | {"date", "text"}
    health = {"rows": int(len(typed)), "columns": int(len(cols)),
              "described": int(sum(c.role in described_roles for c in cols)),
              "unknown": int(sum(c.role == "unknown" for c in cols)),
              "missingCells": int(sum(int((~c.present).sum()) for c in cols if c.kind != "other")),
              "roles": {r: int(sum(c.role == r for c in cols)) for r in sorted({c.role for c in cols})}}
    skipped = [{"column": c.name, "reason": c.skip} for c in cols if c.skip]
    skipped += [{"column": entry["columns"][1], "reason": f"tested through {entry['kept']}"}
                for entry in suppressed if entry["kept"]]

    return _clean({
        "checked": len(tests), "passed": len(passed), "fdr": fdr, "minGroup": min_group,
        "health": health,
        "cards": cards,
        "tests": [{"id": t.id, "kind": t.kind, "columns": t.columns, "measure": t.measure,
                   "value": _r(t.value), "n": t.n, "p": _q(t.p), "q": _q(t.q), "passed": t.q <= fdr}
                  for t in tests],
        "suppressed": suppressed,
        "skipped": skipped,
        "stratum": strat.name if strat else None,
        "summaries": summaries,
        "pareto": _pareto(cols, ids, options),
        "similar": (_similar(cols, ids, neighbours, dropped) if neighbours
                    else {"columns": [], "k": 0, "sites": []}),
        "seed": seed, "bootstrap": bootstrap,
    })


def _clean(value: Any) -> Any:
    """Strict JSON: NaN and infinity become null, numpy scalars become Python ones."""
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return [_clean(v) for v in value.tolist()]
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (float, np.floating)):
        value = float(value)
        return value if math.isfinite(value) else None
    return value


# ---------- typing a raw table (until the dictionary module types it) ----------

_YES = {"yes", "y", "true", "t", "1"}
_NO = {"no", "n", "false", "f", "0"}


def type_table(raw: pd.DataFrame, entries: list[dict]) -> pd.DataFrame:
    """A minimal typed frame from a table of text cells and its dictionary entries.

    It reads only what the entry says: numbers as floats, ordinals as positions in
    `categories` (0-based), flags as 1.0 / 0.0, categories as stripped text, and every missing
    marker as missing. Anything it cannot read becomes missing; nothing is guessed.
    """
    by_name = {str(e["name"]): e for e in entries if "name" in e}
    out = {}
    for name in raw.columns:
        entry = by_name.get(str(name), {})
        role = entry.get("evsient:role", "unknown")
        markers = set(MISSING_MARKERS) | {str(v) for v in (entry.get("missingValues") or [])}
        cells = [None if v is None or (isinstance(v, float) and math.isnan(v)) or str(v).strip() in markers
                 else str(v).strip() for v in raw[name].astype(object)]
        if role in ROLES_RANKABLE - {"ordinal"}:
            out[name] = pd.to_numeric(pd.Series(cells, dtype=object).str.replace(",", "", regex=False),
                                      errors="coerce").astype(float)
        elif role == "ordinal":
            lookup = {str(c).lower(): float(i) for i, c in enumerate(entry.get("categories") or [])}
            out[name] = pd.Series([lookup.get(c.lower(), np.nan) if c else np.nan for c in cells],
                                  dtype=float)
        elif role == "flag":
            out[name] = pd.Series([1.0 if c and c.lower() in _YES else 0.0 if c and c.lower() in _NO
                                   else np.nan for c in cells], dtype=float)
        else:
            out[name] = pd.Series(cells, dtype=object)
    return pd.DataFrame(out, index=raw.index)


# ---------- the browser bridge ----------

def bridge_scan(table_json: str, entries_json: str, options_json: str = "{}") -> str:
    """JSON in, JSON out, for the planner's Pyodide worker.

    `table_json` is {"columns": [...], "rows": [[...]]}, with "typed": true when the cells are
    already typed (numbers, codes, null for missing); otherwise the cells are the text the
    visitor uploaded and `type_table` reads them. `entries_json` is the dictionary, either a
    list of entries or a Table Schema with `fields`. Options: fdr, minGroup, seed, stratum,
    asOf, staleYears, thresholds, neighbours, bootstrap, paretoColumns.
    """
    table = json.loads(table_json)
    entries = json.loads(entries_json)
    if isinstance(entries, dict):
        entries = entries.get("fields", [])
    options = json.loads(options_json or "{}")
    columns = [str(c) for c in table["columns"]]
    if len(set(columns)) != len(columns):
        raise ValueError("Two columns in this file have the same name. Rename one and upload it again.")
    width = len(columns)
    rows = [(list(row) + [None] * width)[:width] for row in table["rows"]]
    frame = pd.DataFrame(rows, columns=columns, dtype=object)
    if table.get("typed"):
        typed = frame
        for e in entries:
            name = str(e.get("name"))
            if name in typed.columns and e.get("evsient:role") in (ROLES_RANKABLE | {"flag"}):
                typed[name] = pd.to_numeric(typed[name], errors="coerce").astype(float)
    else:
        typed = type_table(frame, entries)
    result = scan(typed, entries, fdr=float(options.get("fdr", FDR)),
                  min_group=int(options.get("minGroup", MIN_GROUP)), seed=int(options.get("seed", 1)),
                  stratum=options.get("stratum", "auto"), as_of=options.get("asOf"),
                  stale_years=int(options.get("staleYears", 3)), thresholds=options.get("thresholds"),
                  neighbours=int(options.get("neighbours", 5)),
                  bootstrap=int(options.get("bootstrap", BOOTSTRAP)),
                  pareto_columns=options.get("paretoColumns"))
    return json.dumps(result, allow_nan=False)

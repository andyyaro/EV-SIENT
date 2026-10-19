"""How firm is the ranking? A score breakdown and three planning-support stability checks.

The readiness score is a weighted sum (``scoring.SUBSCORE_WEIGHTS``) of four subscores, each
itself a weighted sum of drivers (``scoring.DRIVER_WEIGHTS``). The published ranks therefore
depend on two things nobody has measured: the weights, which are a judgement, and inputs that
are not yet confirmed. This module reports how much the order moves when either moves. It
re-weights the scores the engine already computed; it never re-scores a site, changes a rank or
writes anything back.

    breakdown            each subscore's and each driver's contribution, in readiness points,
                         adding up exactly to the published score
    weight_sensitivity   one weight at a time moved by plus and minus 5 points, the others
                         rescaled in proportion; and the smallest single-weight change that
                         changes the top site
    rank_stability       many plausible weightings drawn around the defaults (a Dirichlet
                         distribution); for each site the share of draws in which it ranks
                         first or in the top three, and the 5th to 95th percentile of its rank
    input_uncertainty    the range each score could take if inputs whose field group is not
                         yet confirmed turned out anywhere from no credit to full credit

None of these is a probability that a site is actually the best place to build. They say how
much the order depends on choices and inputs the model cannot settle. The method is written
out in plain language in docs/methodology/rank_stability.md.

Everything here is deterministic (a fixed seed), uses numpy and pandas only, and runs inside
the planner's browser under Pyodide; a 600-site cohort takes well under a second.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from .intake import FIELD_GROUP_FOR_INPUT
from .scoring import DRIVER_WEIGHTS, INVERTED_DRIVERS, SUBSCORE_WEIGHTS

#: Subscores in the formula's order.
SUBSCORES: list[str] = list(SUBSCORE_WEIGHTS)

#: How far the one-at-a-time check moves a weight: 5 points of 100.
SENSITIVITY_STEP = 0.05

#: Weightings drawn for the rank-stability check. 2,000 keeps the share of first places within
#: about one percentage point of its limit (standard error at most 1.1 points) and runs in a few
#: milliseconds natively, well under a second under Pyodide even at 600 sites.
DEFAULT_DRAWS = 2000

#: How tightly the drawn weights sit around the defaults. With 50, a weight of 45 points
#: typically lands between about 34 and 57 (5th to 95th percentile).
DEFAULT_CONCENTRATION = 50.0

#: Fixed so the same results always give the same answer.
DEFAULT_SEED = 20261018

#: A field group whose data confidence is below this (the "Low" band, confidence.level_for) is
#: treated as not yet confirmed by the input check.
CONFIRMED_AT = 50.0

#: The supplied fields a driver is built from. `existing_ports_total` and `install_cost_est_usd`
#: are the engine's own sums of supplied fields; every other driver reads one field.
DRIVER_INPUTS: dict[str, list[str]] = {
    "existing_ports_total_n": ["existing_l2_ports_1mi", "existing_dcfc_ports_3mi"],
    "install_cost_est_usd_n": ["trenching_ft", "trench_cost_per_ft", "service_upgrade_cost_usd"],
}

#: The driver whose input is a placeholder at every reference site until a utility or facility
#: confirms it (contract capacity_basis).
CAPACITY_DRIVER = "spare_capacity_kw_n"


def driver_inputs(driver: str) -> list[str]:
    """The supplied fields one driver reads."""
    return DRIVER_INPUTS.get(driver, [driver[:-2] if driver.endswith("_n") else driver])


def _short(subscore: str) -> str:
    return subscore.replace("_subscore", "")


def _label(labels: dict[str, str] | None, key: str) -> str:
    return (labels or {}).get(key, key)


def _float(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return math.nan
    return out


# ---------- shared reading of the results table ----------

def _ordered(results: pd.DataFrame) -> pd.DataFrame:
    """The results in published rank order, with text site IDs."""
    df = results.copy()
    df["site_id"] = df["site_id"].astype(str)
    if "model_rank" in df.columns:
        df = df.sort_values("model_rank", kind="stable")
    return df.reset_index(drop=True)


def _names(df: pd.DataFrame) -> list[str]:
    """Each site's display name, or its ID where the results have none."""
    if "site_name" not in df.columns:
        return [str(i) for i in df["site_id"]]
    return [n if isinstance(n, str) else str(i) for n, i in zip(df["site_name"], df["site_id"])]


def _subscores(df: pd.DataFrame) -> np.ndarray:
    """N x 4 subscores, in SUBSCORES order. A missing subscore is refused, never read as 0."""
    missing = [c for c in SUBSCORES if c not in df.columns]
    if missing:
        raise ValueError(f"These results have no {', '.join(missing)}, so their weights cannot be checked.")
    out = df[SUBSCORES].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if np.isnan(out).any():
        raise ValueError("A site in these results has no subscore, so the weights cannot be checked.")
    return out


def _weights() -> np.ndarray:
    return np.array([SUBSCORE_WEIGHTS[s] for s in SUBSCORES], dtype=float)


def _access(df: pd.DataFrame) -> np.ndarray:
    if "readiness_access_adjustment" not in df.columns:
        return np.ones(len(df))
    return pd.to_numeric(df["readiness_access_adjustment"], errors="coerce").fillna(1.0).to_numpy(dtype=float)


def _driver_terms(df: pd.DataFrame) -> list[dict]:
    """Each driver's points and full-credit points per site, as `browser_api.explain` adds them.

    A driver adds subscore weight x 100 x driver weight x credit, where credit is the normalised
    value (or 1 minus it for a lower-is-better driver) and 0 for a value nobody recorded. A site
    not recorded as open to the public has its demand drivers scaled by the access adjustment.
    """
    access = _access(df)
    terms = []
    for subscore, weights in DRIVER_WEIGHTS.items():
        scale = access if subscore == "demand_subscore" else np.ones(len(df))
        for driver, w in weights.items():
            raw = (pd.to_numeric(df[driver], errors="coerce").to_numpy(dtype=float)
                   if driver in df.columns else np.full(len(df), np.nan))
            credit = (1 - raw) if driver in INVERTED_DRIVERS else raw
            credit = np.where(np.isnan(credit), 0.0, credit)
            full = SUBSCORE_WEIGHTS[subscore] * 100 * w * scale
            terms.append({"key": driver, "subscore": subscore, "weight": SUBSCORE_WEIGHTS[subscore] * w,
                          "inverted": driver in INVERTED_DRIVERS, "points": full * credit, "max": full})
    return terms


def _apportion(values: list[float], target_units: int, unit: float) -> list[float]:
    """Round each value to `unit` so the rounded values add up to exactly target_units x unit.

    Largest remainder: floor every value, then give the missing units to the largest remainders
    (or take surplus units from the smallest). Each part moves by less than one unit, and a part
    that adds nothing stays at zero, so a driver earning no credit is never shown as earning some.
    """
    scaled = [v / unit for v in values]
    floors = [math.floor(s + 1e-9) for s in scaled]
    short = target_units - sum(floors)
    movable = [i for i in range(len(values)) if values[i] > 0 and (short > 0 or floors[i] > 0)]
    order = sorted(movable, key=lambda i: (scaled[i] - floors[i]), reverse=short > 0)
    for k in range(abs(short)):
        if not order:
            break
        floors[order[k % len(order)]] += 1 if short > 0 else -1
    return [round(f * unit, 10) for f in floors]


def _ranks(scores: np.ndarray, base_rank: np.ndarray) -> np.ndarray:
    """1-based ranks, highest score first; an exact tie keeps the published order."""
    order = np.lexsort((base_rank, -scores))
    ranks = np.empty(len(scores), dtype=int)
    ranks[order] = np.arange(1, len(scores) + 1)
    return ranks


def reweight(weights: np.ndarray, i: int, value: float) -> np.ndarray:
    """Set weight i to `value` and rescale the others in proportion so the four add up to 1."""
    rest = 1.0 - weights[i]
    out = weights * ((1.0 - value) / rest) if rest > 0 else np.zeros_like(weights)
    out[i] = value
    return out


# ---------- 1. breakdown ----------

def breakdown(results: pd.DataFrame, labels: dict[str, str] | None = None) -> list[dict]:
    """Every site's score as the sum of its parts, in published rank order.

    `points` are exact and add up to `total`, the unrounded score. `shown` are the same
    contributions rounded so they add up exactly to the published score (which is `total`
    rounded to 0.1): the subscores at 0.1 points, and the drivers, all of them together, at
    0.01 points.
    """
    df = _ordered(results)
    S = _subscores(df)
    w = _weights()
    terms = _driver_terms(df)
    access = _access(df)
    ids, names = df["site_id"].tolist(), _names(df)
    ranks = (df["model_rank"].astype(int).tolist() if "model_rank" in df.columns
             else list(range(1, len(df) + 1)))
    published = (pd.to_numeric(df["readiness_score"], errors="coerce").tolist()
                 if "readiness_score" in df.columns else [math.nan] * len(df))
    # Plain lists, read once: a pandas lookup per site and driver is what makes 600 sites slow.
    by_sub = [[(t, t["points"].tolist(), t["max"].tolist()) for t in terms if t["subscore"] == sub]
              for sub in SUBSCORES]
    meta = [[{"key": t["key"], "label": _label(labels, t["key"]), "subscore": _short(t["subscore"]),
              "weight": round(float(t["weight"]), 6), "inverted": t["inverted"]} for t, _, _ in group]
            for group in by_sub]
    out = []
    for n in range(len(df)):
        sub_points = [float(w[i] * S[n, i]) for i in range(len(SUBSCORES))]
        total = float(sum(sub_points))
        p = published[n]
        score = p if not math.isnan(p) and abs(p - total) <= 0.05 + 1e-9 else round(total, 1)
        sub_shown = _apportion(sub_points, round(score * 10), 0.1)
        subscores, parts, part_meta = [], [], []
        for i, subscore in enumerate(SUBSCORES):
            pts = [float(points[n]) for _, points, _ in by_sub[i]]
            # The drivers are rescaled onto the subscore's own value, so a subscore read from
            # the results file and its recomputed drivers never disagree in the last digit.
            scale = sub_points[i] / sum(pts) if sum(pts) > 0 else 0.0
            parts += [x * scale for x in pts]
            part_meta += [(m, float(full[n])) for m, (_, _, full) in zip(meta[i], by_sub[i])]
            subscores.append({
                "key": _short(subscore), "label": _label(labels, subscore), "weight": float(w[i]),
                "value": float(S[n, i]), "points": sub_points[i], "shown": sub_shown[i],
                "max": float(w[i] * 100),
            })
        shown = _apportion(parts, round(score * 100), 0.01)
        drivers = [{**m, "points": x, "shown": sh, "max": full}
                   for (m, full), x, sh in zip(part_meta, parts, shown)]
        out.append({
            "siteId": str(ids[n]), "name": names[n], "rank": int(ranks[n]),
            "score": score, "total": total, "accessAdjustment": float(access[n]),
            "subscores": subscores, "drivers": drivers,
        })
    return out


# ---------- 2. one weight at a time ----------

def _flip(S: np.ndarray, w: np.ndarray, i: int, top: int, base_rank: np.ndarray, direction: int) -> dict | None:
    """The nearest weight for subscore i, moving in `direction`, at which `top` stops being first.

    Each site's score is a straight line in weight i (the others rescaled in proportion), so the
    top site changes where another site's line first meets the top site's line.
    """
    rest = (S @ w - w[i] * S[:, i]) / (1.0 - w[i])
    slope = S[:, i] - rest
    a = slope - slope[top]
    b = rest - rest[top]
    others = (np.arange(len(S)) != top) & (a != 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        at = np.where(others, -b / np.where(others, a, 1.0), np.nan)
    if direction > 0:
        hit = others & (a > 0) & (at > w[i]) & (at <= 1.0)
        best = float(at[hit].min()) if hit.any() else None
    else:
        hit = others & (a < 0) & (at < w[i]) & (at >= 0.0)
        best = float(at[hit].max()) if hit.any() else None
    if best is None:
        return None
    nudge = min(1.0, max(0.0, best + direction * 1e-9))
    after = int(np.argmin(_ranks(S @ reweight(w, i, nudge), base_rank)))
    # A crossing exactly at 0 or 100 points is a tie, not a change of first place.
    return None if after == top else {"at": float(best), "newTop": after}


def weight_sensitivity(results: pd.DataFrame, step: float = SENSITIVITY_STEP,
                       labels: dict[str, str] | None = None) -> dict:
    """Each subscore weight moved by plus and minus `step`, the others rescaled in proportion.

    Reports the top site and every rank change in each case, then, for each weight and each
    direction, the nearest weight (between 0 and 100 points) at which the top site changes.
    Ranks here use unrounded scores; the published ranks use scores rounded to 0.1.
    """
    df = _ordered(results)
    S = _subscores(df)
    w = _weights()
    ids = df["site_id"].tolist()
    base_rank = np.arange(1, len(df) + 1)
    base = _ranks(S @ w, base_rank)
    top = int(np.argmin(base))
    cases, case_ranks = [], [base]
    for i, subscore in enumerate(SUBSCORES):
        for sign in (+1, -1):
            value = w[i] + sign * step
            if not 0.0 <= value <= 1.0:
                continue
            wi = reweight(w, i, value)
            scores = S @ wi
            ranks = _ranks(scores, base_rank)
            case_ranks.append(ranks)
            lead = int(np.argmin(ranks))
            leaders = [int(k) for k in np.argsort(ranks)[:3]]
            cases.append({
                "subscore": _short(subscore), "label": _label(labels, subscore),
                "change": round(sign * step * 100, 6),
                "weights": {_short(s): round(float(x), 6) for s, x in zip(SUBSCORES, wi)},
                "top": ids[lead], "topChanged": lead != top,
                "leaders": [{"siteId": ids[k], "score": round(float(scores[k]), 1)} for k in leaders],
                "rankChanges": [{"siteId": ids[k], "from": int(base[k]), "to": int(ranks[k])}
                                for k in range(len(ids)) if ranks[k] != base[k]],
            })
    flips = []
    for i, subscore in enumerate(SUBSCORES):
        for direction in (+1, -1):
            found = _flip(S, w, i, top, base_rank, direction)
            if found is None:
                continue
            flips.append({
                "subscore": _short(subscore), "label": _label(labels, subscore),
                "direction": "up" if direction > 0 else "down",
                "from": round(float(w[i]) * 100, 6), "to": round(found["at"] * 100, 4),
                "change": round((found["at"] - float(w[i])) * 100, 4),
                "newTop": ids[found["newTop"]],
            })
    smallest = min(flips, key=lambda f: abs(f["change"])) if flips else None
    names = dict(zip(ids, _names(df)))
    every = np.vstack(case_ranks)
    best, worst = every.min(axis=0), every.max(axis=0)
    return {
        "step": round(step * 100, 6),
        "top": ids[top],
        "cases": cases,
        "flips": sorted(flips, key=lambda f: abs(f["change"])),
        "smallestFlip": smallest,
        "sentence": flip_sentence(names[ids[top]], smallest, names),
        "siteRanks": {ids[k]: {"best": int(best[k]), "worst": int(worst[k])} for k in range(len(ids))},
    }


def _pts(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".") if abs(x - round(x)) > 1e-9 else f"{round(x):d}"


def flip_sentence(top_name: str, smallest: dict | None, names: dict[str, str]) -> str:
    """The plain sentence about the smallest single-weight change that changes the top site."""
    if smallest is None:
        return (f"{top_name} stays first whatever any one weight is set to, from 0 to 100 points, "
                f"with the other weights scaled to match.")
    verb = "rises" if smallest["direction"] == "up" else "falls"
    return (f"{top_name} stays first unless the {smallest['label']} weight {verb} from "
            f"{_pts(smallest['from'])} to about {smallest['to']:.1f} points (a change of "
            f"{abs(smallest['change']):.1f}, with the other weights scaled to match); then "
            f"{names.get(smallest['newTop'], smallest['newTop'])} moves to first. No smaller change "
            f"to a single weight changes the top site.")


# ---------- 3. many weightings at once ----------

def rank_stability(results: pd.DataFrame, draws: int = DEFAULT_DRAWS,
                   concentration: float = DEFAULT_CONCENTRATION, seed: int = DEFAULT_SEED,
                   labels: dict[str, str] | None = None) -> dict:
    """Ranks under `draws` weightings drawn from a Dirichlet distribution around the defaults.

    The Dirichlet's parameters are concentration x the default weights, so the draws average to
    the defaults and always add up to 1. For each site: the share of draws in which it ranks
    first and in the top three, and the 5th, 50th and 95th percentile of its rank.
    """
    if int(draws) < 1:
        raise ValueError("Ask for at least one weighting.")
    if not concentration > 0:
        raise ValueError("The concentration must be above 0.")
    draws = int(draws)
    df = _ordered(results)
    S = _subscores(df)
    w = _weights()
    ids = df["site_id"].tolist()
    rng = np.random.default_rng(int(seed))
    W = rng.dirichlet(concentration * w, size=draws)
    scores = W @ S.T
    # Highest score first; an exact tie keeps the published order (argsort is stable on -score).
    order = np.argsort(-scores, axis=1, kind="stable")
    ranks = np.empty_like(order)
    np.put_along_axis(ranks, order, np.arange(1, len(ids) + 1)[None, :].repeat(draws, axis=0), axis=1)
    # The 5th, 50th and 95th percentile as numpy's "inverted_cdf" defines them (an observed
    # rank, never an interpolated one), read from one sort instead of three quantile passes.
    ordered = np.sort(ranks, axis=0)
    q = ordered[[max(math.ceil(p * draws) - 1, 0) for p in (0.05, 0.5, 0.95)], :]
    first, top3 = (ranks == 1).mean(axis=0), (ranks <= 3).mean(axis=0)
    spread = np.quantile(W, [0.05, 0.95], axis=0, method="inverted_cdf")
    return {
        "draws": draws, "concentration": float(concentration), "seed": int(seed),
        "weightSpread": [{"key": _short(s), "label": _label(labels, s), "weight": float(w[i]),
                          "low": round(float(spread[0, i]), 6), "high": round(float(spread[1, i]), 6)}
                         for i, s in enumerate(SUBSCORES)],
        "sites": [{"siteId": ids[k],
                   "pFirst": float(first[k]), "pTop3": float(top3[k]),
                   "rankLow": int(q[0, k]), "rankMedian": int(q[1, k]), "rankHigh": int(q[2, k])}
                  for k in range(len(ids))],
    }


# ---------- 4. inputs not yet confirmed ----------

def confidence_from_results(results: pd.DataFrame) -> dict[str, dict[str, float]] | None:
    """Per-site field-group confidence, when the results carry it as `group=score; ...` text."""
    for column in ("confidence_breakdown", "data_confidence_reason"):
        if column not in results.columns:
            continue
        out: dict[str, dict[str, float]] = {}
        for _, row in results.iterrows():
            text = row[column]
            if not isinstance(text, str):
                continue
            parts = {}
            for part in text.split(";"):
                if "=" in part:
                    key, value = part.strip().split("=", 1)
                    v = _float(value)
                    if not math.isnan(v):
                        parts[key.strip()] = v
            if parts:
                out[str(row["site_id"])] = parts
        if out:
            return out
    return None


def input_uncertainty(results: pd.DataFrame, confidence: dict[str, dict[str, float]] | None = None,
                      threshold: float = CONFIRMED_AT, labels: dict[str, str] | None = None) -> dict:
    """How far each score could move if inputs not yet confirmed turned out differently.

    A driver is "not yet confirmed" at a site when any field it reads belongs to a field group
    whose data confidence there is below `threshold`. Each such driver is let run from no credit
    to full credit, which gives the lowest and highest score the site could have; then the best
    and worst rank each site could reach while every other site also moves within its own range.
    This is a range, not a probability: it does not say any value is likely.

    Two passes: the electrical capacity driver alone (a placeholder until a utility or facility
    confirms it), and every driver not yet confirmed.
    """
    df = _ordered(results)
    if confidence is None:
        confidence = confidence_from_results(df)
    if not confidence:
        return {"done": False, "threshold": threshold, "scenarios": [],
                "reason": ("These results do not say how well each group of inputs is sourced, so "
                           "there is no honest way to tell which inputs to vary.")}
    S = _subscores(df)
    total = S @ _weights()
    terms = _driver_terms(df)
    ids = df["site_id"].tolist()
    N = len(ids)
    groups = {g for site in confidence.values() for g in site}
    weak = {g: np.array([confidence.get(i, {}).get(g, math.inf) < threshold for i in ids]) for g in groups}
    scenarios = []
    for key, label, only in (("capacity", "Electrical capacity only", {CAPACITY_DRIVER}),
                             ("unconfirmed", "Every input not yet confirmed", None)):
        low, high = total.copy(), total.copy()
        which: list[list[str]] = [[] for _ in ids]
        for t in terms:
            if only is not None and t["key"] not in only:
                continue
            mask = np.zeros(N, dtype=bool)
            for f in driver_inputs(t["key"]):
                g = FIELD_GROUP_FOR_INPUT.get(f)
                if g in weak:
                    mask |= weak[g]
            low = low - np.where(mask, t["points"], 0.0)
            high = high + np.where(mask, t["max"] - t["points"], 0.0)
            for n in np.flatnonzero(mask):
                which[n].append(t["key"])
        # Best rank: this site at its highest, every other at its lowest; worst: the reverse.
        # A site's own low never exceeds its own high, so it never counts against itself.
        best = 1 + N - np.searchsorted(np.sort(low), high, side="right")
        worst = 1 + N - np.searchsorted(np.sort(high), low, side="right") - (high > low)
        scenarios.append({
            "key": key, "label": label,
            "couldBeFirst": [ids[n] for n in range(N) if best[n] == 1],
            # Clamped to the scale only to drop float noise (a -0.0, a 100.0000001).
            "sites": [{"siteId": ids[n], "low": round(min(100.0, max(0.0, float(low[n]))), 4) + 0.0,
                       "high": round(min(100.0, max(0.0, float(high[n]))), 4) + 0.0,
                       "bestRank": int(best[n]), "worstRank": int(worst[n]),
                       "drivers": which[n]} for n in range(N)],
        })
    return {
        "done": True, "threshold": threshold, "scenarios": scenarios,
        "missingConfidence": [i for i in ids if i not in confidence],
    }


# ---------- everything at once ----------

METHOD_NOTE = (
    "A planning-support sensitivity check, not a probability that a site is actually the best "
    "place to build. It re-weights the scores the model already computed to show how much the "
    "order depends on the weights, which are a judgement, and on inputs not yet confirmed.")


def analyse(results: pd.DataFrame, confidence: dict[str, dict[str, float]] | None = None,
            labels: dict[str, str] | None = None, draws: int = DEFAULT_DRAWS,
            concentration: float = DEFAULT_CONCENTRATION, seed: int = DEFAULT_SEED) -> dict:
    """The breakdown and all three checks, joined per site, as the platform and the site show them."""
    parts = breakdown(results, labels)
    sens = weight_sensitivity(results, labels=labels)
    stab = rank_stability(results, draws=draws, concentration=concentration, seed=seed, labels=labels)
    inputs = input_uncertainty(results, confidence, labels=labels)
    by_stab = {s["siteId"]: s for s in stab["sites"]}
    by_input = {sc["key"]: {s["siteId"]: s for s in sc["sites"]} for sc in inputs["scenarios"]}
    sites = []
    for site in parts:
        sid = site["siteId"]
        s = by_stab[sid]
        sites.append({
            **site,
            "stability": {k: s[k] for k in ("pFirst", "pTop3", "rankLow", "rankMedian", "rankHigh")},
            "weightCases": sens["siteRanks"][sid],
            "inputRange": {k: {f: v[sid][f] for f in ("low", "high", "bestRank", "worstRank", "drivers")}
                           for k, v in by_input.items()},
        })
    return {
        "note": METHOD_NOTE,
        "weights": [{"key": _short(s), "label": _label(labels, s), "weight": SUBSCORE_WEIGHTS[s]}
                    for s in SUBSCORES],
        "sites": sites,
        "sensitivity": {k: v for k, v in sens.items() if k != "siteRanks"},
        "rankStability": {k: v for k, v in stab.items() if k != "sites"},
        "inputUncertainty": {**inputs, "scenarios": [{k: v for k, v in sc.items() if k != "sites"}
                                                     for sc in inputs["scenarios"]]},
    }

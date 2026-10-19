"""A visitor's own index: a weighted sum of confirmed value functions, never an official score.

The contract is docs/FLEXIBLE_ANALYSIS.md section 3. A visitor picks columns from their own
file, confirms which way is better for each, gives each a value function and a weight, and may
add screens. This module checks that spec, runs it, and says how far the ranking can be trusted.

The arithmetic is the readiness model's, so the two can be read the same way:

    value  = f(x), a value function bounded to [0, 1] with pinned anchors
    points = weight x value x 100            (weights normalised to sum to 1)
    score  = the sum of the points           (so the drivers add up to the score)

* **Anchors are pinned.** A linear criterion with no anchors takes the observed range of the
  whole file once, before any screen, and the result returns them in `spec`, so a later run on
  fewer rows scores every remaining site exactly as before. Thresholds and targets are always
  the visitor's own numbers. Nothing here is min-max scaled against whichever rows are loaded.
* **Missing values earn no credit** (DEC-011), and every site also gets the score it would have
  if its missing values earned full credit, and its completeness. Sites with values for fewer
  than `minCoverage` of the criteria are listed, not ranked.
* **Screens come first.** They are JsonLogic, evaluated by the small interpreter below (never
  `eval`), and a site a screen removes is listed with the screen's reason.
* **Robustness is shown, not assumed.** Weights are drawn from a Dirichlet centred on the
  visitor's weights (and ordinal maps are nudged), with a fixed seed, and each site gets its
  5th to 95th percentile rank and its share of draws in the top k. Because the index is linear,
  "what would change the rank" is computed exactly for each adjacent pair.
* **Gates** are the JRC composite-indicator checks plus double counting and minimum data, each
  with a fixed message and the numbers behind it.

Every result carries `"official": false` and the visitor's own name for the index. It uses
pandas, numpy and the standard library only, so it runs unchanged under Pyodide.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any, Mapping

import numpy as np
import pandas as pd

PACK = "evsient-custom-index"
PACK_MAJOR = 1
BADGE = "Not an official EV-SIENT score"

DIRECTIONS = ("higher_better", "lower_better", "neither")
DIRECTION_WORDS = {"higher_better": "higher is better", "lower_better": "lower is better",
                   "neither": "neither direction is better"}
KINDS = ("linear", "threshold", "target", "ordinal")
MISSING_POLICIES = ("no_credit",)

MIN_CRITERIA = 2
MIN_SITES = 10
DEFAULT_MIN_COVERAGE = 0.65
DEFAULT_ROBUSTNESS = {"draws": 2000, "spread": 0.25, "seed": 1, "ordinalSpread": 0.2}
MAX_DRAWS = 20000

#: Gate thresholds. The first five are the JRC pocket guide's; the double-counting pair is an
#: illustrative two-step setting (the report's call), not a JRC rule.
JRC_COVERAGE = 0.65
SKEW_LIMIT, KURTOSIS_LIMIT, KURTOSIS_ALONE = 2.0, 3.5, 10.0
WINSORISE_MAX = 5
DOMINATES = 0.95
BARELY_COUNTS = 0.3
SIZE_BIAS = 0.6
DOUBLE_WARN, DOUBLE_STRONG = 0.8, 0.9
GATES = ("minimum_data", "coverage", "outliers", "dominance", "barely_counts", "size_bias",
         "double_counting")

#: The contract's visible list of missing markers (section 1), never pandas' defaults.
MISSING_MARKERS = ("", "n/a", "N/A", "NULL", "null", "none", "-", "Unknown", "unknown", "TBD",
                   "To be confirmed")
NUMERIC_ROLES = {"count", "measure", "score", "percentage", "money", "year", "latitude",
                 "longitude"}
LABEL_ROLES = {"ordinal", "category"}
FLAG_WORDS = {"yes": 1.0, "y": 1.0, "true": 1.0, "1": 1.0,
              "no": 0.0, "n": 0.0, "false": 0.0, "0": 0.0}

#: Screens: the JsonLogic subset the engine runs. Anything else is refused, never ignored.
SCREEN_OPERATORS = ("var", "==", "!=", "<", "<=", ">", ">=", "and", "or", "!", "in", "missing")
SCREEN_MAX_DEPTH = 32
SCREEN_MAX_NODES = 500

_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


# ---------- small helpers ----------

def _clean(value: Any) -> Any:
    """JSON-safe: NaN and infinities become null, numpy scalars become Python ones."""
    if value is None:
        return None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        value = float(value)
        return None if math.isnan(value) or math.isinf(value) else value
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [_clean(v) for v in value]
    return value


def _out(payload: dict) -> str:
    return json.dumps(_clean(payload), allow_nan=False)


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _missing(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, (float, np.floating)):
        return math.isnan(v)
    return v is pd.NA or v is pd.NaT


def _py(v: Any) -> Any:
    """A typed cell as a plain Python value, None for missing."""
    if _missing(v):
        return None
    if isinstance(v, np.generic):
        return v.item()
    return v


def _label(v: Any) -> str | None:
    """A category label as text: 3.0 reads as "3", so a 1 to 5 scale can use an ordinal map."""
    v = _py(v)
    if v is None:
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _fmt(x: float | None) -> str:
    if x is None:
        return "no value"
    x = float(x)
    if x.is_integer() and abs(x) < 1e15:
        return str(int(x))
    return f"{x:.4g}" if abs(x) < 1e4 else f"{x:.0f}"


def _said(v: Any) -> str:
    """A value the visitor gave, quoted for a sentence (never a Python repr)."""
    if v is None:
        return "empty"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, (int, float)) and math.isfinite(v):
        return _fmt(v)
    if isinstance(v, float):
        return "not a number"
    return "not a single value"


def _pct(share: float) -> str:
    text = f"{100 * share:.1f}"
    return (text[:-2] if text.endswith(".0") else text) + "%"


def _fsum_mean(xs: list[float]) -> float:
    return math.fsum(xs) / len(xs)


def _pearson(x: list[float], y: list[float]) -> float | None:
    """Pearson correlation with exact (fsum) sums, so native and Pyodide agree to the bit."""
    if len(x) < 3:
        return None
    mx, my = _fsum_mean(x), _fsum_mean(y)
    dx = [a - mx for a in x]
    dy = [b - my for b in y]
    sxx = math.fsum(a * a for a in dx)
    syy = math.fsum(b * b for b in dy)
    if sxx <= 0 or syy <= 0:
        return None
    r = math.fsum(a * b for a, b in zip(dx, dy)) / math.sqrt(sxx * syy)
    return max(-1.0, min(1.0, r))


def _average_ranks(x: list[float]) -> list[float]:
    return pd.Series(x, dtype=float).rank(method="average").tolist()


def _spearman(x: list[float], y: list[float]) -> float | None:
    if len(x) < 3:
        return None
    return _pearson(_average_ranks(x), _average_ranks(y))


def _competition_ranks(scores: np.ndarray) -> np.ndarray:
    """1 + the number of sites scoring strictly higher, so tied sites share a rank."""
    order = np.argsort(-scores, kind="stable")
    ordered = scores[order]
    new = np.empty(len(scores), dtype=bool)
    new[:1] = True
    new[1:] = ordered[1:] != ordered[:-1]
    ranks_sorted = np.maximum.accumulate(np.where(new, np.arange(1, len(scores) + 1), 0))
    ranks = np.empty(len(scores), dtype=np.int64)
    ranks[order] = ranks_sorted
    return ranks


def _top_k(n: int) -> int:
    """The top k a share is reported for: 10 sites, or 10% of them when there are under 100."""
    return max(1, min(10, math.ceil(0.1 * n)))


# ---------- screens: a JsonLogic subset, interpreted, never eval'd ----------

class ScreenError(ValueError):
    """A screen the engine will not run, with the reason in words."""


def _logic_nodes(logic: Any, depth: int = 0, seen: list[int] | None = None) -> set[str]:
    """Check a screen's shape and operators; return the column names it reads."""
    seen = seen if seen is not None else [0]
    seen[0] += 1
    if seen[0] > SCREEN_MAX_NODES or depth > SCREEN_MAX_DEPTH:
        raise ScreenError("is too long or too deeply nested to check")
    if isinstance(logic, list):
        out: set[str] = set()
        for item in logic:
            out |= _logic_nodes(item, depth + 1, seen)
        return out
    if isinstance(logic, dict):
        if len(logic) != 1:
            raise ScreenError("has a rule with more than one operator in the same braces")
        (op, args), = logic.items()
        if op not in SCREEN_OPERATORS:
            raise ScreenError(f'uses "{op}", which screens do not support (use one of '
                              f'{", ".join(SCREEN_OPERATORS)})')
        if op == "var":
            name = args[0] if isinstance(args, list) and args else args
            if not isinstance(name, str) or not name:
                raise ScreenError('has a "var" without a column name')
            if isinstance(args, list) and len(args) > 2:
                raise ScreenError('has a "var" with more than a column and a default')
            if isinstance(args, list) and len(args) == 2:
                _logic_nodes(args[1], depth + 1, seen)
            return {name}
        if op == "missing":
            names = args if isinstance(args, list) else [args]
            if not names or not all(isinstance(n, str) and n for n in names):
                raise ScreenError('has a "missing" that does not list column names')
            return set(names)
        items = args if isinstance(args, list) else [args]
        arity = {"==": (2, 2), "!=": (2, 2), "<": (2, 3), "<=": (2, 3), ">": (2, 2),
                 ">=": (2, 2), "in": (2, 2), "!": (1, 1), "and": (1, None), "or": (1, None)}[op]
        if len(items) < arity[0] or (arity[1] is not None and len(items) > arity[1]):
            raise ScreenError(f'gives "{op}" {len(items)} argument(s)')
        out = set()
        for item in items:
            out |= _logic_nodes(item, depth + 1, seen)
        return out
    if logic is None or isinstance(logic, (str, bool)) or _is_number(logic):
        return set()
    raise ScreenError("contains a value that is not text, a number, true, false or null")


def _truthy(v: Any) -> bool:
    if isinstance(v, list):
        return len(v) > 0
    if v is None or v is False or v == "":
        return False
    if _is_number(v) or isinstance(v, float):
        return v == v and v != 0
    return True


def _as_number(v: Any) -> float | None:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v) if math.isfinite(v) else None
    if isinstance(v, str):
        try:
            x = float(v.strip())
        except ValueError:
            return None
        return x if math.isfinite(x) else None
    return None


def _loose_equal(a: Any, b: Any) -> bool:
    """== as screens use it: numbers as numbers (a number written as text too), text as text."""
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    x, y = _as_number(a), _as_number(b)
    return x is not None and y is not None and x == y


def _strict_equal(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if _is_number(a) and _is_number(b):
        return float(a) == float(b)
    return type(a) is type(b) and a == b


def evaluate(logic: Any, data: Mapping[str, Any]) -> Any:
    """Evaluate a checked screen against one site's values (missing values are None).

    Ordering comparisons (<, <=, >, >=) need numbers, and are false when a side is missing or
    is text that is not a number, so a missing value never passes a numeric screen silently.
    """
    if isinstance(logic, list):
        return [evaluate(item, data) for item in logic]
    if not isinstance(logic, dict):
        return logic
    (op, args), = logic.items()
    if op == "var":
        name, default = (args[0], args[1] if len(args) > 1 else None) if isinstance(args, list) \
            else (args, None)
        value = data.get(name)
        return evaluate(default, data) if value is None else value
    if op == "missing":
        names = args if isinstance(args, list) else [args]
        return [n for n in names if data.get(n) is None or data.get(n) == ""]
    items = args if isinstance(args, list) else [args]
    if op == "and":
        value = None
        for item in items:
            value = evaluate(item, data)
            if not _truthy(value):
                return value
        return value
    if op == "or":
        value = None
        for item in items:
            value = evaluate(item, data)
            if _truthy(value):
                return value
        return value
    values = [evaluate(item, data) for item in items]
    if op == "!":
        return not _truthy(values[0])
    if op == "==":
        return _loose_equal(values[0], values[1])
    if op == "!=":
        return not _loose_equal(values[0], values[1])
    if op == "in":
        needle, hay = values
        if isinstance(hay, list):
            return any(_strict_equal(needle, h) for h in hay)
        if isinstance(hay, str) and isinstance(needle, str):
            return needle in hay
        return False
    numbers = [_as_number(v) for v in values]
    if any(x is None for x in numbers):
        return False
    pairs = list(zip(numbers, numbers[1:]))
    compare = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
               ">": lambda a, b: a > b, ">=": lambda a, b: a >= b}[op]
    return all(compare(a, b) for a, b in pairs)


# ---------- the spec ----------

def _entries_by_name(entries: Any) -> dict[str, dict] | None:
    if entries is None:
        return None
    if isinstance(entries, dict):
        entries = entries.get("fields", [])
    return {str(e["name"]): e for e in entries if isinstance(e, dict) and e.get("name")}


def _refusal(code: str, message: str, column: str | None = None) -> dict:
    out = {"code": code, "message": message}
    if column is not None:
        out["column"] = column
    return out


def _check_value(column: str, direction: str, value: Any, entry: dict | None) -> list[dict]:
    """Refusals for one criterion's value function."""
    bad: list[dict] = []
    if not isinstance(value, dict) or value.get("kind") not in KINDS:
        return [_refusal("value_function", f"Choose how {column} turns into credit: linear, "
                         "threshold, target or ordinal.", column)]
    kind = value["kind"]
    role = (entry or {}).get("evsient:role")
    if kind != "ordinal" and role in LABEL_ROLES:
        return [_refusal("value_function", f"{column} is a set of categories, not numbers. Give "
                         "each category a value between 0 and 1 with an ordinal map.", column)]
    if kind in ("linear", "threshold"):
        worst, best = value.get("worst"), value.get("best")
        if kind == "linear" and worst is None and best is None:
            pass  # anchors default to the observed range and are pinned by run()
        elif not (_is_number(worst) and _is_number(best)):
            return [_refusal("value_function", f"Give {column} both a worst and a best value, "
                             "as numbers.", column)]
        if direction == "neither":
            return [_refusal("value_direction", f"You said neither direction is better for "
                             f"{column}, so it needs a target value function, not a {kind} "
                             "one.", column)]
        if _is_number(worst) and _is_number(best):
            if worst == best:
                bad.append(_refusal("value_direction", f"The worst and best values for {column} "
                                    f"are both {_fmt(best)}. Set them apart.", column))
            elif direction == "higher_better" and best < worst:
                bad.append(_refusal("value_direction", f"For {column}, higher is better, so its "
                                    f"best value ({_fmt(best)}) must be above its worst "
                                    f"({_fmt(worst)}).", column))
            elif direction == "lower_better" and best > worst:
                bad.append(_refusal("value_direction", f"For {column}, lower is better, so its "
                                    f"best value ({_fmt(best)}) must be below its worst "
                                    f"({_fmt(worst)}).", column))
    elif kind == "target":
        low, target, high = value.get("low"), value.get("target"), value.get("high")
        if direction != "neither":
            bad.append(_refusal("value_direction", f"A target suits a column where neither "
                                f"direction is better, but you said {DIRECTION_WORDS[direction]} "
                                f"for {column}. Use a linear or threshold value function.",
                                column))
        elif not all(_is_number(x) for x in (low, target, high)):
            bad.append(_refusal("value_function", f"Give {column} a target and the low and high "
                                "values where credit runs out, as numbers.", column))
        elif not low < target < high:
            bad.append(_refusal("value_function", f"For {column}, the low value ({_fmt(low)}) "
                                f"must be below the target ({_fmt(target)}) and the target below "
                                f"the high value ({_fmt(high)}).", column))
    else:
        mapping = value.get("map")
        if not isinstance(mapping, dict) or not mapping:
            return [_refusal("ordinal_map", f"Give each category of {column} a value between 0 "
                             "and 1.", column)]
        for category, credit in mapping.items():
            if not _is_number(credit) or not 0 <= credit <= 1:
                bad.append(_refusal("ordinal_map", f'The value for "{category}" in {column} is '
                                    f"{_said(credit)}; it must be a number from 0 to 1.", column))
        categories = [str(c) for c in (entry or {}).get("categories") or []]
        missing = [c for c in categories if c not in mapping]
        for category in missing:
            bad.append(_refusal("ordinal_map", f'The scale for {column} gives no value for '
                                f'"{category}". Give every category a value between 0 and 1.',
                                column))
        extra = [c for c in mapping if categories and c not in categories]
        for category in extra:
            bad.append(_refusal("ordinal_map", f'The scale for {column} gives a value for '
                                f'"{category}", which is not one of its categories '
                                f'({", ".join(categories)}).', column))
        ordered = (entry or {}).get("categoriesOrdered") and not missing and not extra
        if ordered and not bad and direction in ("higher_better", "lower_better"):
            credits = [mapping[c] for c in categories]
            rising = all(a <= b for a, b in zip(credits, credits[1:]))
            falling = all(a >= b for a, b in zip(credits, credits[1:]))
            order = " < ".join(categories)
            if direction == "higher_better" and not rising:
                bad.append(_refusal("value_direction", f"For {column}, higher is better, so "
                                    f"credit must not fall along {order}.", column))
            if direction == "lower_better" and not falling:
                bad.append(_refusal("value_direction", f"For {column}, lower is better, so "
                                    f"credit must not rise along {order}.", column))
    return bad


def validate(spec: Any, entries: Any = None, *, columns: Any = None) -> dict:
    """Check a spec; return {"ok", "refusals", "spec"} with defaults filled and weights normalised.

    `entries` are the confirmed column dictionary (a list of entries, or a Table Schema with
    `fields`). With them, every criterion's direction must be confirmed by the visitor and agree
    with the spec, and ordinal maps are checked against the column's categories. `columns` is
    the set of column names a run can see (the typed and raw tables), when there is data.
    """
    bad: list[dict] = []
    if not isinstance(spec, dict):
        return {"ok": False, "refusals": [_refusal("spec", "The index settings could not be "
                                                   "read. Build the index again.")], "spec": None}
    by_name = _entries_by_name(entries)
    known = set(by_name or ()) | set(columns or ())
    check_columns = by_name is not None or columns is not None

    if spec.get("pack") != PACK:
        bad.append(_refusal("pack", f"These settings are for {_said(spec.get('pack'))}, not for an "
                            f"index built here ({PACK})."))
    version = spec.get("packVersion")
    match = _SEMVER.match(version) if isinstance(version, str) else None
    if not match:
        bad.append(_refusal("pack", f"The index has no readable version ({_said(version)}); it "
                            "should look like 1.0.0."))
    elif int(match.group(1)) != PACK_MAJOR:
        bad.append(_refusal("pack", f"This index was saved as version {version}; this planner "
                            f"reads version {PACK_MAJOR}."))
    name = spec.get("name")
    if not isinstance(name, str) or not name.strip():
        bad.append(_refusal("name", "Give the index a name, so it is never mistaken for the "
                            "readiness score."))
    elif len(name) > 120:
        bad.append(_refusal("name", "Keep the index's name under 120 characters."))

    criteria = spec.get("criteria")
    if not isinstance(criteria, list):
        criteria = []
    if len(criteria) < MIN_CRITERIA:
        bad.append(_refusal("few_criteria", f"An index needs at least {MIN_CRITERIA} criteria; "
                            f"this one has {len(criteria)}."))
    out_criteria = []
    seen: set[str] = set()
    for position, criterion in enumerate(criteria, start=1):
        if not isinstance(criterion, dict) or not isinstance(criterion.get("column"), str) \
                or not criterion["column"]:
            bad.append(_refusal("column", f"Criterion {position} does not name a column."))
            continue
        column = criterion["column"]
        if column in seen:
            bad.append(_refusal("column", f"{column} is in the index twice. Keep it once and "
                                "give it the weight you want.", column))
            continue
        seen.add(column)
        if check_columns and column not in known:
            bad.append(_refusal("unknown_column", f"There is no column called {column} in this "
                                "file.", column))
            continue
        entry = (by_name or {}).get(column)
        direction = criterion.get("direction")
        if direction is None:
            bad.append(_refusal("unconfirmed_direction", f"Confirm whether higher or lower "
                                f"{column} is better before it goes into an index.", column))
            continue
        if direction not in DIRECTIONS:
            bad.append(_refusal("direction", f"The direction for {column} is "
                                f"{_said(direction)}; say higher is better, lower is better, or "
                                "neither.", column))
            continue
        if by_name is not None:
            confirmed = (entry or {}).get("evsient:direction")
            if entry is None or entry.get("evsient:provenance") != "confirmed_by_user" \
                    or confirmed not in DIRECTIONS:
                bad.append(_refusal("unconfirmed_direction", f"Confirm whether higher or lower "
                                    f"{column} is better before it goes into an index.", column))
                continue
            if confirmed != direction:
                bad.append(_refusal("direction_mismatch", f"The index treats {column} as "
                                    f"{DIRECTION_WORDS[direction]}, but you confirmed "
                                    f"{DIRECTION_WORDS[confirmed]}. Change one so they agree.",
                                    column))
                continue
        weight = criterion.get("weight")
        if not _is_number(weight) or weight <= 0:
            bad.append(_refusal("weight", f"The weight on {column} is {_said(weight)}. Every "
                                "weight must be a number above 0; take the criterion out "
                                "instead.", column))
            continue
        value_bad = _check_value(column, direction, criterion.get("value"), entry)
        bad.extend(value_bad)
        if not value_bad:
            out_criteria.append({"column": column, "direction": direction,
                                 "weight": float(weight), "value": dict(criterion["value"])})

    screens = spec.get("screens") or []
    out_screens = []
    if not isinstance(screens, list):
        bad.append(_refusal("screen", "The screens could not be read."))
        screens = []
    for position, screen in enumerate(screens, start=1):
        reason = screen.get("reason") if isinstance(screen, dict) else None
        if not isinstance(reason, str) or not reason.strip():
            bad.append(_refusal("screen", f"Screen {position} needs a reason, shown beside "
                                "every site it removes."))
            continue
        try:
            used = _logic_nodes(screen.get("logic"))
            if not isinstance(screen.get("logic"), dict):
                raise ScreenError("is not a rule")
        except ScreenError as e:
            bad.append(_refusal("screen", f'The screen "{reason}" {e}.'))
            continue
        unknown = sorted(c for c in used if check_columns and c not in known)
        for column in unknown:
            bad.append(_refusal("unknown_column", f'The screen "{reason}" reads {column}, and '
                                "there is no column called that in this file.", column))
        if not unknown:
            out_screens.append({"logic": screen["logic"], "reason": reason})

    missing = spec.get("missing", "no_credit")
    if missing not in MISSING_POLICIES:
        bad.append(_refusal("missing", f"Missing values can only earn no credit here "
                            f"(\"no_credit\"), not {_said(missing)}."))
    coverage = spec.get("minCoverage", DEFAULT_MIN_COVERAGE)
    if not _is_number(coverage) or not 0 < coverage <= 1:
        bad.append(_refusal("min_coverage", f"The share of criteria a site needs before it is "
                            f"ranked must be above 0 and at most 1, not {_said(coverage)}."))
    robustness = {**DEFAULT_ROBUSTNESS, **(spec.get("robustness") or {})}
    draws, spread = robustness["draws"], robustness["spread"]
    seed, ordinal_spread = robustness["seed"], robustness["ordinalSpread"]
    if not isinstance(draws, int) or isinstance(draws, bool) or not 0 <= draws <= MAX_DRAWS:
        bad.append(_refusal("robustness", f"The number of draws must be a whole number from 0 "
                            f"to {MAX_DRAWS}, not {_said(draws)}."))
    if not _is_number(spread) or not 0 <= spread <= 1:
        bad.append(_refusal("robustness", f"The weight spread must be from 0 to 1, not "
                            f"{_said(spread)}."))
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        bad.append(_refusal("robustness", f"The seed must be a whole number of 0 or more, not "
                            f"{_said(seed)}."))
    if not _is_number(ordinal_spread) or not 0 <= ordinal_spread <= 0.5:
        bad.append(_refusal("robustness", f"The ordinal spread must be from 0 to 0.5, not "
                            f"{_said(ordinal_spread)}."))

    if bad:
        return {"ok": False, "refusals": bad, "spec": None}
    # Weights that already sum to 1 are kept as they are, so a spec a run returns runs again to
    # the same numbers (normalising is idempotent).
    total = math.fsum(c["weight"] for c in out_criteria)
    if abs(total - 1.0) > 1e-12:
        for c in out_criteria:
            c["weight"] = c["weight"] / total
    normalised = {
        "pack": PACK, "packVersion": version, "name": name.strip(),
        "criteria": out_criteria, "screens": out_screens, "missing": missing,
        "minCoverage": float(coverage),
        "robustness": {"draws": draws, "spread": float(spread), "seed": seed,
                       "ordinalSpread": float(ordinal_spread)},
    }
    return {"ok": True, "refusals": [], "spec": normalised}


# ---------- reading a raw table (a minimal reader, for the bridge and tests) ----------

def read_typed(raw: pd.DataFrame, entries: Any) -> pd.DataFrame:
    """The typed table a run scores: numbers as floats, categories as their labels, flags 1/0.

    A deliberately small reader so this module stands alone. Missing markers are the contract's
    visible list plus each entry's `missingValues`. A number that does not read is missing, never
    guessed; a decimal comma is honoured only when the entry's reading report says so. A label is
    matched to the entry's categories ignoring case and spaces. Other roles keep their text.
    """
    by_name = _entries_by_name(entries) or {}
    out: dict[str, list] = {}
    numeric: set[str] = set()
    for name, entry in by_name.items():
        if name not in raw.columns:
            continue
        role = entry.get("evsient:role")
        markers = set(MISSING_MARKERS) | {str(m) for m in entry.get("missingValues") or []}
        comma = (entry.get("evsient:reading") or {}).get("decimalSeparator") == ","
        lookup = {str(c).strip().lower(): str(c) for c in entry.get("categories") or []}
        values: list = []
        for cell in raw[name].tolist():
            text = "" if _missing(cell) else str(cell).strip()
            if text in markers:
                values.append(None)
            elif role in NUMERIC_ROLES:
                if comma and "." not in text:
                    text = text.replace(",", ".")
                try:
                    x = float(text)
                except ValueError:
                    x = None
                values.append(x if x is not None and math.isfinite(x) else None)
            elif role == "flag":
                values.append(FLAG_WORDS.get(text.lower()))
            elif role in LABEL_ROLES and lookup:
                values.append(lookup.get(text.lower()))
            else:
                values.append(text)
        if role in NUMERIC_ROLES or role == "flag":
            numeric.add(name)
        out[name] = values
    frame = pd.DataFrame(index=raw.index)
    for name, values in out.items():
        if name in numeric:
            frame[name] = pd.Series([np.nan if v is None else v for v in values],
                                    index=raw.index, dtype=float)
        else:
            frame[name] = pd.Series(values, index=raw.index, dtype=object)
    return frame


# ---------- running an index ----------

def _numeric(series: pd.Series) -> tuple[np.ndarray, str | None]:
    """A typed column as floats (NaN for missing), and the first cell that is not a number."""
    out = np.full(len(series), np.nan)
    for i, v in enumerate(series.tolist()):
        v = _py(v)
        if v is None:
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            x = _as_number(v)
            if x is None:
                return out, str(v)
            v = x
        out[i] = float(v)
    return out, None


def _value_of(value: dict, x: np.ndarray) -> np.ndarray:
    """The value function on numbers, bounded to [0, 1]; NaN stays NaN (no credit later)."""
    if value["kind"] == "target":
        low, target, high = value["low"], value["target"], value["high"]
        rising = (x - low) / (target - low)
        falling = (high - x) / (high - target)
        v = np.where(x <= target, rising, falling)
    else:
        v = (x - value["worst"]) / (value["best"] - value["worst"])
    return np.clip(v, 0.0, 1.0)


def _describe(criterion: dict) -> str:
    """The formula card's line for one value function."""
    value, column = criterion["value"], criterion["column"]
    kind = value["kind"]
    if kind == "linear":
        return (f"{column}: no credit at {_fmt(value['worst'])}, full credit at "
                f"{_fmt(value['best'])}, in a straight line between.")
    if kind == "threshold":
        word = "below" if value["best"] > value["worst"] else "above"
        other = "above" if word == "below" else "below"
        return (f"{column}: no credit {word} {_fmt(value['worst'])}, full credit at or {other} "
                f"{_fmt(value['best'])}, in a straight line between.")
    if kind == "target":
        return (f"{column}: full credit at {_fmt(value['target'])}, falling in a straight line "
                f"to no credit at {_fmt(value['low'])} and at {_fmt(value['high'])}.")
    pairs = ", ".join(f"{k} = {_fmt(v)}" for k, v in value["map"].items())
    return f"{column}: {pairs}."


def _refused(spec: Any, refusals: list[dict], sites: int | None = None,
             criteria: int | None = None) -> dict:
    name = spec.get("name") if isinstance(spec, dict) else None
    name = name if isinstance(name, str) else None
    gates = []
    codes = {r["code"] for r in refusals}
    if codes & {"few_criteria", "few_sites", "constant", "unconfirmed_direction"}:
        gates.append(_minimum_data_gate(refusals, sites, criteria))
    return {"official": False, "name": name, "badge": BADGE, "refused": True,
            "refusals": refusals, "spec": None, "formula": [], "summary": None, "sites": [],
            "unranked": [], "excluded": [], "rankChanges": [], "robustness": None,
            "gatesChecked": ["minimum_data"], "gates": gates}


def _minimum_data_gate(refusals: list[dict], sites: int | None, criteria: int | None) -> dict:
    return {
        "id": "minimum_data", "level": "block",
        "message": (f"An index needs at least {MIN_CRITERIA} criteria and {MIN_SITES} sites to "
                    "rank, a confirmed direction for every column, and no column that is the "
                    "same for every site. This one does not have them yet."),
        "columns": sorted({r["column"] for r in refusals if r.get("column")}),
        "numbers": {
            "criteria": criteria, "minCriteria": MIN_CRITERIA,
            "sites": sites, "minSites": MIN_SITES,
            "constant": sorted(r["column"] for r in refusals if r["code"] == "constant"),
            "unconfirmed": sorted(r["column"] for r in refusals
                                  if r["code"] == "unconfirmed_direction"),
        },
    }


def run(typed: pd.DataFrame, raw: pd.DataFrame, spec: dict, *,
        population_column: str | None = None, entries: Any = None,
        name_column: str | None = None) -> dict:
    """Run a visitor's index on a typed table. Returns a JSON-ready dict; never raises on data.

    `typed` and `raw` share an index, which is the site id. `typed` holds the dictionary's
    reading of each column (numbers as floats, categories as labels, flags 1/0); `raw` holds the
    text as uploaded, shown beside each driver and read by screens for columns `typed` lacks.
    A spec that cannot run comes back with `"refused": true` and the reasons in words.
    """
    raw = raw if raw is not None else pd.DataFrame(index=typed.index)
    columns = set(map(str, typed.columns)) | set(map(str, raw.columns))
    check = validate(spec, entries, columns=columns)
    refusals = list(check["refusals"])
    if population_column is not None and population_column not in columns:
        refusals.append(_refusal("unknown_column", f"There is no column called "
                                 f"{population_column} to check size bias against.",
                                 population_column))
    n_sites = len(typed)
    n_criteria = len(spec.get("criteria") or []) if isinstance(spec, dict) else None
    ids = [str(i) for i in typed.index]
    if "" in ids:
        refusals.append(_refusal("site_id", "Some sites have no id. Give every site its own id."))
    elif len(set(ids)) != len(ids):
        seen_ids: set[str] = set()
        dupe = next(i for i in ids if i in seen_ids or seen_ids.add(i))
        refusals.append(_refusal("site_id", f"Two sites share the id {dupe}. Give every site its "
                                 "own id."))
    elif not raw.index.equals(typed.index):
        if raw.index.has_duplicates:
            refusals.append(_refusal("site_id", "The raw table repeats a site id, so its rows "
                                     "cannot be matched to the sites."))
        else:
            raw = raw.reindex(typed.index)
    if n_sites < MIN_SITES:
        refusals.append(_refusal("few_sites", f"An index needs at least {MIN_SITES} sites to "
                                 f"rank; this file has {n_sites}."))
    if refusals:
        return _refused(spec, refusals, n_sites, n_criteria)
    given = {c["column"]: c["weight"] for c in spec["criteria"]}
    spec = check["spec"]
    crits = spec["criteria"]

    def column_of(name: str) -> pd.Series:
        return typed[name] if name in typed.columns else raw[name]

    # Pin anchors and read every criterion over the whole file, before any screen.
    numbers: dict[str, np.ndarray] = {}
    labels: dict[str, list] = {}
    for c in crits:
        series, value, column = column_of(c["column"]), c["value"], c["column"]
        if value["kind"] == "ordinal":
            labels[column] = [_label(v) for v in series.tolist()]
            unmapped = sorted({x for x in labels[column] if x is not None} - set(value["map"]))
            for category in unmapped:
                refusals.append(_refusal("ordinal_map", f'The scale for {column} gives no value '
                                         f'for "{category}". Give every category a value between '
                                         "0 and 1.", column))
            continue
        x, text = _numeric(series)
        if text is not None:
            refusals.append(_refusal("value_function", f'{column} holds text such as "{text}", '
                                     "not numbers. Give each category a value with an ordinal "
                                     "map.", column))
            continue
        numbers[column] = x
        if value["kind"] == "linear" and value.get("worst") is None:
            seen = x[~np.isnan(x)]
            if not seen.size or seen.min() == seen.max():
                said = f"is {_fmt(float(seen[0]))} for every site" if seen.size else "has no values"
                refusals.append(_refusal("constant", f"{column} {said}, so it cannot separate "
                                         "them. Take it out of the index.", column))
                continue
            low, high = float(seen.min()), float(seen.max())
            worst, best = (low, high) if c["direction"] == "higher_better" else (high, low)
            value.update({"worst": worst, "best": best, "pinnedFrom": "observed range"})
    if refusals:
        return _refused(spec, refusals, n_sites, n_criteria)

    # Screens, before scoring.
    excluded: list[dict] = []
    keep = np.ones(n_sites, dtype=bool)
    if spec["screens"]:
        cells: dict[str, list] = {}
        needed = set().union(*(_logic_nodes(s["logic"]) for s in spec["screens"]))
        for name in needed:
            cells[name] = [_py(v) for v in column_of(name).tolist()]
            if name not in typed.columns:
                cells[name] = [None if v is None or str(v).strip() in MISSING_MARKERS
                               else str(v).strip() for v in cells[name]]
        for i in range(n_sites):
            row = {name: cells[name][i] for name in needed}
            reasons = []
            for position, screen in enumerate(spec["screens"], start=1):
                if not _truthy(evaluate(screen["logic"], row)):
                    used = sorted(_logic_nodes(screen["logic"]))
                    reasons.append({"screen": position, "reason": screen["reason"],
                                    "missing": [u for u in used if row.get(u) is None]})
            if reasons:
                keep[i] = False
                excluded.append({"siteId": ids[i], "name": None, "reasons": reasons, "_row": i})

    # Values over the screened sites.
    idx = np.flatnonzero(keep)
    n_kept = len(idx)
    if n_kept < MIN_SITES:
        refusals.append(_refusal("few_sites", f"An index needs at least {MIN_SITES} sites to "
                                 f"rank; {n_kept} are left after the screens."))
        return _refused(spec, refusals, n_kept, len(crits))
    values = np.full((n_kept, len(crits)), np.nan)
    for j, c in enumerate(crits):
        column = c["column"]
        if c["value"]["kind"] == "ordinal":
            mapping = c["value"]["map"]
            values[:, j] = [np.nan if labels[column][i] is None else mapping[labels[column][i]]
                            for i in idx]
        else:
            values[:, j] = _value_of(c["value"], numbers[column][idx])
    for c in crits:
        column = c["column"]
        if c["value"]["kind"] == "ordinal":
            distinct = {labels[column][i] for i in idx} - {None}
        else:
            kept = numbers[column][idx]
            distinct = set(kept[~np.isnan(kept)].tolist())
        if len(distinct) < 2:
            if distinct:
                only = next(iter(distinct))
                said = f"is {only if isinstance(only, str) else _fmt(only)} for every site"
            else:
                said = "has no values for the sites"
            refusals.append(_refusal("constant", f"{column} {said} left after the screens, so it "
                                     "cannot separate them. Take it out of the index.", column))
    present = ~np.isnan(values)
    completeness = present.sum(axis=1) / len(crits)
    eligible = completeness >= spec["minCoverage"] - 1e-12
    if not refusals and int(eligible.sum()) < MIN_SITES:
        refusals.append(_refusal("few_sites", f"An index needs at least {MIN_SITES} sites to "
                                 f"rank; {int(eligible.sum())} are left after the screens and the "
                                 "coverage rule."))
    if refusals:
        return _refused(spec, refusals, int(eligible.sum()), len(crits))

    weights = np.array([c["weight"] for c in crits])
    credit = np.where(present, values, 0.0)
    points = credit * (100.0 * weights)[None, :]
    maxima = 100.0 * weights
    scores = np.zeros(n_kept)
    best = np.zeros(n_kept)
    for j in range(len(crits)):
        scores = scores + points[:, j]
        best = best + np.where(present[:, j], points[:, j], maxima[j])

    names = None
    if name_column is not None and name_column in raw.columns:
        names = [None if _missing(v) else str(v) for v in raw[name_column].tolist()]
    raw_cells = {c["column"]: (raw[c["column"]].tolist() if c["column"] in raw.columns
                               else typed[c["column"]].tolist()) for c in crits}

    def site_record(k: int) -> dict:
        i = idx[k]
        drivers = []
        for j, c in enumerate(crits):
            cell = raw_cells[c["column"]][i]
            drivers.append({
                "column": c["column"], "weight": c["weight"],
                "value": float(credit[k, j]), "points": float(points[k, j]),
                "max": float(maxima[j]), "absent": not bool(present[k, j]),
                "raw": None if _missing(cell) else str(cell),
            })
        return {
            "siteId": ids[i], "name": names[i] if names else None,
            "score": float(scores[k]),
            "bounds": {"worst": float(scores[k]), "best": float(best[k])},
            "completeness": float(completeness[k]),
            "missing": [c["column"] for j, c in enumerate(crits) if not present[k, j]],
            "drivers": drivers,
        }

    ranked_k = np.flatnonzero(eligible)
    unranked_k = np.flatnonzero(~eligible)
    ranks = _competition_ranks(scores[ranked_k])
    order = ranked_k[np.lexsort((ranked_k, ranks))]
    rank_of = dict(zip(ranked_k.tolist(), ranks.tolist()))
    n_ranked = len(order)
    k_top = _top_k(n_ranked)

    sites = []
    for k in order:
        record = site_record(k)
        record["rank"] = int(rank_of[int(k)])
        sites.append(record)
    unranked = []
    for k in unranked_k:
        record = site_record(k)
        record["reason"] = (f"Has values for {_pct(completeness[k])} of the criteria, under the "
                            f"{_pct(spec['minCoverage'])} a site needs to be ranked.")
        unranked.append(record)
    for record in excluded:
        row = record.pop("_row")
        record["name"] = names[row] if names else None

    rob = spec["robustness"]
    robustness = _robustness(crits, credit[order], labels, idx[order], rob, k_top)
    if robustness is not None:
        for s, low, high, share in zip(sites, robustness.pop("rankLow"),
                                       robustness.pop("rankHigh"), robustness.pop("topShare")):
            s["robustness"] = {"rankLow": int(low), "rankHigh": int(high), "topShare": share,
                               "neverTopK": share == 0.0}
    shares = robustness.pop("pairShares") if robustness is not None else None
    rank_changes = _rank_changes(crits, sites, credit[order], numbers, labels, idx[order],
                                 shares)

    population = None
    if population_column is not None:
        population, _ = _numeric(column_of(population_column))
        population = population[idx[order]]
    influence = [_pearson(credit[order, j].tolist(), scores[order].tolist())
                 for j in range(len(crits))]
    gates = _gates(crits, influence, values[order], present, scores[order], numbers, idx,
                   population, population_column)

    with_missing = int((~present).any(axis=1).sum())
    summary = {
        "sites": n_sites, "excluded": len(excluded), "unranked": len(unranked),
        "ranked": n_ranked, "withMissing": with_missing, "k": k_top,
        "disclosure": (f"{with_missing} of {n_kept} sites have at least one missing value; "
                       "missing values earn no credit. Sites with values for under "
                       f"{_pct(spec['minCoverage'])} of the criteria are listed but not ranked."),
        "note": (f"{spec['name']} is your own index, not an official EV-SIENT score. It is a "
                 "weighted sum: each criterion adds weight x value x 100 points."),
    }
    formula = []
    for j, c in enumerate(crits):
        formula.append({
            "column": c["column"], "direction": c["direction"],
            "directionWords": DIRECTION_WORDS[c["direction"]],
            "weight": c["weight"], "weightGiven": given[c["column"]], "value": c["value"],
            "describe": _describe(c),
            "coverage": float(present[:, j].mean()) if n_kept else 0.0,
            "indexCorrelation": influence[j],
        })
    return {
        "official": False, "name": spec["name"], "badge": BADGE, "refused": False,
        "refusals": [], "spec": spec, "formula": formula, "summary": summary,
        "sites": sites, "unranked": unranked, "excluded": excluded,
        "rankChanges": rank_changes, "robustness": robustness,
        "gatesChecked": [g for g in GATES if g != "size_bias" or population is not None],
        "gates": gates,
    }


# ---------- robustness ----------

def _concentration(weights: np.ndarray, spread: float) -> float:
    """The Dirichlet concentration for a spread: each weight's sd is about `spread` x itself.

    For Dirichlet(kappa x w), sd(W_i) / w_i = sqrt((1 - w_i) / (w_i (kappa + 1))). kappa is set
    so the average of that ratio over the criteria equals the spread.
    """
    ratio = float(np.mean(np.sqrt((1 - weights) / weights)))
    return max(2.0, (ratio / spread) ** 2 - 1)


def _ordinal_plan(criterion: dict) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray]:
    """Categories, their credit, and the band each may move in when the map is nudged.

    The categories at the map's lowest and highest credit stay put (they are the anchors); the
    ones between move by up to `ordinalSpread`, never past their neighbours on the scale.
    """
    mapping = criterion["value"]["map"]
    cats = list(mapping)
    base = np.array([float(mapping[c]) for c in cats])
    order = sorted(range(len(cats)), key=lambda i: (base[i], i))
    lo, hi = base.copy(), base.copy()
    top, bottom = base.max(), base.min()
    for pos, i in enumerate(order):
        if base[i] in (top, bottom):
            continue
        neighbours = [base[order[p]] for p in (pos - 1, pos + 1) if 0 <= p < len(order)]
        lo[i], hi[i] = min(neighbours), max(neighbours)
    return cats, base, lo, hi


def _robustness(crits: list[dict], credit: np.ndarray, labels: dict, rows: np.ndarray,
                rob: dict, k_top: int) -> dict | None:
    """Rank bands from draws of weights and ordinal maps, for the ranked sites in rank order.

    Scores are added criterion by criterion with elementwise operations only (no matrix
    product), so a site's score in a draw does not depend on how a BLAS kernel blocks the sum,
    tied sites stay exactly tied, and native and Pyodide count the same ranks.
    """
    draws = rob["draws"]
    n, m = credit.shape
    if draws == 0 or n == 0:
        return None
    weights = np.array([c["weight"] for c in crits])
    rng = np.random.default_rng(rob["seed"])
    if rob["spread"] > 0:
        kappa = _concentration(weights, rob["spread"])
        drawn = rng.dirichlet(kappa * weights, size=draws)
    else:
        kappa = None
        drawn = np.tile(weights, (draws, 1))
    scores = np.zeros((draws, n))
    nudged = []
    for j, c in enumerate(crits):
        w = 100.0 * drawn[:, j][:, None]
        if c["value"]["kind"] == "ordinal" and rob["ordinalSpread"] > 0:
            cats, base, lo, hi = _ordinal_plan(c)
            moving = lo < hi
            half = rob["ordinalSpread"]
            noise = rng.uniform(-half, half, size=(draws, len(cats)))
            maps = np.where(moving[None, :], np.clip(base[None, :] + noise, lo, hi), base[None, :])
            code_of = {cat: i for i, cat in enumerate(cats)}
            codes = np.array([code_of.get(labels[c["column"]][r], -1) for r in rows])
            cell = np.where(codes[None, :] >= 0, maps[:, np.maximum(codes, 0)], 0.0)
            if moving.any():
                nudged.append(c["column"])
            scores = scores + w * cell
        else:
            scores = scores + w * credit[:, j][None, :]
    order = np.argsort(-scores, axis=1, kind="stable")
    ordered = np.take_along_axis(scores, order, axis=1)
    new = np.ones_like(ordered, dtype=bool)
    new[:, 1:] = ordered[:, 1:] != ordered[:, :-1]
    positions = np.broadcast_to(np.arange(1, n + 1), (draws, n))
    ranks_sorted = np.maximum.accumulate(np.where(new, positions, 0), axis=1)
    ranks = np.empty_like(ranks_sorted)
    np.put_along_axis(ranks, order, ranks_sorted, axis=1)
    low = np.percentile(ranks, 5, axis=0, method="lower")
    high = np.percentile(ranks, 95, axis=0, method="higher")
    top = (ranks <= k_top).sum(axis=0) / draws
    pair_shares = ((scores[:, :-1] >= scores[:, 1:]).sum(axis=0) / draws).tolist()
    return {
        "draws": draws, "spread": rob["spread"], "seed": rob["seed"],
        "ordinalSpread": rob["ordinalSpread"], "concentration": kappa, "k": k_top,
        "ordinalMapsNudged": nudged,
        "method": ("Weights drawn from a Dirichlet distribution centred on your weights; "
                   "ordinal values between the ends of each scale nudged within their "
                   "neighbours; ranks counted in every draw."),
        "rankLow": low.tolist(), "rankHigh": high.tolist(), "topShare": top.tolist(),
        "pairShares": pair_shares,
    }


# ---------- what would change the rank ----------

def _raw_for(criterion: dict, target_value: float, current_raw: float | None) -> float:
    """The raw number at which a numeric value function gives `target_value`."""
    value = criterion["value"]
    if value["kind"] == "target":
        below = value["low"] + target_value * (value["target"] - value["low"])
        above = value["high"] - target_value * (value["high"] - value["target"])
        if current_raw is not None and abs(current_raw - above) < abs(current_raw - below):
            return float(above)
        return float(below)
    return float(value["worst"] + target_value * (value["best"] - value["worst"]))


def _rank_changes(crits: list[dict], sites: list[dict], credit: np.ndarray, numbers: dict,
                  labels: dict, rows: np.ndarray, shares: list[float] | None) -> list[dict]:
    """For each adjacent pair, the exact weight shift and value change that would swap them.

    Shifting criterion c's weight by t, with the others rescaled to keep the sum at 1, moves the
    gap between the two sites linearly in t, so the shift at which they tie is exact. A shift
    past it puts the lower site above. The value change is how far the lower site's own value on
    c would have to rise to draw level, read back into the column's units.
    """
    weights = np.array([c["weight"] for c in crits])
    position = {c["column"]: j for j, c in enumerate(crits)}
    out = []
    for p in range(len(sites) - 1):
        a, b = sites[p], sites[p + 1]
        d = credit[p] - credit[p + 1]
        gap = a["score"] - b["score"]
        shifts, changes = [], []
        for j, c in enumerate(crits):
            w = weights[j]
            rest = math.fsum(weights[i] * d[i] for i in range(len(crits)) if i != j)
            slope = d[j] - rest / (1 - w)
            if gap == 0:
                t = 0.0
            elif slope == 0:
                t = None
            else:
                t = -(gap / 100.0) / slope
            # Past the tie the lower site leads, so the shift counts only if the weight can
            # still move beyond it inside (0, 1).
            if t is not None and 0.0 < w + t < 1.0:
                shifts.append({"column": c["column"], "shift": t, "newWeight": w + t})
            if gap == 0:
                continue
            need = credit[p + 1, j] + (gap / 100.0) / w
            if need > 1.0 + 1e-12:
                continue
            need = min(need, 1.0)
            column = c["column"]
            if c["value"]["kind"] == "ordinal":
                mapping = c["value"]["map"]
                options = [(v, cat) for cat, v in mapping.items() if v >= need - 1e-12]
                to_value, to = min(options, key=lambda o: (o[0], list(mapping).index(o[1])))
                change = {"column": column, "from": labels[column][rows[p + 1]], "to": to,
                          "valueFrom": float(credit[p + 1, j]), "valueTo": float(to_value),
                          "ties": abs(to_value - need) <= 1e-12}
            else:
                current = numbers[column][rows[p + 1]]
                current = None if math.isnan(current) else float(current)
                # Reaching `to` draws level; going past it passes, unless `to` is already the
                # full-credit anchor, past which there is no more credit to earn.
                change = {"column": column, "from": current,
                          "to": _raw_for(c, need, current),
                          "valueFrom": float(credit[p + 1, j]), "valueTo": float(need),
                          "ties": True}
                if need >= 1.0:
                    change["capped"] = True
            changes.append(change)
        shifts.sort(key=lambda s: (abs(s["shift"]), position[s["column"]]))
        changes.sort(key=lambda s: (s["valueTo"] - s["valueFrom"], position[s["column"]]))
        record = {"above": a["siteId"], "below": b["siteId"], "gap": gap,
                  "tied": gap == 0, "weightShifts": shifts, "valueChanges": changes,
                  "shareAhead": shares[p] if shares is not None else None,
                  "sentences": _change_sentences(a, b, gap, shifts, changes, crits)}
        out.append(record)
    return out


def _change_sentences(a: dict, b: dict, gap: float, shifts: list, changes: list,
                      crits: list[dict]) -> list[str]:
    above = a["name"] or a["siteId"]
    below = b["name"] or b["siteId"]
    if gap == 0:
        return [f"{below} and {above} are tied."]
    out = []
    if shifts:
        s = shifts[0]
        given = next(c["weight"] for c in crits if c["column"] == s["column"])
        verb = "more" if s["shift"] > 0 else "less"
        out.append(f"Giving {s['column']} {verb} than {_pct(s['newWeight'])} of the weight "
                   f"(now {_pct(given)}) would lift {below} above {above}.")
    if changes:
        ch = changes[0]
        if isinstance(ch["to"], str):
            was = ch["from"] if ch["from"] is not None else "no value"
            end = "draw level with" if ch["ties"] else "pass"
            out.append(f"{below} would {end} {above} if its {ch['column']} were {ch['to']} "
                       f"instead of {was}.")
        elif ch.get("capped"):
            out.append(f"{below} would draw level with {above} if its {ch['column']} reached "
                       f"{_fmt(ch['to'])} (now {_fmt(ch['from'])}).")
        else:
            out.append(f"{below} would pass {above} if its {ch['column']} went past "
                       f"{_fmt(ch['to'])} (now {_fmt(ch['from'])}).")
    if not out:
        out.append(f"No single weight shift or change to one value lifts {below} above {above}.")
    return out


# ---------- gates ----------

def _skew_kurt(x: np.ndarray) -> tuple[float | None, float | None]:
    s = pd.Series(x, dtype=float)
    skew = s.skew() if len(s) >= 3 else None
    kurt = s.kurt() if len(s) >= 4 else None
    clean = lambda v: None if v is None or not math.isfinite(v) else float(v)
    return clean(skew), clean(kurt)


def _outlying(skew: float | None, kurt: float | None) -> bool:
    if skew is None or kurt is None:
        return False
    return (abs(skew) > SKEW_LIMIT and kurt > KURTOSIS_LIMIT) or kurt > KURTOSIS_ALONE


def _winsorise(x: np.ndarray) -> dict:
    """The JRC treatment: cap the most extreme value at the next one, until the rule passes.

    The side follows the sign of the skew at each step, and no more than WINSORISE_MAX of the
    original values are changed (the COIN tool's default), so `resolves` can be false.
    """
    original = np.sort(x)
    x = original.copy()
    while True:
        skew, kurt = _skew_kurt(x)
        if not _outlying(skew, kurt) or int((x != original).sum()) >= WINSORISE_MAX:
            break
        if skew >= 0:
            top = x.max()
            below = x[x < top]
            if not below.size:
                break
            x[x == top] = below.max()
        else:
            bottom = x.min()
            above = x[x > bottom]
            if not above.size:
                break
            x[x == bottom] = above.min()
    capped_high = int((original > x.max()).sum())
    capped_low = int((original < x.min()).sum())
    skew, kurt = _skew_kurt(x)
    return {"cappedHigh": capped_high, "cappedLow": capped_low,
            "cap": float(x.max()) if capped_high else None,
            "floor": float(x.min()) if capped_low else None,
            "skewAfter": skew, "kurtosisAfter": kurt, "resolves": not _outlying(skew, kurt)}


def _gates(crits: list[dict], influence: list[float | None], values: np.ndarray,
           present_kept: np.ndarray, scores: np.ndarray, numbers: dict, kept_rows: np.ndarray,
           population: np.ndarray | None, population_column: str | None) -> list[dict]:
    """The gates, over the screened sites (coverage, outliers) or the ranked ones (the rest).

    `influence` is each criterion's Pearson correlation with the index over the ranked sites,
    on the credit the score adds up (missing as 0); `values` is the ranked sites' credit with
    missing as NaN, for the pairwise double-counting check.
    """
    gates: list[dict] = []
    for j, c in enumerate(crits):
        share = float(present_kept[:, j].mean())
        if share < JRC_COVERAGE:
            gates.append({
                "id": "coverage", "level": "warn", "columns": [c["column"]],
                "message": (f"{c['column']} has a value for {_pct(share)} of the sites being "
                            f"scored, under the {_pct(JRC_COVERAGE)} a criterion should have. "
                            "Sites without it earn no credit for it, so the ranking partly "
                            "reflects which sites were recorded."),
                "numbers": {"coverage": share, "threshold": JRC_COVERAGE,
                            "present": int(present_kept[:, j].sum()),
                            "sites": int(len(present_kept))}})
    for c in crits:
        if c["value"]["kind"] == "ordinal":
            continue
        x = numbers[c["column"]][kept_rows]
        x = x[~np.isnan(x)]
        skew, kurt = _skew_kurt(x)
        if _outlying(skew, kurt):
            fix = _winsorise(x)
            gates.append({
                "id": "outliers", "level": "warn", "columns": [c["column"]],
                "message": (f"{c['column']} has a few extreme values (skewness {skew:.2f}, "
                            f"kurtosis {kurt:.2f}). Extreme values can set the scale for every "
                            "other site. Capping the most extreme ones at the next value "
                            "(winsorising), or moving the anchors in, would reduce their pull."),
                "numbers": {"skewness": skew, "kurtosis": kurt, "skewLimit": SKEW_LIMIT,
                            "kurtosisLimit": KURTOSIS_LIMIT, "kurtosisAlone": KURTOSIS_ALONE,
                            "n": int(x.size), "winsorise": fix}})
    for c, r in zip(crits, influence):
        weight = c["weight"]
        if r is not None and r > DOMINATES:
            gates.append({
                "id": "dominance", "level": "warn", "columns": [c["column"]],
                "message": (f"{c['column']} correlates {r:.2f} with the index, above "
                            f"{DOMINATES}: the index is mostly this one column, whatever the "
                            "other weights say."),
                "numbers": {"correlation": r, "threshold": DOMINATES, "weight": weight}})
        if r is None or abs(r) < BARELY_COUNTS:
            gates.append({
                "id": "barely_counts", "level": "warn", "columns": [c["column"]],
                "message": (f"{c['column']} correlates "
                            f"{'not at all' if r is None else f'{r:.2f}'} with the index, "
                            f"between -{BARELY_COUNTS} and {BARELY_COUNTS}: at "
                            f"{_pct(weight)} of the weight it barely changes the ranking."),
                "numbers": {"correlation": r, "threshold": BARELY_COUNTS, "weight": weight}})
    if population is not None:
        has = ~np.isnan(population)
        rho = _spearman(scores[has].tolist(), population[has].tolist())
        pearson = _pearson(scores[has].tolist(), population[has].tolist())
        if rho is not None and abs(rho) > SIZE_BIAS:
            gates.append({
                "id": "size_bias", "level": "warn", "columns": [population_column],
                "message": (f"The index correlates {rho:.2f} with {population_column} (rank "
                            f"correlation), beyond {SIZE_BIAS}: it partly ranks sites by size. "
                            f"Dividing a criterion by {population_column} would separate the two."),
                "numbers": {"spearman": rho, "pearson": pearson, "threshold": SIZE_BIAS,
                            "n": int(has.sum())}})
    for i in range(len(crits)):
        for j in range(i + 1, len(crits)):
            both = ~np.isnan(values[:, i]) & ~np.isnan(values[:, j])
            rho = _spearman(values[both, i].tolist(), values[both, j].tolist())
            if rho is None or rho <= DOUBLE_WARN:
                continue
            a, b = crits[i]["column"], crits[j]["column"]
            strong = rho > DOUBLE_STRONG
            share = crits[i]["weight"] + crits[j]["weight"]
            gates.append({
                "id": "double_counting", "level": "strong" if strong else "warn",
                "columns": [a, b],
                "message": (f"{a} and {b} move together (rank correlation {rho:.2f}, above "
                            f"{DOUBLE_STRONG if strong else DOUBLE_WARN}), so together their "
                            f"{_pct(share)} of the weight may count the same thing twice."),
                "numbers": {"spearman": rho, "threshold": DOUBLE_STRONG if strong else DOUBLE_WARN,
                            "weightShare": share, "n": int(both.sum())}})
    return gates


# ---------- the slope graph against the readiness score ----------

def comparison(index_result: dict, readiness_scores: Mapping[str, float]) -> dict:
    """The visitor's ranking beside the readiness model's, for the slope graph.

    Both are re-ranked over the sites they share (ties share a rank), so a shift of +5 means the
    visitor's index puts the site 5 places higher than the readiness score does. The two answer
    different questions; this shows where they agree, it does not say which is right.
    """
    sites = index_result.get("sites") or []
    common = []
    for s in sites:
        r = readiness_scores.get(s["siteId"])
        if _is_number(r):
            common.append((s, float(r)))
    index_ids = {s["siteId"] for s in sites}
    out = {"official": False, "name": index_result.get("name"), "badge": BADGE,
           "n": len(common), "spearman": None, "sites": [], "disagreements": [],
           "notInReadiness": [s["siteId"] for s in sites
                              if not _is_number(readiness_scores.get(s["siteId"]))],
           "notInIndex": sorted(str(k) for k in readiness_scores if str(k) not in index_ids)}
    if not common:
        return out
    index_scores = np.array([s["score"] for s, _ in common])
    official = np.array([r for _, r in common])
    index_rank = _competition_ranks(index_scores)
    readiness_rank = _competition_ranks(official)
    out["spearman"] = _spearman(index_scores.tolist(), official.tolist())
    rows = []
    for (s, r), ir, rr in zip(common, index_rank.tolist(), readiness_rank.tolist()):
        rows.append({"siteId": s["siteId"], "name": s.get("name"), "indexRank": ir,
                     "readinessRank": rr, "indexScore": s["score"], "readinessScore": r,
                     "shift": rr - ir})
    out["sites"] = rows
    out["disagreements"] = sorted(rows, key=lambda x: (-abs(x["shift"]), x["indexRank"]))[:10]
    return out


# ---------- the bridge (JSON in, JSON out, as browser_api) ----------

def _loads(text: str, what: str) -> Any:
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        raise ValueError(f"The {what} could not be read.") from None


def frames(table: dict, entries: Any) -> tuple[pd.DataFrame, pd.DataFrame, str | None]:
    """A browser table as (raw, typed, name column), indexed by the dictionary's identifier.

    `raw` keeps every cell as the text the planner typed (as browser_api does); `typed` is
    `read_typed`'s reading. Without an identifier column, sites are called "row 1", "row 2".
    """
    if not isinstance(table, dict) or "columns" not in table or "rows" not in table:
        raise ValueError("The table could not be read.")
    columns = [str(c) for c in table["columns"]]
    if len(set(columns)) != len(columns):
        raise ValueError("Two columns in this file have the same name. Rename one and upload it "
                         "again.")
    width = len(columns)
    rows = [(["" if cell is None else str(cell) for cell in row] + [""] * width)[:width]
            for row in table["rows"]]
    raw = pd.DataFrame(rows, columns=columns, dtype=object)
    by_name = _entries_by_name(entries) or {}

    def role_column(role: str) -> str | None:
        return next((n for n, e in by_name.items()
                     if e.get("evsient:role") == role and n in columns), None)

    id_column, name_column = role_column("identifier"), role_column("name")
    if id_column is not None:
        raw.index = pd.Index([str(v).strip() for v in raw[id_column].tolist()], dtype=object)
    else:
        raw.index = pd.Index([f"row {i}" for i in range(1, len(raw) + 1)], dtype=object)
    return raw, read_typed(raw, list(by_name.values())), name_column


def bridge_validate(spec_json: str, entries_json: str) -> str:
    """validate() for the worker: the spec checked against the confirmed dictionary."""
    spec = _loads(spec_json, "index settings")
    entries = _loads(entries_json, "column dictionary")
    return _out(validate(spec, entries))


def bridge_run(table_json: str, entries_json: str, spec_json: str,
               options_json: str = "{}") -> str:
    """run() for the worker, on the uploaded table and the confirmed dictionary.

    Options: `populationColumn` turns on the size-bias gate; `readinessScores` ({siteId: score},
    from the readiness run) adds the slope-graph `comparison`.
    """
    table = _loads(table_json, "table")
    entries = _loads(entries_json, "column dictionary")
    spec = _loads(spec_json, "index settings")
    options = _loads(options_json or "{}", "options") or {}
    raw, typed, name_column = frames(table, entries)
    result = run(typed, raw, spec, population_column=options.get("populationColumn"),
                 entries=entries, name_column=name_column)
    readiness = options.get("readinessScores")
    if isinstance(readiness, dict) and not result["refused"]:
        result["comparison"] = comparison(result, {str(k): v for k, v in readiness.items()})
    return _out(result)

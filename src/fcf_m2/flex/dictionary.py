"""The column dictionary: what each of a visitor's own columns means, proposed and then confirmed.

What this is for
----------------
Intake asks one question of every column: which of the model's 32 fields is this? On the owner's
360-site test file that found a home for 7 of 31 columns, and the other 24 were carried as text
nobody had read. A map coloured by `flood_risk` then orders its legend High, Low, Moderate,
Unknown. The gap is meaning, not mapping.

This module asks the second question: what is this column? It proposes one entry per column (a
role, a unit, a declared range, the order of its levels, which cells are missing) from four
deterministic signals, shows the evidence for every proposal, and lets the visitor confirm or
correct it. The contract it keeps is section 1 of docs/FLEXIBLE_ANALYSIS.md.

    header grammar   `_kw`, `_m2`, `_usd`, `_pct`, `_0_100`, `_1_5`, `_year`, `_on`, `id`, `name`
    value profiling  distinct count, numeric share, whole numbers, range, closed vocabulary
    scale library    Low < Moderate < High, Poor < Fair < Good < Excellent, Likert 1 to 5 ...
    unit tables      header tokens to UCUM codes, and an ISO 4217 subset for money

No model is involved, and nothing here sends anything anywhere.

The rule that shapes all of it
------------------------------
The same as intake's: **reading must never silently improve the data.** Every cell goes through
one reader, the same one `parse` uses, and the reading report says for every distinct pattern how
it was read and how many cells it covers. So:

* The missing markers are a visible list (`MISSING_MARKERS`), never pandas' defaults. "NA" is
  Namibia's country code and stays a value.
* A sentinel such as -999 is flagged, never applied: it is read as the number it is until the
  visitor marks it missing.
* The decimal mark is decided per column from cells that can only be read one way. A cell such as
  "1.234", which could be read two ways, is counted as ambiguous and is read only when the rest of
  its column settles the question, or, when nothing in its column does, when every column that
  settles it in the file agrees (the evidence says so). Otherwise it is not read at all.
* A value outside a declared range, or a decimal on a whole-number scale, is reported and kept as
  written. Nothing is clamped or rounded.

The one property it never sets
------------------------------
Direction. Words such as "risk" or "potential" suggest one, and the suggestion is shown as
evidence, but `evsient:direction` stays null until the visitor chooses. A silent direction error is
the most damaging mistake in an index someone builds themselves, and no published method infers
direction reliably.
"""

from __future__ import annotations

import copy
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from ..scoring import NUMERIC_FIELDS, YES_NO_FIELDS

#: What a column can be (docs/FLEXIBLE_ANALYSIS.md section 1).
ROLES = ("identifier", "name", "category", "ordinal", "flag", "count", "measure", "score",
         "percentage", "money", "date", "year", "latitude", "longitude", "address", "text",
         "unknown")
DIRECTIONS = ("higher_better", "lower_better", "neither")
PROVENANCE = ("inferred", "confirmed_by_user")
AGREEMENT = ("agree", "conflict", "unknown")

#: The cells read as missing, compared without case or surrounding spaces. A visible list, so a
#: planner can see why a cell was not read; pandas' own list also takes "NA", which is Namibia.
MISSING_MARKERS = ("", "n/a", "N/A", "NULL", "null", "none", "-", "Unknown", "unknown", "TBD",
                   "To be confirmed")
_MISSING = frozenset(m.casefold() for m in MISSING_MARKERS)

#: Numbers that often mean "no data". Flagged in the reading report, never applied: a -999 is
#: read as -999 until the visitor marks it missing.
SENTINELS = (-999.0, -99.0, 9999.0, 99999.0)

#: Distinct patterns listed per column; the rest are counted.
PATTERN_CAP = 50

#: The profile of the Frictionless Table Schema the project file stores (v2, June 2024).
TABLE_SCHEMA_PROFILE = "https://datapackage.org/profiles/2.0/tableschema.json"
DICTIONARY_VERSION = 1

_NUMERIC = frozenset({"count", "measure", "score", "percentage", "money", "year", "latitude",
                      "longitude"})
_CATEGORICAL = frozenset({"category", "ordinal", "flag"})
#: Roles for which "higher is better" can mean something.
_DIRECTIONAL = frozenset({"ordinal", "flag", "count", "measure", "score", "percentage", "money",
                          "year", "date"})
_UNIT_ROLES = frozenset({"measure", "money", "percentage", "count"})
_RANGE_ROLES = frozenset({"score", "percentage", "ordinal"})

#: Every entry has exactly these keys, in this order. The four standard Frictionless keys that do
#: not apply to a role are null here and left out of the Table Schema.
_ENTRY_KEYS = ("name", "type", "format", "categories", "categoriesOrdered", "missingValues",
               "decimalChar", "evsient:role", "evsient:unit", "evsient:range",
               "evsient:direction", "evsient:modelField", "evsient:evidence", "evsient:agreement",
               "evsient:provenance", "evsient:reading")
_OPTIONAL_STANDARD = ("format", "categories", "categoriesOrdered", "decimalChar")

_TYPE_FOR_ROLE = {
    "count": "integer", "measure": "number", "score": "number", "percentage": "number",
    "money": "number", "latitude": "number", "longitude": "number", "year": "year",
    "date": "date", "unknown": "any",
}

# ---------- the libraries ----------

#: Header tokens that name a unit: the UCUM code and the words shown to the visitor. Single
#: letters are limited to the three intake already reads (`_m`, `_h`, `_w`), because `_a` or `_s`
#: is far more often a label than amperes or seconds.
UNITS: dict[str, tuple[str, str]] = {
    "w": ("W", "watts"), "kw": ("kW", "kilowatts"), "mw": ("MW", "megawatts"),
    "wh": ("W.h", "watt hours"), "kwh": ("kW.h", "kilowatt hours"),
    "mwh": ("MW.h", "megawatt hours"), "kva": ("kV.A", "kilovolt amperes"),
    "volts": ("V", "volts"), "amp": ("A", "amperes"), "amps": ("A", "amperes"),
    "m": ("m", "metres"), "metres": ("m", "metres"), "meters": ("m", "metres"),
    "km": ("km", "kilometres"), "cm": ("cm", "centimetres"), "mm": ("mm", "millimetres"),
    "ft": ("[ft_i]", "feet"), "feet": ("[ft_i]", "feet"), "mi": ("[mi_i]", "miles"),
    "miles": ("[mi_i]", "miles"),
    "m2": ("m2", "square metres"), "sqm": ("m2", "square metres"),
    "km2": ("km2", "square kilometres"), "ft2": ("[sft_i]", "square feet"),
    "sqft": ("[sft_i]", "square feet"), "ha": ("har", "hectares"),
    "hectares": ("har", "hectares"), "acres": ("[acr_us]", "acres"),
    "sec": ("s", "seconds"), "secs": ("s", "seconds"), "seconds": ("s", "seconds"),
    "min": ("min", "minutes"), "mins": ("min", "minutes"), "minutes": ("min", "minutes"),
    "h": ("h", "hours"), "hr": ("h", "hours"), "hrs": ("h", "hours"), "hours": ("h", "hours"),
    "days": ("d", "days"), "weeks": ("wk", "weeks"), "years": ("a", "years"),
    "yrs": ("a", "years"),
    "kg": ("kg", "kilograms"), "tonnes": ("t", "tonnes"),
    "litres": ("L", "litres"), "liters": ("L", "litres"), "m3": ("m3", "cubic metres"),
    "degc": ("Cel", "degrees Celsius"), "celsius": ("Cel", "degrees Celsius"),
    "kmh": ("km/h", "kilometres per hour"), "kph": ("km/h", "kilometres per hour"),
    "mph": ("[mi_i]/h", "miles per hour"),
    "kgco2e": ("kg{CO2e}", "kilograms of CO2 equivalent"),
    "tco2e": ("t{CO2e}", "tonnes of CO2 equivalent"),
}
#: Units written as two tokens.
UNIT_PAIRS: dict[tuple[str, str], tuple[str, str]] = {
    ("sq", "m"): ("m2", "square metres"), ("sq", "km"): ("km2", "square kilometres"),
    ("sq", "ft"): ("[sft_i]", "square feet"),
}

#: An ISO 4217 subset: the currencies of the regions the platform has seen, and the major ones.
#: Codes that are also common English words (ALL, TOP, TRY, CUP, MAD, PHP) are left out on
#: purpose, because a header ending `_all` is not in Albanian lek.
CURRENCIES: dict[str, str] = {
    "USD": "US dollars", "EUR": "euros", "GBP": "pounds sterling", "CAD": "Canadian dollars",
    "AUD": "Australian dollars", "NZD": "New Zealand dollars", "JPY": "yen", "CNY": "yuan",
    "INR": "Indian rupees", "BRL": "Brazilian reais", "MXN": "Mexican pesos",
    "ZAR": "South African rand", "NGN": "naira", "GHS": "Ghanaian cedis",
    "KES": "Kenyan shillings", "RWF": "Rwandan francs", "UGX": "Ugandan shillings",
    "TZS": "Tanzanian shillings", "ETB": "birr", "XOF": "West African CFA francs",
    "XAF": "Central African CFA francs", "EGP": "Egyptian pounds", "CHF": "Swiss francs",
    "SEK": "Swedish kronor", "NOK": "Norwegian kroner", "DKK": "Danish kroner",
    "PLN": "zloty", "KRW": "won", "SGD": "Singapore dollars", "HKD": "Hong Kong dollars",
    "IDR": "rupiah", "COP": "Colombian pesos", "CLP": "Chilean pesos", "PEN": "soles",
    "ARS": "Argentine pesos",
}
#: Signs in a cell that name one currency. "$" names several and so names none.
_SYMBOL_CODES = {"US$": "USD", "CA$": "CAD", "R$": "BRL", "KSh": "KES", "€": "EUR", "£": "GBP",
                 "₹": "INR", "₦": "NGN", "₵": "GHS"}
_PREFIXES = ("US$", "CA$", "R$", "KSh", "$", "€", "£", "¥", "₹", "₦", "₵")
_SUFFIXES = ("%", "€", "FCFA", "CFA")

#: Known ordered scales, lowest first. Each level is the spellings that mean it.
SCALES: dict[str, list[tuple[str, ...]]] = {
    "level": [("very low",), ("low",), ("moderate", "medium"), ("high",), ("very high",)],
    "quality": [("very poor",), ("poor",), ("fair",), ("good",), ("very good",), ("excellent",)],
    "frequency": [("never",), ("rarely",), ("sometimes",), ("often",), ("always",)],
    "agreement": [("strongly disagree",), ("disagree",), ("neither agree nor disagree", "neutral"),
                  ("agree",), ("strongly agree",)],
}
#: Declared ranges read as a Likert scale of whole-number levels rather than a bounded score.
LIKERT = ((1, 5), (1, 7))

#: The same yes and no words the model's scoring reads.
YES = frozenset({"1", "1.0", "y", "yes", "true", "t"})
NO = frozenset({"0", "0.0", "n", "no", "false", "f"})

#: Header words and what they suggest. Compared after a plural "s" is dropped.
_LAT = frozenset({"lat", "latitude"})
_LON = frozenset({"lon", "lng", "longitude"})
_ID_SUFFIX = frozenset({"id", "uuid", "guid", "code", "ref", "key", "identifier"})
_NAME_SUFFIX = frozenset({"name", "title", "label"})
_TEXT_WORDS = frozenset({"note", "notes", "comment", "comments", "description", "desc",
                         "remark", "remarks", "details", "observation", "observations",
                         "summary", "narrative"})
_ADDRESS_WORDS = frozenset({"address", "addr", "street", "postcode", "zipcode", "zip", "postal"})
_DATE_SUFFIX = frozenset({"on", "date", "dated"})
_DATE_WORDS = frozenset({"date", "datetime", "timestamp"})
_YEAR_WORDS = frozenset({"year", "yr"})
_PCT_SUFFIX = frozenset({"pct", "percent", "percentage", "perc"})
_SHARE_WORDS = frozenset({"share", "fraction", "proportion"})
_MONEY_WORDS = frozenset({"cost", "price", "budget", "spend", "spending", "revenue", "fee",
                          "funding", "grant", "dollar", "salary", "rent", "income"})
_EURO_WORDS = frozenset({"euro", "euros"})
_COUNT_WORDS = frozenset({"population", "visit", "visitor", "count", "household", "job",
                          "employee", "staff", "resident", "people", "person", "space", "stall",
                          "port", "vehicle", "trip", "session", "user", "member", "student", "bed",
                          "volunteer", "num", "qty", "quantity", "worker", "patient", "customer",
                          "passenger", "charger"})
_FLAG_PREFIX = frozenset({"is", "has", "can", "allows", "does", "needs"})
_FLAG_SUFFIX = frozenset({"flag", "ok", "yn", "bool"})
_CATEGORY_WORDS = frozenset({"type", "category", "class", "kind", "group", "status", "country",
                             "city", "region", "state", "province", "district", "county", "zone",
                             "sector", "neighborhood", "neighbourhood", "ward", "municipality",
                             "borough", "tier", "segment"})
_SCALE_WORDS = frozenset({"risk", "level", "rating", "grade", "priority", "quality", "condition",
                          "severity", "frequency", "score", "index", "likelihood",
                          "vulnerability", "exposure", "suitability"})

#: Words that suggest a direction. The research's inference, not a benchmarked result, which is
#: why each only ever reaches the evidence as a proposal for the visitor to confirm.
LOWER_BETTER_WORDS = ("risk", "cost", "distance", "time", "wait", "price")
HIGHER_BETTER_WORDS = ("potential", "capacity", "access", "accessibility", "population", "visit",
                       "priority", "area")

_DIRECTION_WORDS = {"higher_better": "higher is better", "lower_better": "lower is better",
                    "neither": "neither"}


# ---------- small helpers ----------

def _text(cell: Any) -> str:
    """A cell as the text it was written as. Empty for None or a float NaN a caller's own reader
    produced; the dictionary itself reads with every cell kept as text."""
    if cell is None or cell is pd.NA or cell is pd.NaT:
        return ""
    if isinstance(cell, str):
        return cell
    if isinstance(cell, float) and math.isnan(cell):
        return ""
    if isinstance(cell, np.generic):
        return _text(cell.item())
    return str(cell)


def _is_marker(raw: str) -> bool:
    return raw.strip().casefold() in _MISSING


def _num(value: float) -> int | float:
    """A number for JSON and for sentences: whole numbers without a trailing ".0"."""
    return int(value) if float(value).is_integer() and abs(value) < 2 ** 53 else float(value)


def _say(value: float) -> str:
    return repr(_num(value))


def _singular(token: str) -> str:
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def _evidence(signal: str, match: str, text: str, **more: Any) -> dict:
    return {"signal": signal, "match": match, "text": text, **more}


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _count(n: int, one: str, many: str) -> str:
    """"1 value lies", "2 values lie": a count with the words that agree with it."""
    return f"{n} {one if n == 1 else many}"


# ---------- header grammar ----------

@dataclass
class _Header:
    """What a column's name says, with the token each statement came from."""

    role: str | None = None
    unit: str | None = None
    range: list | None = None
    likert: bool = False
    scale: bool = False            # a word such as "risk" or "level" suggests levels
    evidence: list[dict] = field(default_factory=list)
    directions: list[dict] = field(default_factory=list)


def _tokens(header: str) -> list[str]:
    text = str(header).replace("²", "2").replace("³", "3").replace("%", "_pct_")
    if not re.search(r"[_\s\-.]", text):
        # camelCase only where there is no other separator: `solarRoofKw`, not `battery_kWh`.
        text = re.sub(r"([a-z])([A-Z][a-z])", r"\1_\2", text)
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def _read_header(name: str) -> _Header:
    """Suffix grammar first (a declared range, a unit, a currency, `_year`, `_on`, `_id`,
    `_name`), then words anywhere in the name. The first statement that applies sets the role."""
    head = _Header()
    tokens = _tokens(name)
    words = set(tokens) | {_singular(t) for t in tokens}
    ev = head.evidence

    def say(role: str, match: str, text: str) -> None:
        if head.role is None:
            head.role = role
            ev.append(_evidence("header", match, text))

    if words & _LAT:
        token = next(t for t in tokens if t in _LAT)
        say("latitude", token, f"the header word '{token}' names a latitude")
    elif words & _LON or tokens == ["long"]:
        token = next((t for t in tokens if t in _LON), "long")
        say("longitude", token, f"the header word '{token}' names a longitude")

    body = list(tokens)
    if len(body) >= 3 and body[-1].isdigit() and body[-2].isdigit() and int(body[-2]) < int(body[-1]):
        lo, hi = int(body[-2]), int(body[-1])
        head.range = [lo, hi]
        head.likert = (lo, hi) in LIKERT
        suffix = f"_{body[-2]}_{body[-1]}"
        say("score", suffix, f"the header ends in '{suffix}', which declares a range of {lo} to {hi}")
        body = body[:-2]

    rate = len(body) >= 2 and body[-2] == "per"
    last = body[-1] if body else ""
    if rate and head.role is None:
        ev.append(_evidence("header", f"per_{last}",
                            f"the header ends in 'per {last}', a rate; its unit is not recorded "
                            f"from the header"))
    elif head.role is None and last in _PCT_SUFFIX:
        head.unit, head.range = "%", [0, 100]
        say("percentage", f"_{last}", f"the header ends in '_{last}', a percentage from 0 to 100")
    elif head.role is None and last.upper() in CURRENCIES and len(body) > 1:
        head.unit = last.upper()
        say("money", f"_{last}",
            f"the header ends in '_{last}', the ISO 4217 code for {CURRENCIES[head.unit]}")
    elif head.role is None and len(body) > 1 and (tuple(body[-2:]) in UNIT_PAIRS or last in UNITS):
        pair = tuple(body[-2:]) in UNIT_PAIRS
        code, words_for = UNIT_PAIRS[tuple(body[-2:])] if pair else UNITS[last]
        token = "_".join(body[-2:]) if pair else last
        head.unit = code
        say("measure", f"_{token}", f"the header ends in '_{token}', the unit code for "
                                    f"{words_for} ({code})")

    if head.role is None and last in _YEAR_WORDS and len(body) > 1:
        say("year", f"_{last}", f"the header ends in '_{last}', a calendar year")
    if head.role is None and last in _DATE_SUFFIX and len(body) > 1:
        say("date", f"_{last}", f"the header ends in '_{last}', a date")
    if head.role is None and words & _ADDRESS_WORDS:
        token = next(t for t in tokens if t in _ADDRESS_WORDS)
        say("address", token, f"the header word '{token}' names an address")
    category_word = next((t for t in tokens if _singular(t) in _CATEGORY_WORDS or t in _CATEGORY_WORDS), None)
    if head.role is None and last in _ID_SUFFIX and not (last == "code" and category_word):
        say("identifier", last, f"the header word '{last}' names an identifier")
    if head.role is None and last in _NAME_SUFFIX:
        say("name", last, f"the header word '{last}' names a name")
    if head.role is None and words & _TEXT_WORDS:
        token = next(t for t in tokens if t in _TEXT_WORDS)
        say("text", token, f"the header word '{token}' names free text")
    if head.role is None and words & _DATE_WORDS:
        token = next(t for t in tokens if t in _DATE_WORDS)
        say("date", token, f"the header word '{token}' names a date")
    if head.role is None and set(tokens) & _YEAR_WORDS:      # "years" is a duration, not a year
        token = next(t for t in tokens if t in _YEAR_WORDS)
        say("year", token, f"the header word '{token}' names a calendar year")
    if head.role is None and words & _EURO_WORDS:
        token = next(t for t in tokens if t in _EURO_WORDS)
        head.unit = "EUR"
        say("money", token, f"the header word '{token}' names an amount in euros (EUR)")
    if head.role is None and words & _SHARE_WORDS:
        token = next(t for t in tokens if _singular(t) in _SHARE_WORDS or t in _SHARE_WORDS)
        head.unit, head.range = "1", [0, 1]
        say("percentage", token, f"the header word '{token}' names a share from 0 to 1")
    if head.role is None and (words & _MONEY_WORDS):
        token = next(t for t in tokens if t in _MONEY_WORDS or _singular(t) in _MONEY_WORDS)
        say("money", token, f"the header word '{token}' names an amount of money, but no "
                            f"currency is named")
    if head.role is None and (words & _COUNT_WORDS):
        token = next(t for t in tokens if t in _COUNT_WORDS or _singular(t) in _COUNT_WORDS)
        say("count", token, f"the header word '{token}' names something counted")
    if head.role is None and ((tokens and tokens[0] in _FLAG_PREFIX and len(tokens) > 1)
                              or last in _FLAG_SUFFIX):
        token = tokens[0] if tokens[0] in _FLAG_PREFIX else last
        say("flag", token, f"the header word '{token}' names a yes or no question")
    if head.role is None and category_word:
        say("category", category_word, f"the header word '{category_word}' names a grouping")
    if words & _SCALE_WORDS:
        token = next(t for t in tokens if t in _SCALE_WORDS or _singular(t) in _SCALE_WORDS)
        head.scale = True
        if head.role is None:
            ev.append(_evidence("header", token, f"the header word '{token}' suggests a scale "
                                                 f"of levels"))

    for direction, vocabulary in (("lower_better", LOWER_BETTER_WORDS),
                                  ("higher_better", HIGHER_BETTER_WORDS)):
        for token in tokens:
            if token in vocabulary or _singular(token) in vocabulary:
                head.directions.append(_evidence(
                    "direction", token,
                    f"the word '{token}' in the header suggests {_DIRECTION_WORDS[direction]}; "
                    f"a proposal only, until you confirm a direction",
                    direction=direction))
                break
    return head


# ---------- reading one cell ----------

_INT = re.compile(r"\d+")
_SCI = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)[eE][-+]?\d+")
_GROUPED = re.compile(r"[1-9]\d{0,2}(?P<g>[,.' \u00a0\u202f])\d{3}(?:(?P=g)\d{3})*"
                      r"(?:(?P<d>[.,])\d+)?")
_DEC = re.compile(r"\d*(?P<d>[.,])\d+")
_ISO_DATE = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})"
                       r"(?P<time>[T ]\d{1,2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?")
_SLASH_DATE = re.compile(r"(\d{1,2})([/.])(\d{1,2})\2(\d{4})")

_GROUP_NAMES = {",": "','", ".": "'.'", "'": "an apostrophe", " ": "a space",
                "\u00a0": "a space", "\u202f": "a space"}


def _affixes(raw: str) -> tuple[str, str, str, str]:
    """(sign, currency prefix, the digits, suffix) of a cell written as a number."""
    t = raw.strip().replace("\u2212", "-")
    sign = ""
    if t[:1] in ("-", "+"):
        sign, t = t[0], t[1:].lstrip()
    prefix = next((p for p in _PREFIXES if t.startswith(p)), "")
    if not prefix:
        m = re.match(r"([A-Z]{3})\s*(?=[\d.,])", t)
        if m and m.group(1) in CURRENCIES:
            prefix = m.group(1)
    if prefix:
        t = t[len(prefix):].lstrip()
    if not sign and t[:1] in ("-", "+"):
        sign, t = t[0], t[1:]
    suffix = next((s for s in _SUFFIXES if t.endswith(s)), "")
    if not suffix:
        m = re.search(r"(?<=[\d\s])([A-Z]{3})$", t)
        if m and m.group(1) in CURRENCIES:
            suffix = m.group(1)
    if suffix:
        t = t[:-len(suffix)].rstrip()
    return sign, prefix, t, suffix


def _classify(core: str) -> tuple[str, str | None, str | None, float | None, float | None]:
    """How the digits of a cell can be read: (form, decimal mark it proves, group mark, value,
    value if the group mark were a decimal mark). The second value exists only for a cell that
    could be read two ways."""
    if _INT.fullmatch(core):
        return "int", None, None, float(core), None
    if _SCI.fullmatch(core):
        return "sci", ("." if "." in core else None), None, float(core), None
    m = _GROUPED.fullmatch(core)
    if m:
        g, d = m.group("g"), m.group("d")
        if d:
            if d == g:
                return "bad", None, None, None, None
            return "grouped", d, g, float(core.replace(g, "").replace(d, ".")), None
        if g in ".,":
            if core.count(g) >= 2:
                return "grouped", ("," if g == "." else "."), g, float(core.replace(g, "")), None
            return "ambiguous", g, g, float(core.replace(g, "")), float(core.replace(g, "."))
        return "grouped", None, g, float(core.replace(g, "")), None
    m = _DEC.fullmatch(core)
    if m:
        d = m.group("d")
        return "decimal", d, None, float(core.replace(d, ".")), None
    return "bad", None, None, None, None


@dataclass
class _Number:
    value: float | None
    state: str                 # value | ambiguous | unreadable | conflict
    form: str
    proves: str | None         # the decimal mark the cell proves on its own, if any
    group: str | None
    prefix: str
    suffix: str
    ambiguous: bool
    core: str


def _number(raw: str, mark: str | None) -> _Number:
    """One cell as a number, given the column's decimal mark (None when undecided)."""
    sign, prefix, core, suffix = _affixes(raw)
    form, proves, group, plain, as_decimal = _classify(core)
    out = _Number(None, "unreadable", form, proves, group, prefix, suffix, form == "ambiguous", core)
    if form == "bad":
        return out
    if form == "ambiguous":
        if mark is None:
            out.state = "ambiguous"
            return out
        value = as_decimal if mark == proves else plain
    elif proves is not None and mark is not None and proves != mark:
        out.state = "conflict"
        return out
    else:
        value = plain
    if not math.isfinite(value):
        return out
    out.value, out.state = (-value if sign == "-" else value), "value"
    if out.value == 0:
        out.value = 0.0
    return out


def _number_note(n: _Number, mark: str | None) -> str:
    if n.form == "ambiguous":
        note = (f"a number, read with this column's decimal mark '{mark}'"
                + (f", so {_GROUP_NAMES[n.group]} separates thousands" if mark != n.group else ""))
    elif n.form == "sci":
        note = "a number in scientific notation"
    elif n.form == "decimal":
        note = f"a number with '{n.proves}' as the decimal mark"
    elif n.form == "grouped":
        note = f"a number; {_GROUP_NAMES[n.group]} separates thousands"
        if n.proves and n.proves in n.core:
            note += f" and '{n.proves}' marks decimals"
    else:
        note = "a number"
    for affix in (n.prefix, n.suffix):
        if affix:
            note += f"; the '{affix}' {'code' if affix in CURRENCIES else 'sign'} is set aside"
    return note


def _shape(raw: str) -> str:
    return re.sub(r"\d", "9", raw)


def _date(raw: str, order: str | None) -> tuple[str | None, str, str | None, bool, str]:
    """One cell as a date: (ISO date, state, the day/month order it proves, whether a time of day
    was set aside, form). `order` is the column's "dmy" or "mdy", or None when undecided."""
    t = raw.strip()
    m = _ISO_DATE.fullmatch(t)
    if m:
        try:
            iso = date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            return None, "unreadable", None, False, "iso"
        return iso, "value", None, bool(m.group("time")), "iso"
    m = _SLASH_DATE.fullmatch(t)
    if not m:
        return None, "unreadable", None, False, "bad"
    a, b, year = int(m.group(1)), int(m.group(3)), int(m.group(4))
    if a > 12 and b > 12:
        return None, "unreadable", None, False, "slash"
    proves = "dmy" if a > 12 else "mdy" if b > 12 else None
    if proves is None and a != b and order is None:
        return None, "ambiguous", None, False, "slash"
    if proves is not None and order is not None and proves != order:
        return None, "conflict", proves, False, "slash"
    use = proves or order or "dmy"          # a == b reads the same either way
    day, month = (a, b) if use == "dmy" else (b, a)
    try:
        return date(year, month, day).isoformat(), "value", proves, False, "slash"
    except ValueError:
        return None, "unreadable", proves, False, "slash"


_FORMAT_FOR_ORDER = {"dmy": "%d/%m/%Y", "mdy": "%m/%d/%Y"}
_ORDER_FOR_FORMAT = {v: k for k, v in _FORMAT_FOR_ORDER.items()}
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y")


# ---------- value profiling ----------

@dataclass
class _Profile:
    cells: int
    filled: list[str]
    counts: Counter
    missing: list[str]
    numeric_share: float = 0.0
    mark: str | None = None
    mark_from_file: bool = False
    marks_seen: tuple = ()
    ambiguous_example: str | None = None
    ambiguous_cells: int = 0
    proof_example: str | None = None
    proof_cells: int = 0
    numbers: list[float] = field(default_factory=list)   # read values, sentinels left out
    sentinel_cells: int = 0
    date_share: float = 0.0
    date_order: str | None = None
    date_example: str | None = None
    date_iso_only: bool = False
    yes_forms: list[str] = field(default_factory=list)
    no_forms: list[str] = field(default_factory=list)
    extras: list[str] = field(default_factory=list)
    is_flag: bool = False
    scale: str | None = None
    scale_levels: list[str] = field(default_factory=list)
    scale_doubled: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)


def _by_count(counts: Counter) -> list[str]:
    return sorted(counts, key=lambda v: (-counts[v], v))


def _profile(cells: list[str], file_mark: str | None = None) -> _Profile:
    filled = [c for c in cells if not _is_marker(c)]
    counts = Counter(filled)
    missing = _by_count(Counter(c for c in cells if _is_marker(c)))
    p = _Profile(len(cells), filled, counts, missing)
    if not filled:
        return p

    # Numbers: the decimal mark first, from the cells that prove one.
    parsed = {raw: _number(raw, None) for raw in counts}
    proofs = Counter()
    for raw, n in parsed.items():
        if n.form != "bad" and n.form != "ambiguous" and n.proves:
            proofs[n.proves] += counts[raw]
            p.proof_example = p.proof_example or raw
    p.marks_seen = tuple(sorted(proofs))
    p.mark = p.marks_seen[0] if len(p.marks_seen) == 1 else None
    if not p.marks_seen and file_mark:
        p.mark, p.mark_from_file = file_mark, True
    p.proof_cells = sum(proofs.values())
    numeric = 0
    symbols = Counter()
    for raw in _by_count(counts):
        n = _number(raw, p.mark)
        if n.form == "bad":
            continue
        numeric += counts[raw]
        if n.ambiguous:
            p.ambiguous_cells += counts[raw]
            p.ambiguous_example = p.ambiguous_example or raw
        for affix in (n.prefix, n.suffix):
            if affix:
                symbols[affix] += counts[raw]
        if n.state == "value":
            if n.value in SENTINELS:
                p.sentinel_cells += counts[raw]
            else:
                p.numbers.extend([n.value] * counts[raw])
    p.numeric_share = numeric / len(filled)
    p.symbols = _by_count(symbols)

    # Dates: the day/month order from the cells that prove one.
    orders, dated, slash = Counter(), 0, 0
    for raw in counts:
        _, state, proves, _, form = _date(raw, None)
        if state in ("value", "ambiguous"):
            dated += counts[raw]
            slash += counts[raw] if form == "slash" else 0
            if proves:
                orders[proves] += counts[raw]
                p.date_example = p.date_example or raw
    p.date_share = dated / len(filled)
    p.date_order = next(iter(orders)) if len(orders) == 1 else None
    p.date_iso_only = slash == 0

    # Yes and no, with at most three other states that are not numbers and not most of the cells.
    folded = {raw: raw.strip().casefold() for raw in counts}
    p.yes_forms = [r for r in _by_count(counts) if folded[r] in YES]
    p.no_forms = [r for r in _by_count(counts) if folded[r] in NO]
    p.extras = [r for r in _by_count(counts) if folded[r] not in YES and folded[r] not in NO]
    extra_cells = sum(counts[r] for r in p.extras)
    p.is_flag = (bool(p.yes_forms) and bool(p.no_forms) and len(p.extras) <= 3
                 and extra_cells * 2 < len(filled)
                 and not any(_number(r, None).form != "bad" for r in p.extras))

    # A known scale: every filled value is a level of one scale, and two or more levels appear.
    for scale, levels in SCALES.items():
        position = {spelling: i for i, level in enumerate(levels) for spelling in level}
        if all(folded[r] in position for r in counts):
            used = Counter(position[folded[r]] for r in counts)
            if len(used) >= 2:
                p.scale = scale
                p.scale_levels = sorted(counts, key=lambda r: (position[folded[r]], -counts[r], r))
                p.scale_doubled = sorted(r for r in counts if used[position[folded[r]]] > 1)
                break
    return p


def _text_shape(p: _Profile) -> str:
    """identifier, text, category or name, for a column whose values are not numbers."""
    values = list(p.counts)
    words = sorted(len(v.split()) for v in p.filled)
    median_words = words[len(words) // 2]
    sentences = sum(p.counts[v] for v in values if v.strip().endswith((".", "!", "?")))
    if median_words >= 8 or (median_words >= 4 and sentences * 2 >= len(p.filled)):
        return "text"
    if len(values) == len(p.filled) and len(values) >= 2 and not any(" " in v.strip() for v in values):
        return "identifier"
    if len(values) <= 100 and len(values) * 2 <= len(p.filled):
        return "category"
    return "name"


def _numbers_fact(p: _Profile) -> tuple[str, str]:
    """(short match, sentence) for how many filled cells are numbers, and their spread."""
    numeric = round(p.numeric_share * len(p.filled))
    match = f"{numeric}/{len(p.filled)} numbers"
    text = f"{numeric} of {len(p.filled)} filled cells are numbers"
    if p.numbers:
        whole = all(v.is_integer() for v in p.numbers)
        spread = f"{_say(min(p.numbers))} to {_say(max(p.numbers))}"
        match += (", whole" if whole else "") + f", {spread}"
        text += (", all whole" if whole else "") + f", from {spread}"
    if p.sentinel_cells:
        text += (f", leaving aside {_count(p.sentinel_cells, 'cell that holds', 'cells that hold')} "
                 f"a common no-data code")
    return match, text


def _value_role(p: _Profile, scale_word: bool) -> tuple[str | None, list[dict]]:
    """The role the values alone suggest, with the fact that suggests it."""
    n = len(p.filled)
    if not n:
        return None, [_evidence("values", "no values", "every cell is empty or a missing marker")]
    if p.date_share == 1:
        return "date", [_evidence("values", f"{n} of {n} dates",
                                  f"all {n} filled cells are dates")]
    if p.is_flag:
        extras = ", ".join(f"'{e}'" for e in p.extras)
        text = (f"values are yes or no" + (f", with the other state(s) {extras}" if extras else ""))
        return "flag", [_evidence("values", " / ".join(p.yes_forms[:1] + p.no_forms[:1] + p.extras), text)]
    if p.scale:
        order = " < ".join(p.scale_levels)
        return "ordinal", [_evidence("scale", order, f"values match the scale {order}")]
    if p.numeric_share >= 0.9:
        whole = bool(p.numbers) and all(v.is_integer() for v in p.numbers)
        nonneg = bool(p.numbers) and min(p.numbers) >= 0
        ev = [_evidence("values", *_numbers_fact(p))]
        if scale_word:
            return "score", ev
        if whole and nonneg:
            low, high = min(p.numbers), max(p.numbers)
            for lo, hi in LIKERT:
                if low >= lo and high <= hi and len(set(p.numbers)) <= hi:
                    ev.append(_evidence("values", f"whole numbers {lo} to {hi}",
                                        f"whole numbers within {lo} to {hi} only: this may be a "
                                        f"{lo} to {hi} scale rather than a count"))
                    break
            return "count", ev
        ev.append(_evidence("values", "no unit", "the header names no unit for these numbers"))
        return "measure", ev
    if p.numeric_share >= 0.5:
        match, text = _numbers_fact(p)
        return "unknown", [_evidence("values", match, f"{text}; the rest are not")]
    shape = _text_shape(p)
    k = len(p.counts)
    facts = {
        "text": (f"{k} distinct", "values are sentences or long phrases"),
        "identifier": (f"{k} of {n} distinct", f"all {n} filled values are different and none "
                                               f"has a space"),
        "category": (f"{k} distinct in {n}",
                     "every filled cell holds the same value" if k == 1 else
                     f"{k} distinct values repeat across {n} filled cells, a closed list"),
        "name": (f"{k} distinct in {n}", f"{k} distinct values in {n} filled cells rarely repeat"),
    }
    match, text = facts[shape]
    return shape, [_evidence("values", match, text)]


# ---------- deciding ----------

@dataclass
class _Decision:
    role: str = "unknown"
    agreement: str = "unknown"
    unit: str | None = None
    range: list | None = None
    categories: list | None = None
    evidence: list[dict] = field(default_factory=list)


def _decide(head: _Header, p: _Profile) -> _Decision:
    d = _Decision(evidence=list(head.evidence))
    ev = d.evidence
    vrole, vev = _value_role(p, head.scale)
    h = head.role
    n = len(p.filled)

    if h in _NUMERIC:
        d.unit, d.range = head.unit, head.range
        if not n:
            d.role = "ordinal" if head.likert else h
            if head.likert:
                d.categories = list(range(head.range[0], head.range[1] + 1))
            ev.extend(vev)
            return d
        if p.numeric_share < 0.5:
            d.role, d.agreement, d.unit, d.range = "unknown", "conflict", None, None
            ev.extend(vev)
            match, text = _numbers_fact(p)
            ev.append(_evidence("values", match, f"the header suggests numbers, but {text}"))
            return d
        ev.append(_evidence("values", *_numbers_fact(p)))
        d.role, d.agreement = h, "agree"
        if p.numeric_share < 0.9:
            d.agreement = "conflict"
        nums = p.numbers
        if h == "score" and head.range:
            lo, hi = head.range
            outside = [v for v in nums if not lo <= v <= hi]
            decimals = [v for v in nums if not v.is_integer()]
            if head.likert and not outside and not decimals:
                d.role = "ordinal"
                d.categories = list(range(lo, hi + 1))
                ev.append(_evidence("scale", f"{lo} to {hi}", f"whole numbers within {lo} to {hi}, "
                                                             f"a {lo} to {hi} scale of levels"))
            elif outside or (head.likert and decimals):
                d.agreement = "conflict"
                if outside:
                    lie = _count(len(outside), "value lies", "values lie")
                    ev.append(_evidence("values", f"{len(outside)} outside {lo} to {hi}",
                                        f"{lie} outside the declared range {lo} to {hi}; kept as "
                                        f"written, not clamped"))
                if head.likert and decimals:
                    are = _count(len(decimals), "value is a decimal", "values are decimals")
                    ev.append(_evidence("values", f"{len(decimals)} decimals",
                                        f"{are} on a whole-number scale; kept as written, not "
                                        f"rounded"))
            elif nums:
                ev.append(_evidence("range", f"{lo} to {hi}", f"every value lies inside the declared "
                                                              f"range {lo} to {hi}"
                                    + (", apart from possible no-data codes" if p.sentinel_cells else "")))
        elif h == "percentage":
            lo, hi = head.range
            outside = [v for v in nums if not lo <= v <= hi]
            if outside:
                d.agreement = "conflict"
                lie = _count(len(outside), "value lies", "values lie")
                ev.append(_evidence("values", f"{len(outside)} outside {lo} to {hi}",
                                    f"{lie} outside {lo} to {hi}"))
        elif h in ("latitude", "longitude"):
            bound = 90 if h == "latitude" else 180
            outside = [v for v in nums if abs(v) > bound]
            if outside:
                d.agreement = "conflict"
                ev.append(_evidence("values", f"{len(outside)} outside -{bound} to {bound}",
                                    f"{_count(len(outside), 'value lies', 'values lie')} outside -{bound} to "
                                    f"{bound}, so this may be a projected coordinate"))
        elif h == "year":
            odd = [v for v in nums if not (v.is_integer() and 1800 <= v <= 2200)]
            if odd:
                d.agreement = "conflict"
                ev.append(_evidence("values", f"{len(odd)} not years",
                                    f"{_count(len(odd), 'value is', 'values are')} not whole years from 1800 "
                                    f"to 2200"))
        elif h == "count":
            odd = [v for v in nums if not v.is_integer() or v < 0]
            if odd:
                d.agreement = "conflict"
                ev.append(_evidence("values", f"{len(odd)} not counts",
                                    f"{_count(len(odd), 'value is', 'values are')} not whole numbers of 0 or "
                                    f"more"))
        return d

    if h == "date":
        if n and p.date_share < 0.5:
            d.role, d.agreement = "unknown", "conflict"
            ev.extend(vev)
            ev.append(_evidence("values", f"{round(p.date_share * n)} of {n} dates",
                                f"the header suggests dates, but only {round(p.date_share * n)} of "
                                f"{n} filled cells are dates"))
            return d
        d.role, d.agreement = "date", ("agree" if n else "unknown")
        if n:
            ev.append(_evidence("values", f"{round(p.date_share * n)} of {n} dates",
                                f"{round(p.date_share * n)} of {n} filled cells are dates"))
            if p.date_share < 0.9:
                d.agreement = "conflict"
        return d

    if h == "flag":
        if n and not p.is_flag:
            d.role, d.agreement = "unknown", "conflict"
            ev.extend(vev)
            ev.append(_evidence("values", "not yes or no", "the header suggests yes or no, but "
                                                           "the values are not"))
            return d
        d.role, d.agreement = "flag", ("agree" if n else "unknown")
        ev.extend(vev)
        return d

    if h in ("identifier", "name", "text", "address"):
        d.role = h
        if h != "identifier" or not n:
            ev.extend(vev)
        if not n:
            return d
        if h == "identifier":
            repeated = sum(c - 1 for c in p.counts.values() if c > 1)
            if repeated or p.missing:
                d.agreement = "conflict"
                if repeated:
                    repeat = _count(repeated, "value repeats", "values repeat")
                    ev.append(_evidence("values", f"{repeated} repeats",
                                        f"{repeat} an earlier one, so this does not tell rows "
                                        f"apart"))
                if p.missing:
                    ev.append(_evidence("values", "blank identifiers",
                                        "some rows have no identifier"))
            else:
                d.agreement = "agree"
                ev.append(_evidence("values", f"{n} of {n} distinct",
                                    f"all {n} values are different"))
        elif h == "name":
            d.agreement = "agree" if vrole in ("name", "identifier", "text") else "conflict"
        elif h == "text":
            d.agreement = "agree" if vrole == "text" else "unknown"
        else:
            d.agreement = "agree" if vrole in ("name", "text", "identifier") else "unknown"
        return d

    if h == "category":
        ev.extend(vev)
        if vrole in ("category", "ordinal", "flag"):
            d.role, d.agreement = vrole, "agree"
        else:
            d.role, d.agreement = "category", ("conflict" if n else "unknown")
        return d

    # No role from the header: the values decide, and with one signal agreement is unknown.
    ev.extend(vev)
    d.role = vrole or "unknown"
    d.agreement = "agree" if head.scale and vrole in ("ordinal", "score") else "unknown"
    return d


def _categories_for(role: str, p: _Profile, decided: list | None) -> list | None:
    if decided is not None:
        return decided
    if role == "ordinal":
        return list(p.scale_levels)
    if role == "flag":
        return p.yes_forms + p.no_forms + p.extras
    if role == "category":
        return sorted(p.counts, key=lambda v: (v.casefold(), v))
    return None


def _file_mark(columns: list[list[str]]) -> str | None:
    """The decimal mark every column that proves one agrees on, or None when they differ."""
    marks = set()
    for cells in columns:
        for raw in set(c for c in cells if not _is_marker(c)):
            n = _number(raw, None)
            if n.form != "bad" and n.form != "ambiguous" and n.proves:
                marks.add(n.proves)
    return next(iter(marks)) if len(marks) == 1 else None


def _propose_column(name: str, cells: list[str], model_field: str | None,
                    file_mark: str | None = None) -> dict:
    head = _read_header(name)
    p = _profile(cells, file_mark)
    d = _decide(head, p)
    role = d.role
    ev = d.evidence

    if role in _NUMERIC and p.filled:
        if p.mark_from_file and p.ambiguous_cells:
            ev.append(_evidence("values", f"file decimal mark '{p.mark}'",
                                f"nothing in this column settles the decimal mark, so cells such as "
                                f"'{p.ambiguous_example}' are read with '{p.mark}', the mark every "
                                f"other column in the file that shows one uses; choose the other "
                                f"mark if this column differs"))
        elif p.mark and not p.mark_from_file:
            ev.append(_evidence("values", f"decimal mark '{p.mark}'",
                                f"{_plural(p.proof_cells, 'cell')} can only be read with '{p.mark}' "
                                f"as the decimal mark (for example '{p.proof_example}'), so this "
                                f"column uses '{p.mark}'"))
        elif len(p.marks_seen) > 1:
            d.agreement = "conflict"
            ev.append(_evidence("values", "both decimal marks",
                                "some cells use '.' and some use ',' as the decimal mark, so "
                                "cells that could be read either way are not read"))
        if p.ambiguous_cells and not p.mark:
            ev.append(_evidence("values", f"{p.ambiguous_cells} ambiguous",
                                f"{_plural(p.ambiguous_cells, 'cell')} such as "
                                f"'{p.ambiguous_example}' could be read two ways and nothing else "
                                f"in the column settles it, so "
                                f"{'it is' if p.ambiguous_cells == 1 else 'they are'} not read "
                                f"until you choose the decimal mark"))
        for symbol in p.symbols:
            code = _SYMBOL_CODES.get(symbol) or (symbol if symbol in CURRENCIES else None)
            if code and role == "money" and d.unit and code != d.unit:
                d.agreement = "conflict"
                ev.append(_evidence("values", symbol, f"cells carry '{symbol}' ({code}) but the "
                                                      f"header names {d.unit}"))
            elif code and not d.unit:
                ev.append(_evidence("values", symbol, f"cells carry '{symbol}', which suggests "
                                                      f"{code}; the unit is recorded only from "
                                                      f"the header"))
    if role == "ordinal" and p.scale_doubled:
        d.agreement = "conflict"
        ev.append(_evidence("scale", " / ".join(p.scale_doubled),
                            "one level is written more than one way ("
                            + ", ".join(f"'{v}'" for v in p.scale_doubled)
                            + "); each spelling is its own level until the file is corrected"))
    ev.extend(head.directions)
    if model_field:
        text = f"Map Columns matched this column to the model's field {model_field}"
        if model_field in YES_NO_FIELDS and role != "flag":
            text += ", which the model reads as yes or no"
        elif model_field in NUMERIC_FIELDS and role not in _NUMERIC:
            text += ", which the model reads as a number"
        ev.append(_evidence("mapping", model_field, text))

    categories = _categories_for(role, p, d.categories) if role in _CATEGORICAL else None
    if role in _CATEGORICAL and not categories:
        # A header naming a yes or no question over a column with no values: there are no states
        # to list, so the role stays unknown, with the header's word still in the evidence.
        role, categories = "unknown", None
    date_format = None
    if role == "date":
        date_format = ("%Y-%m-%d" if p.date_iso_only
                       else _FORMAT_FOR_ORDER.get(p.date_order) if p.date_order else None)
        if p.date_order:
            first = "day" if p.date_order == "dmy" else "month"
            ev.append(_evidence("values", f"{first} first",
                                f"dates such as '{p.date_example}' can only be read with the "
                                f"{first} first, so this column is read that way"))
        if not p.date_iso_only and p.date_order is None and p.filled:
            ev.append(_evidence("values", "day and month order",
                                "dates written with '/' do not show whether the day or the month "
                                "comes first, so those that could be either are not read until "
                                "you choose"))
    entry = {
        "name": name,
        "type": _type_for(role, categories),
        "format": date_format,
        "categories": categories,
        "categoriesOrdered": (role == "ordinal") if categories is not None else None,
        "missingValues": list(p.missing),
        "decimalChar": p.mark if role in _NUMERIC else None,
        "evsient:role": role,
        "evsient:unit": d.unit if role in _UNIT_ROLES else None,
        "evsient:range": d.range if role in _RANGE_ROLES else None,
        "evsient:direction": None,
        "evsient:modelField": model_field,
        "evsient:evidence": ev,
        "evsient:agreement": d.agreement,
        "evsient:provenance": "inferred",
        "evsient:reading": None,
    }
    _, entry["evsient:reading"] = _read_cells(cells, entry)
    return entry


def _type_for(role: str, categories: list | None) -> str:
    if role == "ordinal" and categories and all(isinstance(c, int) for c in categories):
        return "integer"
    return _TYPE_FOR_ROLE.get(role, "string")


# ---------- reading every cell ----------

class _Tally:
    """Patterns, counts and the reading report for one column."""

    def __init__(self, cells: int) -> None:
        self.cells = cells
        self.patterns: Counter = Counter()
        self.kinds = Counter()
        self.ambiguous = 0
        self.sentinels: Counter = Counter()

    def add(self, pattern: str, kind: str, read_as: str) -> None:
        self.patterns[(pattern, kind, read_as)] += 1
        self.kinds[kind] += 1

    def report(self, decimal: str | None, distinct: int, low: Any, high: Any) -> dict:
        ordered = sorted(self.patterns.items(), key=lambda item: (-item[1], item[0][0], item[0][2]))
        shown = ordered[:PATTERN_CAP]
        rest = ordered[PATTERN_CAP:]
        k = self.kinds
        return {
            "cells": self.cells,
            "read": k["value"] + k["sentinel"] + k["outOfRange"] + k["notWhole"] + k["extra"],
            "missing": k["missing"],
            "unreadable": k["unreadable"] + k["ambiguous"],
            "ambiguous": self.ambiguous,
            "outOfRange": k["outOfRange"],
            "notWhole": k["notWhole"],
            "decimalSeparator": decimal,
            "distinct": distinct,
            "min": low,
            "max": high,
            "patterns": [{"pattern": p, "kind": kind, "readAs": read_as, "count": c}
                         for (p, kind, read_as), c in shown],
            "patternsNotShown": ({"patterns": len(rest), "cells": sum(c for _, c in rest)}
                                 if rest else None),
            "sentinels": [{"value": v, "count": c} for v, c in
                          sorted(self.sentinels.items(), key=lambda item: (-item[1], item[0]))],
        }


def _whole_scale(entry: dict) -> bool:
    role, rng = entry["evsient:role"], entry["evsient:range"]
    if role in ("count", "year"):
        return True
    return (role == "score" and rng is not None and all(float(b).is_integer() for b in rng)
            and rng[1] - rng[0] <= 10)


def _bounds(entry: dict) -> tuple[float, float, str] | None:
    role, rng = entry["evsient:role"], entry["evsient:range"]
    if role == "latitude":
        return -90.0, 90.0, "outside -90 to 90"
    if role == "longitude":
        return -180.0, 180.0, "outside -180 to 180"
    if role == "year":
        return 1800.0, 2200.0, "not a year from 1800 to 2200"
    if rng is not None and role in ("score", "percentage"):
        return float(rng[0]), float(rng[1]), f"outside the declared range {_say(rng[0])} to {_say(rng[1])}"
    return None


def _read_cells(cells: list[str], entry: dict) -> tuple[list, dict]:
    """Every cell of one column read as its entry says, with the report of how. The only reader:
    `propose` reports with it and `parse` returns what it read, so what was shown is what is done."""
    role = entry["evsient:role"]
    missing = set(entry["missingValues"])
    categories = entry["categories"]
    tally = _Tally(len(cells))
    typed: list = []
    filled = [c for c in cells if c not in missing]
    distinct = len(set(filled))
    low = high = None

    numeric_ordinal = role == "ordinal" and bool(categories) and all(isinstance(c, int) for c in categories)
    if role in _NUMERIC or numeric_ordinal:
        mark = entry["decimalChar"]
        whole = _whole_scale(entry)
        bounds = None if numeric_ordinal else _bounds(entry)
        position = {c: i for i, c in enumerate(categories)} if numeric_ordinal else {}
        values = []
        for raw in cells:
            if raw in missing:
                typed.append(None)
                tally.add(raw, "missing", "missing")
                continue
            n = _number(raw, mark)
            tally.ambiguous += n.ambiguous
            if n.state == "ambiguous":
                typed.append(None)
                tally.add(_shape(raw), "ambiguous",
                          f"not read: {_GROUP_NAMES[n.group]} could be a decimal mark or separate "
                          f"thousands, and nothing else in this column settles which")
                continue
            if n.state == "conflict":
                typed.append(None)
                tally.add(raw, "unreadable", f"not read: it uses '{n.proves}' as the decimal mark, "
                                             f"and this column uses '{mark}'")
                continue
            if n.state != "value":
                typed.append(None)
                tally.add(raw, "unreadable", "not a number")
                continue
            v = n.value
            sentinel = v in SENTINELS and not (role in ("latitude", "longitude")
                                               and bounds and bounds[0] <= v <= bounds[1])
            if sentinel:
                tally.sentinels[raw] += 1
            if numeric_ordinal:
                if v.is_integer() and int(v) in position:
                    i = position[int(v)]
                    typed.append(float(i))
                    tally.add(raw, "value", f"{int(v)} ({i + 1} of {len(categories)})")
                    continue
                typed.append(None)
                note = f"not read: not one of the levels {categories[0]} to {categories[-1]}"
                if sentinel:
                    note += "; it is often a no-data code, so mark it missing if it is one"
                tally.add(raw, "unreadable", note)
                continue
            typed.append(v)
            values.append(v)
            if sentinel:
                tally.add(raw, "sentinel", f"read as {_say(v)}, but {_say(v)} is often a no-data "
                                           f"code; mark it missing if it is one")
            elif bounds and not bounds[0] <= v <= bounds[1]:
                tally.add(raw, "outOfRange", f"read as {_say(v)}, {bounds[2]}; kept as written, "
                                             f"not clamped")
            elif whole and not v.is_integer():
                tally.add(raw, "notWhole", f"read as {_say(v)}, a decimal on a whole-number scale; "
                                           f"kept as written, not rounded")
            else:
                tally.add(_shape(raw), "value", _number_note(n, mark))
        if values:
            low, high = _num(min(values)), _num(max(values))
        return typed, tally.report(mark, distinct, low, high)

    if role == "date":
        order = _ORDER_FOR_FORMAT.get(entry["format"])
        dates = []
        for raw in cells:
            if raw in missing:
                typed.append(None)
                tally.add(raw, "missing", "missing")
                continue
            iso, state, proves, timed, form = _date(raw, order)
            if form == "slash" and proves is None and state in ("value", "ambiguous"):
                parts = re.split(r"[/.]", raw.strip())
                tally.ambiguous += int(parts[0]) != int(parts[1])
            if state == "ambiguous":
                typed.append(None)
                tally.add(_shape(raw), "ambiguous", "not read: the day and the month could be "
                                                    "either way round, and nothing else in this "
                                                    "column settles which")
            elif state == "conflict":
                typed.append(None)
                tally.add(raw, "unreadable", "not read: its day and month are the other way round "
                                             "from this column's")
            elif state != "value":
                typed.append(None)
                tally.add(raw, "unreadable", "not a date")
            else:
                typed.append(iso)
                dates.append(iso)
                read_as = ("a date, year-month-day" if form == "iso" else
                           "a date, day/month/year" if (proves or order) == "dmy" else
                           "a date, month/day/year" if (proves or order) == "mdy" else
                           "a date (its day and month are the same)")
                if timed:
                    read_as += "; the time of day is set aside"
                tally.add(_shape(raw), "value", read_as)
        if dates:
            low, high = min(dates), max(dates)
        return typed, tally.report(None, distinct, low, high)

    if role in _CATEGORICAL:
        cats = list(categories or [])
        position = {c: i for i, c in enumerate(cats)}
        for raw in cells:
            if raw in missing:
                typed.append(None)
                tally.add(raw, "missing", "missing")
            elif role == "flag":
                folded = raw.strip().casefold()
                if folded in YES and raw in position:
                    typed.append(1.0)
                    tally.add(raw, "value", "yes")
                elif folded in NO and raw in position:
                    typed.append(0.0)
                    tally.add(raw, "value", "no")
                elif raw in position:
                    typed.append(None)
                    tally.add(raw, "extra", "a state that is neither yes nor no; mark it missing "
                                            "or keep it as its own state")
                else:
                    typed.append(None)
                    tally.add(raw, "unreadable", "not read: not yes, no or one of this column's "
                                                 "states")
            elif raw in position:
                if role == "ordinal":
                    typed.append(float(position[raw]))
                    tally.add(raw, "value", f"{raw} ({position[raw] + 1} of {len(cats)})")
                else:
                    typed.append(raw)
                    tally.add(raw, "value", "a category")
            else:
                typed.append(None)
                tally.add(raw, "unreadable", "not read: not one of this column's "
                                             + ("levels" if role == "ordinal" else "categories"))
        return typed, tally.report(None, distinct, None, None)

    # Identifiers, names, addresses, text and unknown columns are kept exactly as written.
    for raw in cells:
        if raw in missing:
            typed.append(None)
            tally.add(raw, "missing", "missing")
        else:
            typed.append(raw)
            pattern = re.sub(r"[A-Za-z]", "A", _shape(raw)) if role == "identifier" else raw
            tally.add(pattern, "value", "kept as written")
    return typed, tally.report(None, distinct, None, None)


# ---------- the public interface ----------

def _column_names(frame: pd.DataFrame) -> list[str]:
    names = [str(c) for c in frame.columns]
    if len(set(names)) != len(names):
        raise ValueError("Two columns in this file have the same name. Rename one and upload it again.")
    return names


def _model_fields(model_mapping: dict[str, str] | None, columns: list[str]) -> dict[str, str]:
    """{column: model field} from Map Columns' {model field: column}, the shape intake keeps."""
    by_column: dict[str, str] = {}
    for canonical, column in sorted((model_mapping or {}).items()):
        if column is None:
            continue
        if column not in columns:
            raise ValueError(f"The model field {canonical} is mapped to '{column}', which is not a "
                             f"column in this file.")
        if column in by_column:
            raise ValueError(f"The column '{column}' is mapped to both {by_column[column]} and "
                             f"{canonical}. Map it to one field only.")
        by_column[column] = canonical
    return by_column


def _cells(frame: pd.DataFrame, position: int) -> list[str]:
    return [_text(c) for c in frame.iloc[:, position].tolist()]


def propose(frame: pd.DataFrame, model_mapping: dict[str, str] | None = None) -> list[dict]:
    """One proposed dictionary entry per column, in the file's order. Changes nothing.

    Read the file with every cell as text (`dtype=object, keep_default_na=False`); a frame pandas
    has already typed has lost what its cells said. `model_mapping` is Map Columns' choice in
    intake's shape, `{model field: column}`, and is recorded, never changed.
    """
    columns = _column_names(frame)
    by_column = _model_fields(model_mapping, columns)
    cells = [_cells(frame, i) for i in range(len(columns))]
    mark = _file_mark(cells)
    return [_propose_column(name, cells[i], by_column.get(name), mark)
            for i, name in enumerate(columns)]


def reread(frame: pd.DataFrame, entries: list[dict]) -> list[dict]:
    """The entries with each reading report made again from the file, for after `confirm` has
    changed how a column reads (its role, missing states, levels, decimal mark or date order)."""
    columns = _column_names(frame)
    out = []
    for entry in entries:
        entry = copy.deepcopy(entry)
        if entry["name"] not in columns:
            raise ValueError(f"There is no column called '{entry['name']}' in this file.")
        _, entry["evsient:reading"] = _read_cells(_cells(frame, columns.index(entry["name"])), entry)
        out.append(entry)
    return out


#: What a visitor may change on a column, and whether the change alters how its cells read.
_CHANGES = {"role": True, "unit": False, "direction": False, "categories": True,
            "missingValues": True, "range": True, "decimalSeparator": True, "dateFormat": True,
            "confirm": False}


def confirm(entries: list[dict], changes: list[dict]) -> list[dict]:
    """The entries with the visitor's changes applied. Changes nothing it is given.

    Each change is `{"column": name, ...}` with any of: `role`, `unit`, `direction`, `categories`
    (the levels in order, lowest first for an ordinal), `missingValues`, `range`,
    `decimalSeparator`, `dateFormat`, or `confirm: true` to accept the entry as proposed. A changed
    or confirmed entry becomes `confirmed_by_user` and is never relabelled as inferred. A change
    that alters how cells read clears the entry's reading report; `reread` makes it again.

    Raises ValueError, in a sentence a planner can act on, for anything the dictionary cannot
    hold: an unknown role, an ordinal with no order, a direction that is not one of three, a
    value dropped rather than kept or marked missing.
    """
    out = [copy.deepcopy(e) for e in entries]
    by_name = {e["name"]: e for e in out}
    for change in changes:
        if not isinstance(change, dict) or "column" not in change:
            raise ValueError("Each change must say which column it is for.")
        entry = by_name.get(change["column"])
        if entry is None:
            raise ValueError(f"There is no column called '{change['column']}' in this file.")
        unknown = sorted(set(change) - set(_CHANGES) - {"column"})
        if unknown:
            raise ValueError(f"'{unknown[0]}' is not something that can be changed on a column. "
                             f"Change its role, unit, direction, categories, missingValues, range, "
                             f"decimalSeparator or dateFormat, or confirm it.")
        _apply(entry, change)
        entry["evsient:provenance"] = "confirmed_by_user"
        _validate(entry)
        if any(_CHANGES[k] for k in change if k in _CHANGES):
            entry["evsient:reading"] = None
    return out


def _apply(entry: dict, change: dict) -> None:
    name = entry["name"]
    old_categories = list(entry["categories"] or [])
    old_missing = list(entry["missingValues"])

    if "role" in change:
        role = change["role"]
        if role not in ROLES:
            raise ValueError(f"'{role}' is not a kind of column the planner knows. Choose one of: "
                             f"{', '.join(ROLES)}.")
        entry["evsient:role"] = role
        if role not in _CATEGORICAL:
            entry["categories"] = entry["categoriesOrdered"] = None
        elif entry["categories"] is None and "categories" not in change:
            raise ValueError(f"To read {name} as {_article(role)}, list its values. Its reading "
                             f"report shows them.")
        if role not in _UNIT_ROLES and "unit" not in change:
            entry["evsient:unit"] = None
        if role not in _RANGE_ROLES and "range" not in change:
            entry["evsient:range"] = None
        if role not in _DIRECTIONAL and "direction" not in change:
            entry["evsient:direction"] = None
        if role not in _NUMERIC:
            entry["decimalChar"] = None
        if role != "date":
            entry["format"] = None
        if role == "ordinal" and "categories" not in change and not entry["categoriesOrdered"]:
            raise ValueError(f"{name} is ordinal, so its levels need an order. List them from "
                             f"lowest to highest.")

    role = entry["evsient:role"]
    if "missingValues" in change:
        missing = change["missingValues"]
        if not isinstance(missing, list) or not all(isinstance(m, str) for m in missing):
            raise ValueError(f"The missing values for {name} must be a list of the cells' text.")
        if len(set(missing)) != len(missing):
            raise ValueError(f"A missing value for {name} is listed twice.")
        entry["missingValues"] = list(missing)

    if "categories" in change:
        categories = change["categories"]
        if not isinstance(categories, list) or not categories:
            raise ValueError(f"The values of {name} must be a list.")
        if len(set(map(str, categories))) != len(categories):
            raise ValueError(f"A value of {name} is listed twice.")
        known = set(map(str, old_categories)) | set(old_missing)
        new = [c for c in categories if str(c) not in known]
        if old_categories and new:
            raise ValueError(f"'{new[0]}' is not a value in {name}.")
        entry["categories"] = list(categories)
    if role in _CATEGORICAL and entry["categories"] is not None:
        missing = set(entry["missingValues"])
        if "categories" not in change:
            # A value newly marked missing leaves the levels; one no longer missing joins them,
            # except in an ordinal, where only the visitor can say where it sits.
            kept = [c for c in entry["categories"] if str(c) not in missing]
            returning = [m for m in old_missing if m not in missing and m not in map(str, kept)]
            if returning and role == "ordinal":
                raise ValueError(f"Say where '{returning[0]}' sits in the order of {name}: send "
                                 f"its levels from lowest to highest.")
            entry["categories"] = kept + returning
        overlap = [c for c in entry["categories"] if str(c) in missing]
        if overlap:
            raise ValueError(f"'{overlap[0]}' cannot be both a value of {name} and missing.")
        dropped = [c for c in old_categories if str(c) not in set(map(str, entry["categories"])) | missing]
        if dropped:
            raise ValueError(f"'{dropped[0]}' is a value in {name}. Keep it, or mark it missing; it "
                             f"cannot be dropped.")
        entry["categoriesOrdered"] = role == "ordinal"
    entry["type"] = _type_for(role, entry["categories"])

    if "unit" in change:
        unit = change["unit"]
        if unit is not None:
            if role not in _UNIT_ROLES:
                raise ValueError(f"{name} is {_article(role)}, which has no unit.")
            if role == "money" and unit not in CURRENCIES:
                raise ValueError(f"'{unit}' is not a currency code the planner knows. Use a "
                                 f"three-letter ISO 4217 code such as USD, EUR or KES.")
            if not isinstance(unit, str) or not re.fullmatch(r"[A-Za-z0-9.\[\]/{}%^_-]{1,32}", unit):
                raise ValueError(f"'{unit}' is not a unit code. Use a UCUM code such as kW, m2 or "
                                 f"kW.h.")
        entry["evsient:unit"] = unit

    if "range" in change:
        rng = change["range"]
        if rng is not None:
            if role not in _RANGE_ROLES:
                raise ValueError(f"{name} is {_article(role)}, which has no declared range.")
            if (not isinstance(rng, list) or len(rng) != 2
                    or not all(isinstance(b, (int, float)) and not isinstance(b, bool)
                               and math.isfinite(b) for b in rng) or rng[0] >= rng[1]):
                raise ValueError(f"A range for {name} needs a lowest and a highest number, lowest "
                                 f"first.")
            rng = [_num(rng[0]), _num(rng[1])]
        entry["evsient:range"] = rng

    if "direction" in change:
        direction = change["direction"]
        if direction is not None and direction not in DIRECTIONS:
            raise ValueError(f"The direction for {name} must be higher_better (higher is better), "
                             f"lower_better (lower is better) or neither.")
        if direction in ("higher_better", "lower_better") and role not in _DIRECTIONAL:
            raise ValueError(f"{name} is {_article(role)}, which has no order, so higher or lower "
                             f"cannot be better.")
        entry["evsient:direction"] = direction

    if "decimalSeparator" in change:
        mark = change["decimalSeparator"]
        if mark not in (".", ",", None):
            raise ValueError(f"The decimal mark for {name} must be '.' or ','.")
        if mark is not None and role not in _NUMERIC:
            raise ValueError(f"{name} is {_article(role)}, so it has no decimal mark.")
        entry["decimalChar"] = mark

    if "dateFormat" in change:
        fmt = change["dateFormat"]
        if fmt not in DATE_FORMATS and fmt is not None:
            raise ValueError(f"The date order for {name} must be one of {', '.join(DATE_FORMATS)}.")
        if fmt is not None and role != "date":
            raise ValueError(f"{name} is {_article(role)}, so it has no date order.")
        entry["format"] = fmt

    if "confirm" in change and change["confirm"] is not True:
        raise ValueError(f"To confirm {name}, send confirm: true.")


def _article(role: str) -> str:
    return f"an {role}" if role[0] in "aeiou" else f"a {role}"


def _validate(entry: dict) -> None:
    """Raise ValueError if an entry is not one the dictionary can hold."""
    name, role = entry.get("name"), entry.get("evsient:role")
    if role not in ROLES:
        raise ValueError(f"'{role}' is not a kind of column the planner knows.")
    categories = entry.get("categories")
    if role == "ordinal" and (not categories or len(categories) < 2
                              or entry.get("categoriesOrdered") is not True):
        raise ValueError(f"{name} is ordinal, so its levels need an order. List them from lowest "
                         f"to highest.")
    if role == "flag" and not any(str(c).strip().casefold() in YES | NO for c in categories or []):
        raise ValueError(f"None of {name}'s values read as yes or no, so it cannot be a yes or no "
                         f"column.")
    if role in _CATEGORICAL and not categories:
        raise ValueError(f"To read {name} as {_article(role)}, list its values.")
    if entry.get("evsient:direction") not in (None, *DIRECTIONS):
        raise ValueError(f"The direction for {name} must be higher_better, lower_better or neither.")
    if entry.get("evsient:provenance") not in PROVENANCE:
        raise ValueError(f"The column dictionary entry for {name} has no valid provenance.")
    if entry.get("evsient:agreement") not in AGREEMENT:
        raise ValueError(f"The column dictionary entry for {name} has no valid agreement.")
    if entry.get("evsient:direction") is not None and entry.get("evsient:provenance") == "inferred":
        raise ValueError(f"The direction for {name} was never confirmed. A direction is set only "
                         f"by the person using the planner.")


# ---------- the project file ----------

def to_table_schema(entries: list[dict]) -> dict:
    """The dictionary as a Frictionless Table Schema v2, for the `.evsient` project file.

    Standard keys that do not apply to a column (`categories` on a measure, say) are left out,
    as the specification expects; EV-SIENT's own keys are kept, null or not.
    """
    fields = []
    for entry in entries:
        _validate(entry)
        out = {}
        for key in _ENTRY_KEYS:
            if key in _OPTIONAL_STANDARD and entry.get(key) is None:
                continue
            out[key] = copy.deepcopy(entry.get(key))
        fields.append(out)
    return {"$schema": TABLE_SCHEMA_PROFILE, "fields": fields, "missingValues": [""],
            "evsient:dictionaryVersion": DICTIONARY_VERSION}


def from_table_schema(schema: dict) -> list[dict]:
    """The dictionary entries a project file's Table Schema holds; the inverse of
    `to_table_schema`, exactly."""
    if not isinstance(schema, dict) or not isinstance(schema.get("fields"), list):
        raise ValueError("This project file has no column dictionary, or it is damaged.")
    version = schema.get("evsient:dictionaryVersion")
    if version != DICTIONARY_VERSION:
        raise ValueError(f"This project file's column dictionary is version {version}; this "
                         f"planner reads version {DICTIONARY_VERSION}.")
    entries = []
    for f in schema["fields"]:
        lacking = [k for k in _ENTRY_KEYS if k not in _OPTIONAL_STANDARD and k not in f]
        if lacking:
            raise ValueError(f"The column dictionary entry for {f.get('name', 'a column')} is "
                             f"missing {lacking[0]}.")
        entry = {key: copy.deepcopy(f.get(key)) for key in _ENTRY_KEYS}
        _validate(entry)
        entries.append(entry)
    return entries


# ---------- typed values for the other modules ----------

def parse(frame: pd.DataFrame, entries: list[dict]) -> pd.DataFrame:
    """The typed values Explore and the visitor's own index read, beside the raw cells.

    Columns are a two-level index: `(column, "value")` and `(column, "raw")`. Numbers are floats;
    an ordinal is its level's position (0 for the lowest) as a float; a flag is 1.0, 0.0 or NaN; a
    category is a pandas Categorical; a date is a datetime64; other roles keep their text. Missing
    and unread cells are NaN (or None), exactly the cells the reading report says were not read.
    The raw column is the frame's own, unaltered.
    """
    columns = _column_names(frame)
    data: dict[tuple[str, str], Any] = {}
    for entry in entries:
        name = entry["name"]
        if name not in columns:
            raise ValueError(f"There is no column called '{name}' in this file.")
        position = columns.index(name)
        typed, _ = _read_cells(_cells(frame, position), entry)
        role = entry["evsient:role"]
        if role in _NUMERIC or role in ("ordinal", "flag"):
            value = pd.Series([np.nan if v is None else float(v) for v in typed],
                              index=frame.index, dtype="float64")
        elif role == "category":
            value = pd.Series(pd.Categorical(typed, categories=list(entry["categories"])),
                              index=frame.index)
        elif role == "date":
            value = pd.Series(pd.to_datetime(pd.Series(typed, dtype=object), format="%Y-%m-%d"),
                              index=frame.index)
        else:
            value = pd.Series(typed, index=frame.index, dtype=object)
        data[(name, "value")] = value
        data[(name, "raw")] = frame.iloc[:, position].copy()
    out = pd.DataFrame(data, index=frame.index)
    out.columns = pd.MultiIndex.from_tuples(list(data), names=["column", "part"])
    return out


# ---------- the browser door ----------

def _frame_from(table: dict) -> pd.DataFrame:
    """An uploaded table as `browser_api` builds it: every cell kept as the text typed."""
    columns = [str(c) for c in table["columns"]]
    width = len(columns)
    rows = [(["" if cell is None else str(cell) for cell in row] + [""] * width)[:width]
            for row in table["rows"]]
    return pd.DataFrame(rows, columns=columns, dtype=object)


def _out(payload: dict) -> str:
    return json.dumps(payload, allow_nan=False)


def bridge_propose(table_json: str, mapping_json: str = "null") -> str:
    """`propose` for the browser worker: `{"columns", "rows"}` and Map Columns' mapping (either
    `{"mapping": {...}}` or the mapping itself) in, `{"entries": [...]}` out."""
    table = json.loads(table_json)
    mapping = json.loads(mapping_json or "null") or {}
    if isinstance(mapping, dict) and isinstance(mapping.get("mapping"), dict):
        mapping = mapping["mapping"]
    return _out({"entries": propose(_frame_from(table), mapping)})


def bridge_confirm(entries_json: str, changes_json: str) -> str:
    """`confirm` for the browser worker: `{"entries"}` and `{"changes"}` (or bare lists) in,
    `{"entries": [...]}` out."""
    entries = json.loads(entries_json)
    changes = json.loads(changes_json)
    if isinstance(entries, dict):
        entries = entries.get("entries", [])
    if isinstance(changes, dict):
        changes = changes.get("changes", [])
    return _out({"entries": confirm(entries, changes)})


def bridge_reread(table_json: str, entries_json: str) -> str:
    """`reread` for the browser worker, after a change that cleared a reading report."""
    entries = json.loads(entries_json)
    if isinstance(entries, dict):
        entries = entries.get("entries", [])
    return _out({"entries": reread(_frame_from(json.loads(table_json)), entries)})

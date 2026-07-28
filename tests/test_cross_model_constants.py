"""A physical assumption may not hold two different values in two halves of one model.

The defect this exists to stop recurring
----------------------------------------
`src/fcf_m2/config.py` has always said `CHARGER_EFFICIENCY = 0.92`. Three MATLAB functions
defaulted `ChargerEfficiency` to **0.93**. Same physical quantity, same model, two numbers,
and every MATLAB energy figure was consequently `1/0.93` of the contract's rather than
`1/0.92`.

**It survived because charger efficiency is not a contract field.** The canonical contract is
the mechanism that stops exactly this — one number, one place, consumers quote and never
re-derive — and this quantity lived outside it, so there was nothing to reconcile against. It
was found only by running the pipeline on the canonical data and asking why the energy column
disagreed with the contract's: the implied efficiency measured **0.9300** across all 120 rows.

That is the general lesson, and it is why this file checks by parsing rather than by trusting:
a constant duplicated across languages diverges silently, and the only reliable defence is a
test that reads both copies and compares them.

Scope, stated honestly
----------------------
This checks constants that **demonstrably appear in both halves**. It is not a proof that no
other duplicated constant exists — that would require a semantic mapping between two
languages' variable names, which nothing here has. `test_no_unreviewed_numeric_defaults`
narrows the gap by listing every numeric default in the MATLAB sources so a new one cannot
appear unnoticed, but a reviewer still has to decide whether each has a Python counterpart.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import config  # noqa: E402

MATLAB_SRC = REPO / "matlab/src"

#: MATLAB `addParameter` default -> the Python constant that must equal it.
#: Add a row here whenever a shared physical assumption gains a MATLAB default.
SHARED_CONSTANTS = {
    "ChargerEfficiency": ("CHARGER_EFFICIENCY", "grid-to-battery charger efficiency"),
}

ADD_PARAMETER = re.compile(
    r'addParameter\(\s*p\s*,\s*"(?P<name>\w+)"\s*,\s*(?P<value>-?\d+(?:\.\d+)?)\s*,', re.S)


def matlab_defaults() -> dict[str, list[tuple[Path, float]]]:
    """Every numeric `addParameter` default across matlab/src, by parameter name."""
    found: dict[str, list[tuple[Path, float]]] = {}
    for source in sorted(MATLAB_SRC.glob("*.m")):
        text = source.read_text(encoding="utf-8")
        # Strip comment-only lines so the prose explaining the old 0.93 is not read as code.
        code = "\n".join(line for line in text.splitlines()
                         if not line.lstrip().startswith("%"))
        for match in ADD_PARAMETER.finditer(code):
            found.setdefault(match["name"], []).append(
                (source.relative_to(REPO), float(match["value"])))
    return found


@pytest.fixture(scope="module")
def defaults():
    return matlab_defaults()


def test_the_parser_actually_finds_something():
    """A parser that silently matches nothing turns this whole file into a no-op that
    reports PASS. Three gates in this program have already failed that way."""
    found = matlab_defaults()
    assert len(found) >= 5, f"only found {len(found)} addParameter defaults; parser is broken"
    assert "ChargerEfficiency" in found


@pytest.mark.parametrize("matlab_name", sorted(SHARED_CONSTANTS))
def test_shared_constants_agree_between_python_and_matlab(matlab_name, defaults):
    python_name, description = SHARED_CONSTANTS[matlab_name]
    expected = getattr(config, python_name)
    occurrences = defaults.get(matlab_name, [])
    assert occurrences, f"{matlab_name} has no numeric default in matlab/src"

    disagreeing = [(str(path), value) for path, value in occurrences if value != expected]
    assert disagreeing == [], (
        f"{description}: config.{python_name} = {expected}, but MATLAB defaults "
        f"{matlab_name} to {disagreeing}.\n"
        f"Python is the single producer (data/contract/v1/README.md), so MATLAB follows it. "
        f"Do not 'fix' this by changing the Python value unless that is the deliberate, "
        f"documented decision -- every published emissions figure derives from it.")


def test_every_occurrence_is_checked_not_just_the_first(defaults):
    """The original defect was in THREE files. Finding one and stopping would have left
    two, and the two that remained would have been the ones nobody looked at again."""
    assert len(defaults["ChargerEfficiency"]) >= 3, (
        "expected ChargerEfficiency to be defaulted in at least 3 MATLAB files; if that "
        "changed, confirm the parameter was removed rather than merely renamed")


def test_no_unreviewed_numeric_defaults(defaults):
    """Every numeric MATLAB default is either shared with Python or explicitly MATLAB-only.

    This is a **review** gate, not a correctness one: it cannot tell whether a MATLAB-only
    constant *should* have a Python counterpart. It only guarantees that a new one cannot
    appear without somebody adding it to a list, which is where the question gets asked.
    """
    # Each entry was checked against the Python package before being listed. The two the
    # gate caught on its first run are recorded with what the check found:
    #
    #   TimeStepMinutes (5)     -- makeSessionProfiles' simulation resolution. Python has no
    #                              timestepped simulation: peak_wait.py and queueing.py are
    #                              event- and formula-based, with no fixed grid to disagree
    #                              about. Confirmed by search: no step/resolution constant.
    #   FailSafeFraction (0.5)  -- managedCharging's comms-loss fallback. Python implements no
    #                              managed-charging strategy at all; the only mentions are the
    #                              contract's controlled vocabulary and the MATLAB adapter,
    #                              neither of which computes one. Nothing to disagree with.
    matlab_only = {
        "Seed", "DiversityFactor", "AssumedSiteCapacity_kW", "SiteCapacity_kW",
        "PowerFactor", "DemandChargeRate", "StopTime", "SampleTime", "FontSize",
        "MaxPorts", "MinPorts", "Horizon", "DiscountRate", "AnalysisYears",
        "TimeStepMinutes", "FailSafeFraction",
    }
    unreviewed = sorted(set(defaults) - set(SHARED_CONSTANTS) - matlab_only)
    assert unreviewed == [], (
        f"new numeric MATLAB default(s) not yet reviewed for a Python counterpart: "
        f"{unreviewed}.\nAdd each to SHARED_CONSTANTS (with the Python constant it must "
        f"equal) or to matlab_only (because it genuinely has no Python twin). Deciding "
        f"which is the point of this test.")


def test_python_charger_efficiency_is_where_the_docs_say_it_is():
    """The error message above tells a reader to treat Python as authoritative. That is only
    useful if the authoritative value is where it claims to be."""
    assert hasattr(config, "CHARGER_EFFICIENCY")
    assert 0 < config.CHARGER_EFFICIENCY <= 1
    source = (REPO / "src/fcf_m2/config.py").read_text()
    assert "CHARGER_EFFICIENCY" in source

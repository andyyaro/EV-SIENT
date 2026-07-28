"""The one registry of what the platform can do, and which tier can do it.

Why a registry rather than buttons wired to code
------------------------------------------------
Phase 7 requires that **everything the platform generates is byte-identical to what the CLI
generates**, and that the web tier **states plainly which capabilities require the desktop
app rather than hiding or faking them**. Both fall out of one decision: the platform does not
call the model, it invokes the *same command the CLI invokes*.

So an operation is a **declared command**, not a Python callable. The UI renders this
registry; the desktop tier runs the command; the web tier renders the same list with the
desktop-only entries visibly unavailable and says why. There is no second code path to drift,
which is what makes byte-equivalence provable rather than asserted — see
``tests/test_operations.py``.

This module deliberately knows nothing about any UI framework. Whatever shell Phase 7 lands
in, it reads this.

What is NOT here
----------------
No operation computes anything. ``src/fcf_m2`` remains the only scorer, exactly as the
master prompt requires. If a capability cannot be expressed as "run this command", it does
not belong in the platform until it can.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

#: Capability tiers. The web tier is the PRIMARY distribution, so "desktop" is the exception
#: that must justify itself, not the default.
TIER_BOTH = "both"
TIER_DESKTOP = "desktop"


@dataclass(frozen=True)
class Operation:
    """One thing the platform can do, expressed as the command that does it."""

    id: str
    label: str
    #: What a non-specialist reader should understand this does.
    description: str
    tier: str
    #: argv, relative to the repository root. ``{py}`` is substituted with the interpreter.
    command: list[str]
    #: Paths (repo-relative) this operation writes. Used by the equivalence gate.
    produces: list[str] = field(default_factory=list)
    #: Why this needs the desktop app. REQUIRED for desktop-only operations, because
    #: "unavailable" with no reason is indistinguishable from a broken button.
    desktop_reason: str = ""
    #: Stated limitation shown beside the control, if any.
    caveat: str = ""
    #: Platforms this operation can actually run on. Empty means "anywhere".
    #:
    #: `verify-all` is declared as `bash scripts/verify.sh` and will not run on a stock Windows
    #: machine. Left undeclared, the platform would offer a button that simply fails there —
    #: and this registry's own rule is that an unavailable capability states WHY rather than
    #: appearing broken. The rule was being applied to tiers and not to platforms.
    platforms: tuple[str, ...] = ()
    #: Why it cannot run elsewhere. Required whenever `platforms` is set, for the same reason
    #: `desktop_reason` is required for desktop-only operations.
    platform_reason: str = ""

    def __post_init__(self) -> None:
        if self.platforms and not self.platform_reason:
            raise ValueError(
                f"operation {self.id!r} restricts platforms with no stated reason; a control "
                f"that is unavailable without explanation is indistinguishable from a broken "
                f"one")
        if self.tier == TIER_DESKTOP and not self.desktop_reason:
            raise ValueError(
                f"operation {self.id!r} is desktop-only with no stated reason. The web tier "
                f"must say WHY a capability is unavailable; an unexplained disabled control "
                f"is indistinguishable from a broken one.")
        if self.tier not in (TIER_BOTH, TIER_DESKTOP):
            raise ValueError(f"operation {self.id!r} has unknown tier {self.tier!r}")

    def argv(self, python: str | None = None) -> list[str]:
        interpreter = python or sys.executable
        return [interpreter if part == "{py}" else part for part in self.command]


#: Every operation the platform exposes.
#:
#: Ordered as a user meets them: look at what exists, then run something, then generate an
#: artifact from it.
OPERATIONS: list[Operation] = [
    # ---------------------------------------------------------------- inspect (both tiers)
    Operation(
        id="validate-contract-v1",
        label="Check the canonical contract (v1)",
        description=(
            "Re-checks the frozen v1 contract against every rule, its JSON Schema, and its "
            "SHA-256 hash chain. Proves the numbers on screen match the file they came from."),
        tier=TIER_BOTH,
        command=["{py}", "-m", "fcf_m2.workflow", "validate-contract", "data/contract/v1"],
    ),
    Operation(
        id="validate-contract-v2",
        label="Check the canonical contract (v2)",
        description=(
            "Same checks for contract v2, which adds the fields the field-data loop produces. "
            "v2 is additive: every v1 value survives unchanged."),
        tier=TIER_BOTH,
        command=["{py}", "-m", "fcf_m2.workflow", "validate-contract", "data/contract/v2"],
    ),

    # ---------------------------------------------------------------- run the model
    Operation(
        id="run-milestone2-v3",
        label="Run the model — canonical (milestone2_v3)",
        description=(
            "Runs the full Python model in canonical mode and regenerates the contract: "
            "demand, right-sizing, waits, economics, emissions, confidence and triggers."),
        tier=TIER_DESKTOP,
        desktop_reason=(
            "Running the model executes Python on your machine. The web tier serves "
            "precomputed results and cannot execute anything."),
        command=["{py}", "-m", "fcf_m2.workflow", "run",
                 "--mode", "milestone2_v3", "--out", "data/outputs/v3_run"],
        produces=["data/outputs/v3_run/run_summary.json"],
    ),
    Operation(
        id="run-legacy-v2",
        label="Run the model — legacy V2 baseline",
        description=(
            "Reproduces the accepted V2 baseline exactly: 25 starter ports, 48 pathway. Kept "
            "runnable so the older published figures stay checkable."),
        tier=TIER_DESKTOP,
        desktop_reason=(
            "Running the model executes Python on your machine. The web tier serves "
            "precomputed results and cannot execute anything."),
        command=["{py}", "-m", "fcf_m2.workflow", "run",
                 "--mode", "legacy_v2", "--out", "data/outputs/legacy_check"],
        produces=["data/outputs/legacy_check/run_summary.json"],
        caveat="Legacy mode uses the retired 2035/2050 horizons and cohort-relative scoring.",
    ),

    # ---------------------------------------------------------------- field data (V4)
    Operation(
        id="ingest-observations",
        label="Check what field observations would change",
        description=(
            "Reads observed capacity and session records and reports what they WOULD change — "
            "which sites upgrade from placeholder capacity, which triggers become evaluable. "
            "It never writes: received values enter the inputs and the model re-runs."),
        tier=TIER_DESKTOP,
        desktop_reason=(
            "Reads observation files from your machine. The web tier has no access to your "
            "files and cannot run the ingestion."),
        command=["{py}", "-m", "fcf_m2.workflow", "ingest-observations"],
        caveat=("No field observations have been received. Today this reports nothing to "
                "change, which is the correct answer."),
    ),

    # ---------------------------------------------------------------- generate artifacts
    Operation(
        id="build-contract-v2",
        label="Rebuild contract v2 from the frozen v1",
        description=(
            "Widens the frozen v1 contract into v2. Every shared field is copied across "
            "unchanged, so 'additive' holds by construction rather than by promise."),
        tier=TIER_DESKTOP,
        desktop_reason=("Writes files into the repository. The web tier is served as static\n                        files and has nowhere to write."),
        command=["{py}", "scripts/build_contract_v2.py"],
        produces=["data/contract/v2/contract_manifest.json"],
    ),
    Operation(
        id="build-static-dashboard",
        label="Regenerate the static dashboard",
        description=(
            "Rebuilds the nine contract-derived charts, each stamped with the run and source "
            "it came from."),
        tier=TIER_DESKTOP,
        desktop_reason=("Renders and writes image files. The web tier serves the images from\n                        the last desktop run instead."),
        command=["{py}", "scripts/build_static_dashboard.py"],
        produces=["dashboard/static/footer_log.json"],
    ),
    Operation(
        id="build-tableau-sheets",
        label="Regenerate the Tableau sheet data",
        description=(
            "Rebuilds the seven Tableau sheet tables and the workbook spec from the canonical "
            "contract. Publishing to Tableau Public remains a manual, deliberate step."),
        tier=TIER_DESKTOP,
        desktop_reason=("Writes data files, and publishing drives the Tableau Public desktop\n                        application with real keystrokes. Neither is possible in a browser."),
        command=["{py}", "scripts/build_tableau_workbook.py"],
        produces=["dashboard/tableau/build/workbook_spec.json"],
        caveat=("Building the .twbx and publishing need Tableau Public installed and a "
                "signed-in session. Four presentation features remain unbuildable — see "
                "dashboard/tableau/CAPABILITY_GAP.md."),
    ),
    Operation(
        id="build-nfc-tags",
        label="Generate NFC tag payloads and QR fallbacks",
        description=(
            "Produces the NDEF payload for each site tag, a QR code carrying the same URL, and "
            "the placement cards. Writing a physical tag is done with a phone."),
        tier=TIER_DESKTOP,
        desktop_reason=("Writes payload, QR and placement-card files to disk. The web tier\n                        offers the already-generated payloads for download instead."),
        command=["{py}", "scripts/build_nfc_tags.py"],
        produces=["docs/nfc/tag_payloads.csv"],
    ),
    Operation(
        id="build-docs",
        label="Regenerate the workflow documentation",
        description="Rewrites the workflow step documentation from the executable manifest, "
                    "so the docs cannot drift from what the code actually does.",
        tier=TIER_DESKTOP,
        desktop_reason=("Rewrites tracked documentation files in the repository, which a\n                        browser cannot do."),
        command=["{py}", "-m", "fcf_m2.workflow", "docs"],
        produces=["docs/WORKFLOW_STEPS.md"],
    ),

    # ---------------------------------------------------------------- verify
    Operation(
        id="verify-all",
        label="Run every verification gate",
        description=(
            "Runs the whole gate suite — contract rules, hash chains, cross-model constants, "
            "published-number checks, secret scan, explorer validity, Tableau and provenance. "
            "This is the check CI runs."),
        tier=TIER_DESKTOP,
        desktop_reason=(
            "Executes the full test suite and model runs on your machine. The web tier serves "
            "the result of the last CI run instead."),
        platforms=("darwin", "linux"),
        platform_reason=(
            "The gate suite is a bash script, so it does not run on a stock Windows machine. "
            "Windows users can run the same gates under WSL or Git Bash, or read the result of "
            "the last CI run — CI runs this exact script, so the answer is the same one."),
        command=["bash", "scripts/verify.sh"],
    ),
]

OPERATIONS_BY_ID: dict[str, Operation] = {op.id: op for op in OPERATIONS}


def runs_here(op: "Operation", platform: str | None = None) -> bool:
    """Whether this operation can run on the current platform.

    Separate from the tier question. A desktop-tier operation is unavailable *in a browser*;
    a platform-restricted one is unavailable *on this machine*. Conflating them would tell a
    Windows user to install the desktop app in order to run something the desktop app cannot
    run for them either.
    """
    if not op.platforms:
        return True
    current = platform or sys.platform
    return any(current.startswith(name) for name in op.platforms)


def for_tier(tier: str, platform: str | None = None) -> list[dict]:
    """What a tier shows, including what it CANNOT do and why.

    The web tier gets the whole list, not a filtered one. Hiding a capability is how a product
    quietly becomes less honest than its documentation — a reader who cannot see that
    "Run the model" exists cannot know they need the desktop app for it.
    """
    if tier not in (TIER_BOTH, TIER_DESKTOP):
        raise ValueError(f"unknown tier {tier!r}")
    out = []
    for op in OPERATIONS:
        tier_ok = tier == TIER_DESKTOP or op.tier == TIER_BOTH
        platform_ok = runs_here(op, platform)
        available = tier_ok and platform_ok
        # The tier reason and the platform reason are different facts, and the platform one is
        # reported first when both apply: telling a Windows user to install the desktop app
        # would be useless advice for an operation the desktop app cannot run there either.
        if not platform_ok:
            reason = op.platform_reason
        elif not tier_ok:
            reason = op.desktop_reason
        else:
            reason = ""
        out.append({
            "id": op.id,
            "label": op.label,
            "description": op.description,
            "available": available,
            "unavailable_reason": reason,
            "unavailable_because": ("platform" if not platform_ok
                                    else "tier" if not tier_ok else ""),
            "caveat": op.caveat,
            "produces": list(op.produces),
        })
    return out


@dataclass
class OperationResult:
    operation_id: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run(operation_id: str, repo: Path | None = None, python: str | None = None,
        timeout: int = 900) -> OperationResult:
    """Execute one operation by invoking its declared command.

    Deliberately a subprocess, not an import-and-call. The command executed here is
    character-for-character the command a person would type, which is what makes
    CLI/platform byte-equivalence a property of the design rather than a hope.
    """
    op = OPERATIONS_BY_ID.get(operation_id)
    if op is None:
        raise KeyError(f"unknown operation {operation_id!r}; known: "
                       f"{', '.join(sorted(OPERATIONS_BY_ID))}")
    root = repo or REPO
    result = subprocess.run(op.argv(python), cwd=root, capture_output=True, text=True,
                            timeout=timeout)
    return OperationResult(operation_id=op.id, returncode=result.returncode,
                           stdout=result.stdout, stderr=result.stderr)


__all__ = [
    "TIER_BOTH", "TIER_DESKTOP", "Operation", "OPERATIONS", "OPERATIONS_BY_ID",
    "for_tier", "OperationResult", "run",
]

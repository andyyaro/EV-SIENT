"""The V4 field-data loop: ingestion, capacity provenance, and trigger evaluation.

V4's claim is that the field can correct the model. These tests exist to keep that claim
honest in the specific ways it could quietly stop being true:

* an observation with no attribution upgrading a site's capacity anyway
* evidence claiming more than it supports (a walkthrough asserting `verified_utility`)
* a conflict between utility and facility values being silently resolved
* a missing trigger metric being defaulted rather than reported missing -- a defaulted
  uptime of 1.0 walks straight past the reliability gate that exists to catch it
* the pipeline shipping with real data in it

Every fixture here is synthetic and says so in its own contents.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from fcf_m2 import observed, triggers

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data/observed/fixtures"
OBSERVED = ROOT / "data/observed"

CAPACITY_FIXTURE = FIXTURES / "synthetic_capacity_observations.csv"
SESSION_FIXTURE = FIXTURES / "synthetic_session_observations.csv"


# --------------------------------------------------------------- the honesty guardrail

class TestShipsPipelineNotData:
    """V4 ships the pipeline. It must contain zero real observations."""

    def test_no_real_observations_are_committed(self):
        """Every committed observation row must be a template or a synthetic fixture."""
        import csv
        offenders = []
        for path in sorted(OBSERVED.rglob("*.csv")):
            with open(path) as fh:
                for row in csv.DictReader(fh):
                    site = (row.get("site_id") or "").strip()
                    if site and not (site.startswith("SYN") or site.startswith("EXAMPLE")):
                        offenders.append(f"{path.relative_to(ROOT)}: site_id={site}")
        assert offenders == [], (
            "real-looking site ids in committed observations:\n" + "\n".join(offenders))

    def test_fixtures_declare_themselves_synthetic(self):
        text = CAPACITY_FIXTURE.read_text()
        assert "SYNTHETIC" in text
        assert "Not an observation of any real facility" in text

    def test_templates_carry_only_an_example_row(self):
        import csv
        for name in ("observed_capacity_template.csv", "observed_sessions_template.csv"):
            with open(OBSERVED / name) as fh:
                rows = list(csv.DictReader(fh))
            assert len(rows) == 1, f"{name} should carry exactly one illustrative row"
            assert rows[0]["site_id"].startswith("EXAMPLE")


# --------------------------------------------------------------- capacity provenance

class TestCapacityObservationRefusesWhatItCannotJustify:

    def _valid(self, **overrides):
        base = dict(
            site_id="SYN001", observed_date=date(2026, 9, 1),
            method="facility_panel_schedule", source_org="SYNTHETIC facility",
            source_document="SYNTHETIC panel schedule", observer="SYNTHETIC reviewer",
            service_capacity_kw=400.0)
        base.update(overrides)
        return observed.CapacityObservation(**base)

    def test_a_valid_observation_is_accepted(self):
        assert self._valid().implied_basis == "verified_facility"

    def test_unattributed_observations_are_refused(self):
        """Rule 3: capacity_source must name the document or person, and the date."""
        with pytest.raises(observed.ObservationError, match="provenance"):
            self._valid(source_document="")
        with pytest.raises(observed.ObservationError, match="provenance"):
            self._valid(observer="   ")

    def test_an_observation_with_no_capacity_value_is_refused(self):
        with pytest.raises(observed.ObservationError, match="nothing to confirm"):
            self._valid(service_capacity_kw=None, spare_capacity_kw=None)

    def test_unknown_method_is_refused(self):
        with pytest.raises(observed.ObservationError, match="unknown method"):
            self._valid(method="someone_said_so")

    def test_negative_capacity_is_refused(self):
        with pytest.raises(observed.ObservationError, match="not a valid kW"):
            self._valid(service_capacity_kw=-10.0)

    @pytest.mark.parametrize("method,expected", [
        ("utility_service_record", "verified_utility"),
        ("utility_load_study", "verified_utility"),
        ("facility_panel_schedule", "verified_facility"),
        ("facility_walkthrough", "verified_facility"),
        ("engineering_calculation", "engineering_estimate"),
        ("comparable_site_proxy", "planning_proxy"),
    ])
    def test_evidence_caps_the_claim(self, method, expected):
        """A method can never justify a stronger basis than the evidence supports."""
        assert self._valid(method=method).implied_basis == expected

    def test_capacity_source_names_document_person_and_date(self):
        source = self._valid().capacity_source
        assert "SYNTHETIC panel schedule" in source
        assert "SYNTHETIC reviewer" in source
        assert "2026-09-01" in source


@pytest.fixture(scope="module")
def upgrades():
    obs = observed.read_capacity_observations(CAPACITY_FIXTURE)
    return observed.resolve_capacity(obs, current_basis="placeholder")


@pytest.fixture(scope="module")
def summaries():
    return observed.summarise_sessions(observed.read_session_observations(SESSION_FIXTURE))


class TestCapacityPrecedence:

    def test_facility_evidence_upgrades_off_placeholder(self, upgrades):
        assert upgrades["SYN001"].new_basis == "verified_facility"
        assert upgrades["SYN001"].upgraded

    def test_utility_beats_facility(self, upgrades):
        """Rule 1: verified_utility > verified_facility > placeholder."""
        assert upgrades["SYN002"].new_basis == "verified_utility"

    def test_conflicts_are_flagged_not_resolved(self, upgrades):
        conflicts = upgrades["SYN002"].conflicts
        assert conflicts, "a 500 vs 450 kW disagreement must be surfaced"
        assert "disagreement" in conflicts[0]
        assert "CONFLICT" in upgrades["SYN002"].capacity_source

    def test_the_conservative_value_wins_a_conflict(self, upgrades):
        """Both are kept in the source string; screening uses the lower."""
        assert upgrades["SYN002"].service_capacity_kw == 450.0

    def test_weak_evidence_does_not_claim_verification(self, upgrades):
        assert upgrades["SYN003"].new_basis == "planning_proxy"
        assert not upgrades["SYN003"].new_basis.startswith("verified")

    def test_a_weaker_observation_cannot_downgrade_a_stronger_basis(self):
        obs = [observed.CapacityObservation(
            site_id="SYN009", observed_date=date(2026, 9, 1), method="comparable_site_proxy",
            source_org="o", source_document="d", observer="r", service_capacity_kw=300.0)]
        upgrade = observed.resolve_capacity(obs, current_basis="verified_utility")["SYN009"]
        assert upgrade.new_basis == "verified_utility"
        assert not upgrade.upgraded

    def test_provenance_rows_use_the_existing_confidence_format(self):
        obs = observed.read_capacity_observations(CAPACITY_FIXTURE)
        frame = observed.observation_provenance_rows(obs)
        expected = ["site_id", "field_group", "source_class", "verification_status",
                    "source_org", "source_date", "reviewer", "assumption_type",
                    "unresolved_flag"]
        assert list(frame.columns) == expected
        assert (frame.field_group == "electrical_service").all()


# --------------------------------------------------------------- session observations

class TestSessionObservation:

    def _valid(self, **overrides):
        base = dict(site_id="SYN001", date=date(2026, 9, 1), sessions=8.0,
                    energy_kwh=76.0, mean_dwell_min=95.0, ports_in_service=4,
                    port_hours_available=47.5, port_hours_possible=48.0)
        base.update(overrides)
        return observed.SessionObservation(**base)

    def test_uptime_is_availability_over_possible(self):
        assert self._valid().uptime == pytest.approx(47.5 / 48.0)

    def test_uptime_cannot_exceed_one(self):
        with pytest.raises(observed.ObservationError, match="uptime cannot exceed 1"):
            self._valid(port_hours_available=60.0)

    def test_zero_ports_is_refused(self):
        with pytest.raises(observed.ObservationError, match="ports_in_service"):
            self._valid(ports_in_service=0)

    def test_negative_sessions_are_refused(self):
        with pytest.raises(observed.ObservationError, match="must be >= 0"):
            self._valid(sessions=-1)

    def test_utilization_is_bounded_at_one(self):
        assert self._valid(sessions=1000).utilization == 1.0


class TestSummariseRefusesToInvent:

    def test_missing_wait_is_named_not_defaulted(self):
        rows = [observed.SessionObservation(
            site_id="SYN001", date=date(2026, 9, d + 1), sessions=8.0, energy_kwh=76.0,
            mean_dwell_min=95.0, ports_in_service=4, port_hours_available=47.5,
            port_hours_possible=48.0, wait_p90_min=None) for d in range(10)]
        summary = observed.summarise_sessions(rows)["SYN001"]
        assert summary.p90_wait_min is None
        assert "p90_wait_min" in summary.missing_for_triggers
        assert not summary.sufficient_for_triggers

    def test_a_complete_site_reports_sufficient(self):
        rows = observed.read_session_observations(SESSION_FIXTURE)
        summary = observed.summarise_sessions(rows)["SYN001"]
        assert summary.sufficient_for_triggers
        assert summary.missing_for_triggers == []


# --------------------------------------------------------------- the loop itself

class TestTriggerLoop:
    """Every branch of the policy, including the ones that must refuse."""

    def _decide(self, summary, equity=0.40):
        metrics = triggers.ObservedMetrics(
            site_id=summary.site_id, months_observed=summary.months_observed,
            avg_utilization=summary.avg_utilization, p90_wait_min=summary.p90_wait_min,
            uptime=summary.uptime, equity_index_percentile=equity)
        return triggers.evaluate(metrics, ports_active=4, ports_pathway=8,
                                 site_id=summary.site_id)

    def test_sustained_demand_recommends_review(self, summaries):
        decision = self._decide(summaries["SYN001"])
        assert decision.outcome == "expand_review_recommended"

    def test_poor_reliability_holds_despite_identical_demand(self, summaries):
        """SYN002 has demand as strong as SYN001 and is held purely on uptime.

        This is the property worth protecting: the policy refuses to trust utilisation
        from chargers that were not reliably available to be used.
        """
        assert summaries["SYN002"].avg_utilization >= summaries["SYN001"].avg_utilization * 0.9
        decision = self._decide(summaries["SYN002"])
        assert decision.outcome == "hold"
        assert any("reliability gate" in t for t in decision.rule_trace)

    def test_low_demand_holds(self, summaries):
        assert self._decide(summaries["SYN003"]).outcome == "hold"

    def test_short_observation_window_holds_however_strong_the_demand(self, summaries):
        summary = summaries["SYN004"]
        assert summary.avg_utilization > 0.4, "fixture should have qualifying demand"
        decision = self._decide(summary)
        assert decision.outcome == "hold"
        assert any("minimum" in t for t in decision.rule_trace)

    def test_equity_override_lowers_the_utilisation_gate(self, summaries):
        summary = summaries["SYN005"]
        assert self._decide(summary, equity=0.40).outcome == "hold"
        boosted = self._decide(summary, equity=0.85)
        assert boosted.outcome == "expand_review_recommended"
        assert boosted.equity_override_applied

    def test_no_decision_ever_authorises_expansion(self, summaries):
        """The strongest possible outcome is a recommendation to review."""
        for summary in summaries.values():
            decision = self._decide(summary, equity=0.85)
            assert decision.outcome in {"expand_review_recommended", "hold",
                                        "awaiting_observed_data"}
            if decision.outcome == "expand_review_recommended":
                assert any("human" in t for t in decision.rule_trace)

    def test_policy_status_is_carried_on_every_decision(self, summaries):
        for summary in summaries.values():
            assert "pending" in self._decide(summary).policy_status

    def test_absent_observations_yield_awaiting_not_a_guess(self):
        decision = triggers.evaluate(None, ports_active=4, ports_pathway=8, site_id="SYN001")
        assert decision.outcome == "awaiting_observed_data"


# ============================================================ blank cells are not attribution

def _write_csv(tmp_path, columns, row):
    path = tmp_path / "obs.csv"
    path.write_text(",".join(columns) + "\n"
                    + ",".join(f'"{row.get(c, "")}"' for c in columns) + "\n")
    return path


CAPACITY_ROW = dict(
    site_id="FFX001", observed_date="2026-07-01", method="utility_load_study",
    service_capacity_kw="400", spare_capacity_kw="120", measured_peak_kw="180",
    source_org="Dominion Energy", source_document="Load study LS-2026-114",
    observer="A. Yaro", verification_status="reviewed", notes="")


@pytest.mark.parametrize("blanked", ["source_document", "observer"])
def test_a_blank_attribution_cell_is_refused_not_read_as_the_word_nan(tmp_path, blanked):
    """Regression. This defect was live for the whole life of the V4 loop.

    `__post_init__` refuses an observation whose source_document or observer is blank, because
    an unattributed record must not upgrade a site's capacity_basis. The refusal never fired:
    pandas reads a blank cell as NaN and the reader did `str(NaN).strip()`, delivering the
    four-character string 'nan' — non-empty, so the check passed.

    The result was not cosmetic. The row was accepted, reported implied_basis
    'verified_utility' (the strongest available), and produced the provenance string
    "... : nan (Dominion Energy), recorded by nan on 2026-07-01". That is the exact state the
    fail-closed capacity guard exists to prevent.
    """
    row = dict(CAPACITY_ROW, **{blanked: ""})
    path = _write_csv(tmp_path, observed.CAPACITY_COLUMNS, row)
    with pytest.raises(observed.ObservationError, match="provenance"):
        observed.read_capacity_observations(str(path))


@pytest.mark.parametrize("blanked", ["source_document", "observer"])
def test_a_whitespace_only_attribution_cell_is_also_refused(tmp_path, blanked):
    """Spaces are not attribution either, and are what a real spreadsheet actually produces."""
    row = dict(CAPACITY_ROW, **{blanked: "   "})
    path = _write_csv(tmp_path, observed.CAPACITY_COLUMNS, row)
    with pytest.raises(observed.ObservationError, match="provenance"):
        observed.read_capacity_observations(str(path))


def test_no_text_field_can_ever_arrive_as_the_string_nan(tmp_path):
    """The general form of the bug, not just the two fields that were checked.

    A blank cell in ANY text column must arrive as empty, never as 'nan'. Left unfixed,
    source_org would print 'nan' inside the provenance string that travels into the contract —
    a fabricated-looking source on a row that is otherwise legitimate.
    """
    row = dict(CAPACITY_ROW, source_org="", notes="")
    path = _write_csv(tmp_path, observed.CAPACITY_COLUMNS, row)
    observation = observed.read_capacity_observations(str(path))[0]
    for field_name in ("site_id", "method", "source_org", "source_document", "observer", "notes"):
        assert getattr(observation, field_name) != "nan", (
            f"{field_name} arrived as the literal string 'nan'")
    assert "nan" not in observation.capacity_source.split(), (
        f"the provenance string contains a bare 'nan': {observation.capacity_source!r}")


def test_an_observation_with_no_site_id_is_refused(tmp_path):
    """Unchecked this does not fail — resolve_capacity groups by site_id, so it creates a
    phantom site keyed on the empty string whose confirmed capacity belongs to nowhere."""
    path = _write_csv(tmp_path, observed.CAPACITY_COLUMNS, dict(CAPACITY_ROW, site_id=""))
    with pytest.raises(observed.ObservationError, match="site_id"):
        observed.read_capacity_observations(str(path))


# ---------------------------------------------------------------- provenance may not be upgraded

def _observation(method: str):
    import datetime
    return observed.CapacityObservation(
        site_id="S1", observed_date=datetime.date(2026, 7, 1), method=method,
        service_capacity_kw=400.0, spare_capacity_kw=120.0, measured_peak_kw=180.0,
        source_org="Org", source_document="Doc-1", observer="A. Person",
        verification_status="reviewed", notes="")


def test_a_weak_method_cannot_score_like_an_official_source():
    """The inversion this guards against actually shipped.

    `observation_provenance_rows()` mapped any basis with no same-named entry in
    SOURCE_CLASS_SCORES onto `official_source` (90). The only two bases that fall through
    are `engineering_estimate` and `planning_proxy` -- the two WEAKEST methods -- so a
    comparable-site guess scored 95 against a real utility record's 100. The module's own
    rule says an assumption can never upgrade provenance.
    """
    from fcf_m2.confidence import SOURCE_CLASS_SCORES
    strong = observed.observation_provenance_rows([_observation("utility_service_record")])
    weak = observed.observation_provenance_rows([_observation("comparable_site_proxy")])
    calc = observed.observation_provenance_rows([_observation("engineering_calculation")])

    strong_score = SOURCE_CLASS_SCORES[strong.iloc[0].source_class]
    for frame, label in ((weak, "comparable_site_proxy"), (calc, "engineering_calculation")):
        score = SOURCE_CLASS_SCORES[frame.iloc[0].source_class]
        assert score < strong_score, (
            f"{label} scored {score} against a verified utility record's {strong_score}")
        assert score <= 35, f"{label} scored {score}; a reasoned estimate is not evidence"


def test_an_unmapped_basis_is_refused_rather_than_defaulted():
    """A default is what caused the inversion. An unknown basis must stop the run."""
    obs = _observation("utility_service_record")
    object.__setattr__(obs, "method", "some_future_method")
    observed.METHOD_TO_BASIS["some_future_method"] = "a_basis_nobody_scored"
    try:
        with pytest.raises(observed.ObservationError, match="no source class"):
            observed.observation_provenance_rows([obs])
    finally:
        observed.METHOD_TO_BASIS.pop("some_future_method", None)

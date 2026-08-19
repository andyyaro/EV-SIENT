"""NFC tag payloads: the encoding, and the refusals that matter more than the encoding.

A tag is a physical object left in public space carrying a county's implicit endorsement.
The encoding either works or it visibly does not; the dangerous failures are the quiet
ones, so most of these tests are about what the generator **refuses**:

* a URL on a host we do not control
* a plaintext http URL
* a payload that would not fit the hardware
* a site id the contract does not contain -- a tag pointing at a 404 in a car park

The NDEF byte layout is asserted exactly, byte by byte, because "it fits" and "it decodes"
are things to establish at a desk rather than while standing in a parking lot with a phone.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fcf_m2 import nfc

ROOT = Path(__file__).resolve().parents[1]


class TestUriPrefixAbbreviation:
    """NDEF abbreviates common prefixes to one byte. Getting this wrong wastes memory."""

    @pytest.mark.parametrize("url,code,remainder", [
        ("https://example.com/x", 0x04, b"example.com/x"),
        ("https://www.example.com/x", 0x02, b"example.com/x"),
        ("http://example.com/x", 0x03, b"example.com/x"),
        ("http://www.example.com/x", 0x01, b"example.com/x"),
        ("ftp://example.com", 0x00, b"ftp://example.com"),
    ])
    def test_longest_matching_prefix_wins(self, url, code, remainder):
        assert nfc.encode_uri_payload(url) == (code, remainder)

    def test_www_beats_bare_https(self):
        """https://www. is 0x02, not 0x04 plus a literal www. -- four bytes saved."""
        code, remainder = nfc.encode_uri_payload("https://www.a.com")
        assert code == 0x02
        assert b"www" not in remainder


class TestNdefEncoding:

    def test_exact_byte_layout(self):
        raw = nfc.encode_ndef("https://a.co/t/X")
        assert raw[0] == 0x03, "NDEF Message TLV type"
        assert raw[1] == len(raw) - 3, "TLV length excludes type, length and terminator"
        assert raw[2] == 0xD1, "MB|ME|SR, TNF=well-known"
        assert raw[3] == 0x01, "type length"
        assert raw[5] == 0x55, "record type 'U'"
        assert raw[6] == 0x04, "https:// prefix code"
        assert raw[-1] == 0xFE, "terminator TLV"

    def test_payload_length_field_is_correct(self):
        raw = nfc.encode_ndef("https://a.co/t/X")
        declared = raw[4]
        # total = TLV type+len (2) + header (4: D1 01 len 55) + payload + terminator (1)
        payload_bytes = len(raw) - 2 - 4 - 1
        assert declared == payload_bytes
        assert payload_bytes == 1 + len(b"a.co/t/X")  # URI code + remainder

    def test_round_trips_to_the_original_url(self):
        url = "https://futurecityfellowship.andyyaro.com/t/FFX002"
        raw = nfc.encode_ndef(url)
        code = raw[6]
        recovered = nfc.URI_PREFIXES[code] + raw[7:-1].decode()
        assert recovered == url

    def test_an_over_long_uri_is_refused_not_silently_truncated(self):
        with pytest.raises(nfc.TagError, match="long TLV form"):
            nfc.encode_ndef("https://a.co/" + "x" * 300)


class TestSafetyRefusals:
    """The generator enforces these, rather than trusting a runbook to."""

    def test_a_host_we_do_not_control_is_refused(self):
        with pytest.raises(nfc.TagError, match="allowlist"):
            nfc.build_payload("FFX002", "X", base="https://example.com")

    def test_a_lookalike_host_is_refused(self):
        """andyyaro.com.evil.test ends with an allowed string and is not allowed."""
        with pytest.raises(nfc.TagError, match="allowlist"):
            nfc.build_payload("FFX002", "X", base="https://andyyaro.com.evil.test")

    def test_plaintext_http_is_refused(self):
        with pytest.raises(nfc.TagError, match="not https"):
            nfc.build_payload("FFX002", "X", base="http://andyyaro.com")

    def test_the_allowlist_contains_only_controlled_hosts(self):
        for host in nfc.ALLOWED_HOSTS:
            assert host.endswith("andyyaro.com"), f"{host} is not a controlled domain"


@pytest.fixture(scope="module")
def payloads():
    return nfc.payloads_from_contract(ROOT / "data/contract/v1")


class TestPayloadsFromContract:
    """Derived from the contract, never typed by hand."""

    def test_one_payload_per_contract_site(self, payloads):
        assert len(payloads) == 12

    def test_site_ids_match_the_contract_exactly(self, payloads):
        import pandas as pd
        expected = set(pd.read_csv(ROOT / "data/contract/v1/site_table.csv").site_id)
        assert {p.site_id for p in payloads} == expected

    def test_every_payload_fits_with_room_to_spare(self, payloads):
        for p in payloads:
            assert p.fits
            assert p.bytes_free > 100, (
                f"{p.site_id} leaves only {p.bytes_free} bytes; a longer path would not fit")

    def test_every_url_is_https_on_a_controlled_host(self, payloads):
        for p in payloads:
            assert p.url.startswith("https://")
            host = p.url.split("://", 1)[1].split("/", 1)[0]
            assert host in nfc.ALLOWED_HOSTS

    def test_no_payload_carries_anything_personal(self, payloads):
        """A tag carries a site id and nothing else. No person, no credential, no token."""
        for p in payloads:
            body = p.ndef_bytes.decode("utf-8", "ignore").lower()
            for forbidden in ("token", "key=", "auth", "user", "email", "@", "password",
                              "session", "id_token", "bearer"):
                assert forbidden not in body, f"{p.site_id} payload contains {forbidden!r}"

    def test_urls_are_unique_per_site(self, payloads):
        urls = [p.url for p in payloads]
        assert len(urls) == len(set(urls))

    def test_payload_is_deterministic(self, payloads):
        """The same site must produce the same bytes every time, or verification is moot."""
        again = nfc.payloads_from_contract(ROOT / "data/contract/v1")
        assert {p.site_id: p.hex for p in payloads} == {p.site_id: p.hex for p in again}

    def test_summary_table_has_what_the_runbook_needs(self, payloads):
        frame = nfc.summary_table(payloads)
        assert list(frame.columns) == [
            "site_id", "site_name", "url", "ndef_bytes", "bytes_free", "ndef_hex"]
        assert len(frame) == 12


# --------------------------------------------------------------- the landing pages

LANDING = ROOT / "site/nfc-landing"


@pytest.fixture(scope="module")
def contract():
    import pandas as pd
    return (pd.read_csv(ROOT / "data/contract/v1/site_table.csv"),
            pd.read_csv(ROOT / "data/contract/v1/scenario_table.csv"))


class TestLandingPages:
    """The page a stranger reaches by tapping a coin in a car park.

    Two obligations, both met rather than traded: it must be readable by someone with no
    context on a phone, and it must not read as more certain than the data supports.
    """

    def test_no_extension_bearing_files_remain(self):
        """A .html twin beside an extensionless file is a second copy nothing serves."""
        strays = [p.name for p in LANDING.iterdir() if p.suffix]
        assert strays == [], f"extension-bearing strays would go unserved: {strays}"

    def test_every_tag_url_resolves_to_a_page(self, payloads):
        for p in payloads:
            slug = p.url.rsplit("/", 1)[-1]
            # The file name matches the URL byte for byte, deliberately: a URL that has
            # to be rewritten at the edge to find its own file is a URL with a moving part.
            assert (LANDING / slug).exists(), f"{p.site_id}: tag points at a 404"

    @pytest.mark.parametrize("site_id", [
        "FFX001", "FFX002", "FFX003", "FFX004",
        "PWC001", "PWC002", "PWC003", "PWC004", "PWC005", "PWC006", "PWC007", "PWC008"])
    def test_numbers_trace_to_the_contract(self, site_id, contract):
        _, scen = contract
        row = scen[(scen.site_id == site_id) & (scen.horizon_year == 2026)].iloc[0]
        page = (LANDING / site_id).read_text()
        assert f"<dd>{int(row.ports_active)}</dd>" in page
        assert f"<dd>up to {int(row.ports_pathway_capacity)}</dd>" in page
        assert f"<dd>{row.data_confidence}</dd>" in page

    @staticmethod
    def _rendered_text(path: Path) -> str:
        """Visible text, with tags removed - a caveat split by <strong> is still said."""
        import html as html_mod
        import re
        raw = path.read_text()
        raw = re.sub(r"(?s)<(script|style).*?</\1>", "", raw)
        text = html_mod.unescape(re.sub(r"<[^>]+>", " ", raw))
        return re.sub(r"\s+", " ", text)

    @pytest.mark.parametrize("caveat", [
        "Nothing is being built here",
        "No charger has been approved, funded",
        "placeholder",
        "all twelve",
        "cannot approve, permit, or fund anything",
        "modelled, not measured",
        "never budgets or quotes",
    ])
    def test_the_caveats_survive_the_plain_language(self, caveat):
        """Friendlier framing, identical epistemics. Warm copy must not soften a limit."""
        text = self._rendered_text(LANDING / "FFX002")
        assert caveat in text, f"the landing page no longer says: {caveat}"

    def test_placeholder_capacity_is_stated_as_unconfirmed(self, contract):
        _, scen = contract
        for site_id in scen.site_id.unique():
            row = scen[(scen.site_id == site_id) & (scen.horizon_year == 2026)].iloc[0]
            page = (LANDING / site_id).read_text()
            if row.capacity_basis == "placeholder":
                assert "No - placeholder" in page, f"{site_id} does not say capacity is unconfirmed"

    def test_no_page_claims_a_confidence_the_data_lacks(self, contract):
        _, scen = contract
        for site_id in scen.site_id.unique():
            page = (LANDING / site_id).read_text()
            assert "<dd>High</dd>" not in page, f"{site_id} claims High confidence"

    def test_pages_collect_nothing_personal(self):
        """A page reached by tapping a coin must not ask who you are."""
        for path in sorted(p for p in LANDING.iterdir() if p.is_file()):
            page = path.read_text().lower()
            for forbidden in ("<input", "<form", "cookie", "localstorage", "analytics.js"):
                assert forbidden not in page, f"{path.name} contains {forbidden!r}"

    def test_pages_are_mobile_and_accessible(self):
        for path in sorted(p for p in LANDING.iterdir() if p.is_file()):
            page = path.read_text()
            assert 'name="viewport"' in page
            assert 'lang="en"' in page
            assert page.count("<h1") == 1, f"{path.name} should have exactly one h1"
            assert "prefers-reduced-motion" in page
            assert "focus-visible" in page
            assert "prefers-color-scheme" in page

    def test_pages_are_regenerated_not_hand_edited(self):
        """A page that drifts from the generator is a page nobody can regenerate."""
        import subprocess, sys
        before = {p.name: p.read_text() for p in sorted(LANDING.iterdir()) if p.is_file()}
        subprocess.run([sys.executable, str(ROOT / "scripts/build_nfc_landing.py")],
                       cwd=ROOT, capture_output=True, check=True)
        after = {p.name: p.read_text() for p in sorted(LANDING.iterdir()) if p.is_file()}
        assert before == after, "landing pages differ from a fresh build - were they hand-edited?"


CAPTURE = ROOT / "site/nfc-capture"


class TestCaptureForm:
    """The form that turns a site visit into a capacity confirmation.

    This is the mechanism that closes limitation #1, so the property that matters is that a
    row it produces actually ingests -- a form whose output the model rejects would be a
    dead end that looks like a feature.
    """

    def test_one_form_per_site(self):
        assert len([p for p in CAPTURE.iterdir() if p.is_file()]) == 12

    def test_every_landing_page_links_to_a_form_that_exists(self, payloads):
        for p in payloads:
            page = (LANDING / p.site_id).read_text()
            assert f'href="/f/{p.site_id}"' in page
            assert (CAPTURE / p.site_id).exists(), f"{p.site_id} links to a form that is missing"

    def test_form_columns_match_the_ingestion_schema_exactly(self):
        """If these drift, a submitted row stops ingesting and nobody finds out."""
        from fcf_m2 import observed
        page = (CAPTURE / "FFX002").read_text()
        for column in observed.CAPACITY_COLUMNS:
            assert f'"{column}"' in page, f"the form does not emit {column}"

    def test_a_row_the_form_produces_ingests_and_upgrades(self):
        """End to end: the exact CSV the browser assembles, through the real ingestion."""
        import csv, io, tempfile, os
        from fcf_m2 import observed
        row = {
            "site_id": "FFX002", "observed_date": "2026-09-15",
            "method": "facility_panel_schedule", "service_capacity_kw": "400",
            "spare_capacity_kw": "120", "measured_peak_kw": "280",
            "source_org": "Test Facilities", "source_document": "panel schedule PS-3",
            "observer": "Test Manager", "verification_status": "reviewed",
            "notes": "spare breaker positions: 6",
        }
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=observed.CAPACITY_COLUMNS, lineterminator="\n")
        writer.writeheader(); writer.writerow(row)
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fh:
            fh.write(buf.getvalue()); path = fh.name
        try:
            obs = observed.read_capacity_observations(path)
            assert len(obs) == 1
            assert obs[0].implied_basis == "verified_facility"
            upgrade = observed.resolve_capacity(obs, current_basis="placeholder")["FFX002"]
            assert upgrade.upgraded
            assert upgrade.new_basis == "verified_facility"
        finally:
            os.unlink(path)

    def test_the_form_posts_nowhere(self):
        """No endpoint means no public write path into the model, and nothing to breach.

        Checks for actual *use*, not for the words. The page's own privacy copy says it
        "sets no cookie", and a substring search for "cookie" reads that as evidence it
        does -- the same text-versus-meaning trap as the secret scan and the link checker.
        """
        import re
        forbidden = {
            "form submission": re.compile(r"<form[^>]*\baction\s*=", re.I),
            "POST method": re.compile(r"\bmethod\s*=\s*[\"\']post", re.I),
            "fetch call": re.compile(r"\bfetch\s*\("),
            "XHR": re.compile(r"\bXMLHttpRequest\b"),
            "cookie write": re.compile(r"document\s*\.\s*cookie"),
            "local storage": re.compile(r"\b(?:local|session)Storage\s*\."),
            "beacon": re.compile(r"navigator\s*\.\s*sendBeacon"),
        }
        for path in sorted(p for p in CAPTURE.iterdir() if p.is_file()):
            page = path.read_text()
            for label, pattern in forbidden.items():
                assert not pattern.search(page), f"{path.name} performs a {label}"

    def test_the_form_explains_why_it_asks_who_you_are(self):
        page = (CAPTURE / "FFX002").read_text()
        assert "cannot be used to upgrade" in page
        assert "only person-shaped information collected" in page

    def test_the_form_is_not_indexed(self):
        """A per-site data-entry page should not turn up in a search result."""
        for path in sorted(p for p in CAPTURE.iterdir() if p.is_file()):
            assert 'name="robots" content="noindex"' in path.read_text()

    def test_forms_are_regenerated_not_hand_edited(self):
        import subprocess, sys
        before = {p.name: p.read_text() for p in sorted(CAPTURE.iterdir()) if p.is_file()}
        subprocess.run([sys.executable, str(ROOT / "scripts/build_capture_form.py")],
                       cwd=ROOT, capture_output=True, check=True)
        after = {p.name: p.read_text() for p in sorted(CAPTURE.iterdir()) if p.is_file()}
        assert before == after, "capture forms differ from a fresh build - hand-edited?"

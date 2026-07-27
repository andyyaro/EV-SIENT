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

"""NFC tag payloads, derived from the contract.

The hardware is 50 NTAG215 coins: NFC Forum Type 2, ISO/IEC 14443 Type A, **~504 bytes of
user-writable memory**. That is enough for a URL and nothing else, which decides the design
before anything else does — the tag is a pointer, never a payload.

What a tag carries, and what it must never carry
------------------------------------------------
A tag carries one site-scoped URL on a domain we control. It carries **no personal data, no
identifier for any person, no credential, and nothing that grants access**. An unlocked NDEF
tag is rewritable by anyone with a phone, so a tag implying a county's endorsement and
pointing at a phishing URL is a real liability — which is why every tag is locked or
password-protected before deployment and why the URL host is checked against an allowlist
here, in code, rather than trusted to a runbook.

Byte budgeting
--------------
NDEF URI records abbreviate common prefixes to a single byte: ``https://`` is 0x04. The
full on-tag encoding is computed exactly rather than estimated, because "it fits" is not
something to find out while standing in a car park.

Why the URL is short
--------------------
``/t/<SITE_ID>`` rather than a descriptive path. Every byte spent on prose is a byte
unavailable to the site id, and the human-readable name belongs on the printed card beside
the tag, where it costs nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- constants

#: NTAG215 user-writable memory. The datasheet figure is ~504 bytes (126 pages x 4).
NTAG215_USER_BYTES = 504

#: NDEF URI identifier codes (NFC Forum URI Record Type Definition, table 3).
URI_PREFIXES: dict[int, str] = {
    0x00: "",
    0x01: "http://www.",
    0x02: "https://www.",
    0x03: "http://",
    0x04: "https://",
}

#: Hosts a tag may point at. Anything else is refused, in code.
#: A tag is a physical object in public space that carries an implicit endorsement; it may
#: only ever send someone to infrastructure this project controls.
ALLOWED_HOSTS = frozenset({
    "futurecityfellowship.andyyaro.com",
    "andyyaro.com",
})

#: The deployed base. Chosen over a new domain deliberately: this host already has a
#: CloudFront distribution, an ACM certificate and a Route 53 record, so NFC routes add no
#: recurring cost against the program's $10/month ceiling.
DEFAULT_BASE = "https://futurecityfellowship.andyyaro.com"

#: Path prefix for a site landing page. Short on purpose -- see the module docstring.
SITE_PATH = "/t/"


class TagError(ValueError):
    """Raised when a payload would be unsafe or would not fit. Never a warning."""


# --------------------------------------------------------------------------- encoding

def encode_uri_payload(url: str) -> tuple[int, bytes]:
    """Return the NDEF URI identifier code and the remaining URI bytes.

    Picks the longest matching prefix, because a longer abbreviation saves more bytes.
    """
    best_code, best_prefix = 0x00, ""
    for code, prefix in URI_PREFIXES.items():
        if prefix and url.startswith(prefix) and len(prefix) > len(best_prefix):
            best_code, best_prefix = code, prefix
    return best_code, url[len(best_prefix):].encode("utf-8")


def encode_ndef(url: str) -> bytes:
    """The exact byte sequence written to the tag, including TLV framing.

    Layout, per NFC Forum Type 2 Tag and the URI RTD:

    ===========================  ============================================
    ``03 <len>``                 NDEF Message TLV: type, then length
    ``D1``                       record header: MB=1, ME=1, SR=1, TNF=0x01
    ``01``                       type length (1 byte: 'U')
    ``<payload len>``            1 (URI code) + len(remainder)
    ``55``                       record type 'U' (URI)
    ``<uri code>``               e.g. 0x04 for https://
    ``<remainder>``              the rest of the URL, UTF-8
    ``FE``                       Terminator TLV
    ===========================  ============================================
    """
    code, remainder = encode_uri_payload(url)
    payload = bytes([code]) + remainder
    # The bound is on the RECORD, not the payload. The record is
    # `bytes([0xD1, 0x01, len(payload), 0x55]) + payload` -- four header bytes -- and the
    # single-byte NDEF TLV length form tops out at 254. So the real limit is a payload of
    # 250. Guarding at `payload > 254` let payloads of 251-254 through, producing records of
    # 255-258 that the single-byte form cannot express: exactly the untested long-form branch
    # the refusal exists to avoid. Off by the four header bytes.
    RECORD_HEADER_BYTES = 4
    MAX_SINGLE_BYTE_TLV = 254
    if len(payload) + RECORD_HEADER_BYTES > MAX_SINGLE_BYTE_TLV:
        raise TagError(
            f"URI payload is {len(payload)} bytes, making a "
            f"{len(payload) + RECORD_HEADER_BYTES}-byte record, which needs the long TLV form "
            f"this encoder does not implement (single-byte form maxes at "
            f"{MAX_SINGLE_BYTE_TLV}). Shorten the URL.")
    record = bytes([0xD1, 0x01, len(payload), 0x55]) + payload
    return bytes([0x03, len(record)]) + record + bytes([0xFE])


# --------------------------------------------------------------------------- payloads

@dataclass(frozen=True)
class TagPayload:
    """Exactly what goes on one tag, plus what gets printed beside it."""

    site_id: str
    site_name: str
    url: str
    ndef_bytes: bytes
    label: str

    @property
    def byte_count(self) -> int:
        return len(self.ndef_bytes)

    @property
    def bytes_free(self) -> int:
        return NTAG215_USER_BYTES - self.byte_count

    @property
    def fits(self) -> bool:
        return self.byte_count <= NTAG215_USER_BYTES

    @property
    def hex(self) -> str:
        return " ".join(f"{b:02X}" for b in self.ndef_bytes)


def _validate_url(url: str) -> None:
    if not url.startswith("https://"):
        raise TagError(
            f"{url!r} is not https. A tag in public space must not send anyone to a "
            f"plaintext URL.")
    host = url.split("://", 1)[1].split("/", 1)[0].lower()
    if host not in ALLOWED_HOSTS:
        raise TagError(
            f"host {host!r} is not in the allowlist {sorted(ALLOWED_HOSTS)}. Tags may only "
            f"point at infrastructure this project controls.")


def build_payload(site_id: str, site_name: str, base: str = DEFAULT_BASE) -> TagPayload:
    """One tag's payload for one site. Refuses anything unsafe or oversized."""
    url = f"{base.rstrip('/')}{SITE_PATH}{site_id}"
    _validate_url(url)
    ndef = encode_ndef(url)
    payload = TagPayload(site_id=site_id, site_name=site_name, url=url,
                         ndef_bytes=ndef, label=f"{site_id} — {site_name}")
    if not payload.fits:
        raise TagError(
            f"{site_id}: {payload.byte_count} bytes exceeds the NTAG215 user memory of "
            f"{NTAG215_USER_BYTES} bytes.")
    return payload


def payloads_from_contract(contract_dir: str | Path = "data/contract/v1",
                           base: str = DEFAULT_BASE) -> list[TagPayload]:
    """Every site's payload, read from the contract.

    Derived, never typed by hand: a tag pointing at a site id the contract does not
    contain is a tag pointing at a 404 in a car park.
    """
    site_table = pd.read_csv(Path(contract_dir) / "site_table.csv")
    name_column = ("site_name_display" if "site_name_display" in site_table.columns
                   else "site_name")
    return [build_payload(str(row.site_id), str(getattr(row, name_column)), base)
            for row in site_table.itertuples()]


def summary_table(payloads: list[TagPayload]) -> pd.DataFrame:
    """One row per tag: what to write, how big it is, what to print."""
    return pd.DataFrame([{
        "site_id": p.site_id,
        "site_name": p.site_name,
        "url": p.url,
        "ndef_bytes": p.byte_count,
        "bytes_free": p.bytes_free,
        "ndef_hex": p.hex,
    } for p in payloads])


__all__ = [
    "NTAG215_USER_BYTES", "URI_PREFIXES", "ALLOWED_HOSTS", "DEFAULT_BASE", "SITE_PATH",
    "TagError", "TagPayload",
    "encode_uri_payload", "encode_ndef", "build_payload", "payloads_from_contract",
    "summary_table",
]

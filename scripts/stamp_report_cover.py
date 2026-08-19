#!/usr/bin/env python3
"""Prepend a superseded-notice cover page to the public planning-report PDF.

Why the label had to go INSIDE the document
-------------------------------------------
`site/www/reports/Public_EV_Charging_Planning_Report.pdf` is served publicly, generated
2026-06-28, and its page 3 is headed **"Current Site Ranking"** while publishing all twelve
`legacy_v2` scores with no model mode named anywhere. The linking page on `results.html` was
annotated first - but the PDF is **independently addressable**: it has its own URL and a direct
"open the PDF directly" link, so a warning living on the linking page does not travel with the
file when someone shares it. A reader who arrives at the URL sees "the latest run" and "the
strongest current planning signal" with no correction in sight.

No generator for this report exists in this repository, so it cannot be rebuilt from the
canonical contract here. The owner's decision (open action 8d) was to **stamp it and keep it as
a dated artifact** rather than withdraw it. This script is that stamp.

Why it is not a build step
--------------------------
It needs `qpdf`, which the CI runners do not have, and it modifies a tracked binary. So it runs
**by hand**, once, and its output is committed - the same treatment as `scripts/vendor_cesium.sh`.
Re-running it on an already-stamped file is refused rather than silently producing two covers.

The cover page itself is written here in raw PDF with **no dependencies at all**: one page, US
Letter to match the original's MediaBox, base-14 Helvetica so nothing needs embedding. Adding a
PDF library to the locked requirements for a one-off cover would cost more than it is worth.

    python scripts/stamp_report_cover.py            # stamp in place
    python scripts/stamp_report_cover.py --check    # is it stamped? changes nothing
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORT = REPO / "site/www/reports/Public_EV_Charging_Planning_Report.pdf"

#: Present on the cover and nowhere else, so `--check` can tell stamped from unstamped.
SENTINEL = "SUPERSEDED - READ BEFORE USING ANY FIGURE"

PAGE_W, PAGE_H = 612, 792

#: (text, font, size, y, indent). Every figure here is checked by tests/test_report_cover.py
#: against the canonical fixture, so the cover cannot drift from the model it corrects.
LINES = [
    (SENTINEL, "F2", 15, 720, 56),
    ("", "F1", 11, 700, 56),
    ("This report was generated 2026-06-28 from the legacy_v2 baseline model.", "F1", 11, 686, 56),
    ("Its rankings have since been superseded.", "F1", 11, 668, 56),
    ("", "F1", 11, 650, 56),
    ("What changed", "F2", 12, 636, 56),
    ("Page 3 of this report is headed \"Current Site Ranking\" and lists FFX002 -", "F1", 11, 618, 56),
    ("City of Fairfax Regional Library first at 58.8. That is the legacy_v2 result.", "F1", 11, 602, 56),
    ("", "F1", 11, 586, 56),
    ("Under the canonical model (milestone2_v3), the strongest candidate is", "F1", 11, 572, 56),
    ("FFX004 - Fairfax County Government Center at 53.4, with FFX002 second", "F1", 11, 556, 56),
    ("at 51.8. The two modes are not interchangeable, and this report names", "F1", 11, 540, 56),
    ("neither of them.", "F1", 11, 524, 56),
    ("", "F1", 11, 508, 56),
    ("What has not changed", "F2", 12, 490, 56),
    ("Neither ranking is a feasibility finding. Electrical capacity is an unverified", "F1", 11, 472, 56),
    ("placeholder at all twelve sites - nobody has confirmed that the service at", "F1", 11, 456, 56),
    ("any site could support chargers. All twelve sites score Low data confidence;", "F1", 11, 440, 56),
    ("none reaches Medium. Costs are screening estimates, never budgets, and", "F1", 11, 424, 56),
    ("demand is modelled, not measured.", "F1", 11, 408, 56),
    ("", "F1", 11, 392, 56),
    ("This report remains published as a dated record of the 2026-06-28 run.", "F1", 11, 374, 56),
    ("It is not current model output and should not be cited as such.", "F1", 11, 358, 56),
    ("", "F1", 11, 342, 56),
    ("Cover added 2026-07-28. The eight pages that follow are unaltered.", "F1", 9.5, 96, 56),
    ("Future City Fellowship - George Mason University - planning support only.", "F1", 9.5, 82, 56),
]


def escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def cover_pdf() -> bytes:
    """A one-page US Letter PDF, written by hand. No dependencies."""
    parts = []
    for text, font, size, y, x in LINES:
        if not text:
            continue
        parts.append(f"BT /{font} {size} Tf {x} {y} Td ({escape(text)}) Tj ET")
    # A rule under the heading, so the notice reads as a stamp rather than a paragraph.
    parts.append(f"0.7 w 56 710 m {PAGE_W - 56} 710 l S")
    stream = "\n".join(parts).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
         f"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>").encode(),
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n").encode()
    return bytes(out)


#: The report had exactly this many pages before stamping. One more means a cover is present.
ORIGINAL_PAGES = 8


def page_count(path: Path) -> int:
    """Pages, read from the page-tree `/Count` in the raw bytes. No tooling required.

    A raw scan for the cover TEXT does not work and was wrong in the first version of this
    script: qpdf compresses content streams, so the words on the cover do not appear as
    plaintext anywhere in the file. `/Count` is not compressed, so it survives. Its own test
    caught the mistake, which is the argument for writing the test.
    """
    counts = [int(m) for m in re.findall(rb"/Count\s+(\d+)", path.read_bytes())]
    return max(counts) if counts else 0


def is_stamped(path: Path) -> bool:
    """True if a cover page is present.

    Prefers extracted text, which names the sentinel exactly. Falls back to the page count,
    which needs nothing installed -- CI has no PDF tooling at all.
    """
    result = subprocess.run(["mutool", "draw", "-F", "txt", str(path), "1"],
                            capture_output=True, text=True)
    if result.returncode == 0:
        return SENTINEL in result.stdout
    return page_count(path) > ORIGINAL_PAGES


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true",
                        help="report whether the report is stamped; change nothing")
    args = parser.parse_args()

    if not REPORT.is_file():
        print(f"missing: {REPORT.relative_to(REPO)}")
        return 1

    stamped = is_stamped(REPORT)
    if args.check:
        print(f"{'stamped' if stamped else 'NOT STAMPED'}: {REPORT.relative_to(REPO)}")
        return 0 if stamped else 1

    if stamped:
        print("already stamped; refusing to add a second cover")
        return 0

    if not shutil.which("qpdf"):
        print("qpdf is required to merge the cover and is not installed.\n"
              "  macOS:  brew install qpdf\n"
              "This script is deliberately not part of CI for that reason.")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        cover = Path(tmp) / "cover.pdf"
        merged = Path(tmp) / "merged.pdf"
        cover.write_bytes(cover_pdf())
        result = subprocess.run(
            ["qpdf", "--empty", "--pages", str(cover), str(REPORT), "--", str(merged)],
            capture_output=True, text=True)
        if result.returncode not in (0, 3):      # 3 == warnings only
            print(f"qpdf failed: {result.stderr.strip()}")
            return 1
        shutil.copyfile(merged, REPORT)

    pages = subprocess.run(["qpdf", "--show-npages", str(REPORT)],
                           capture_output=True, text=True).stdout.strip()
    print(f"stamped: {REPORT.relative_to(REPO)} is now {pages} pages "
          f"(1 cover + 8 unaltered)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

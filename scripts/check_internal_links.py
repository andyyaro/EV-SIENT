"""Check that every relative Markdown link/image in the repository resolves to a real file.

Used by scripts/verify.sh and CI when lychee is unavailable. External (http) links are
skipped offline; anchors are ignored.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")

problems = []
for md in REPO.rglob("*.md"):
    if ".git" in md.parts or "venv" in md.parts or "data/outputs" in str(md):
        continue
    for target in LINK.findall(md.read_text(errors="ignore")):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path = target.split("#")[0]
        if not path:
            continue
        resolved = (md.parent / path).resolve()
        if not resolved.exists():
            problems.append(f"{md.relative_to(REPO)} -> {target}")

if problems:
    print("BROKEN RELATIVE LINKS:")
    print("\n".join(problems))
    sys.exit(1)
print(f"internal links OK ({REPO})")

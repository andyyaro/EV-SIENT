"""Refuse the wrong Tableau URL form anywhere the project embeds or shows a view.

Two forms exist and they are not interchangeable:

* ``public.tableau.com/views/<workbook>/<Sheet>`` — the **share / embed** form, what
  Tableau's own Share button produces, and what an ``<iframe>`` needs.
* ``public.tableau.com/app/profile/<profile>/viz/<workbook>/<Sheet>`` — the profile-app
  page route. Fine for a human clicking through, wrong inside an embed.

Both return HTTP 200 and both return the same ~1.4 KB JavaScript shell, because Tableau
Public is a single-page app — so nothing about a status check will catch the mistake, and an
embed built on the page form fails in a way that looks like a rendering problem rather than a
wrong URL.

This gate exists because the wrong form was written into two documents first, and only the
project owner catching it stopped it propagating into the website and the platform.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

#: Where an embed could plausibly be written.
SEARCH_GLOBS = ("**/*.html", "**/*.md", "**/*.js", "**/*.py")

SKIP_DIRS = {"venv", "node_modules", ".git", "__pycache__", "Build"}

PAGE_FORM = re.compile(r"public\.tableau\.com/app/profile/[^\s)\"'<>]+")
EMBED_CONTEXT = re.compile(r"(?i)<iframe|src\s*=|embed|tableau-viz")

#: Files allowed to mention the page form, because they document the DIFFERENCE.
ALLOWED = {
    "dashboard/tableau/EMBED.md",
    "dashboard/tableau/CAPABILITY_GAP.md",
    "docs/operations/v4-program/TABLEAU_MCP_FEEDBACK.md",
    "docs/operations/v4-program/LEDGER.md",
    "docs/operations/v4-program/DECISIONS.md",
    "scripts/check_tableau_embeds.py",
}


def main() -> int:
    problems: list[str] = []
    checked = 0
    for pattern in SEARCH_GLOBS:
        for path in REPO.glob(pattern):
            if any(part in SKIP_DIRS for part in path.parts) or not path.is_file():
                continue
            rel = str(path.relative_to(REPO))
            if rel in ALLOWED:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            checked += 1
            for lineno, line in enumerate(text.splitlines(), 1):
                if PAGE_FORM.search(line) and EMBED_CONTEXT.search(line):
                    problems.append(
                        f"{rel}:{lineno}: embeds the PAGE form; use the /views/ share form "
                        f"-> {line.strip()[:100]}")

    if problems:
        print("TABLEAU EMBED PROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"tableau embeds OK ({checked} files scanned; no page-form URL used as an embed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

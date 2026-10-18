"""Check that every relative Markdown link/image in the repository resolves to a real file.

Used by scripts/verify.sh and CI when lychee is unavailable. External (http) links are
skipped offline; anchors are ignored.

Code is not prose: text inside a fenced code block or an inline code span is a *quotation*
of link syntax, not a link, and Markdown renderers do not linkify it. This checker masks
both before matching so it agrees with lychee, which parses Markdown properly. Without that,
any document that legitimately quotes a link -- a style guide, a patch guide, the Phase 0
inventory -- fails the gate for saying the word rather than doing the thing.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")

FENCE = re.compile(r"(?ms)^[ \t]*(`{3,}|~{3,}).*?^[ \t]*\1[ \t]*$")
INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)", re.S)


def strip_code(text: str) -> str:
    """Blank out code blocks and code spans, preserving offsets and line structure."""
    def blank(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))

    return INLINE_CODE.sub(blank, FENCE.sub(blank, text))


def broken_links() -> list[str]:
    problems = []
    for md in sorted(REPO.rglob("*.md")):
        # node_modules holds installed packages' own docs (platform/app), not ours.
        if (".git" in md.parts or "venv" in md.parts or "node_modules" in md.parts
                or "data/outputs" in str(md)):
            continue
        text = strip_code(md.read_text(errors="ignore"))
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#")[0]
            if not path:
                continue
            if not (md.parent / path).resolve().exists():
                problems.append(f"{md.relative_to(REPO)} -> {target}")
    return problems


if __name__ == "__main__":
    problems = broken_links()
    if problems:
        print("BROKEN RELATIVE LINKS:")
        print("\n".join(problems))
        sys.exit(1)
    print(f"internal links OK ({REPO})")

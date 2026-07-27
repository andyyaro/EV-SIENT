"""The web tier is wired to what exists, computes nothing, and never drops its caveats.

The web tier is the PRIMARY distribution — most readers will only ever see this. So the
failures that matter are the quiet ones: a selector pointing at an element that was renamed,
a fetch for a file that was moved, an arithmetic helper that turns the page into a second
source of truth, or a caveat that got tidied away in a redesign.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fcf_m2 import operations as ops  # noqa: E402

WEB = REPO / "site/platform"
HTML = WEB / "index.html"
JS = WEB / "app.js"
CSS = WEB / "styles.css"


@pytest.fixture(scope="module")
def html() -> str:
    return HTML.read_text()


@pytest.fixture(scope="module")
def js() -> str:
    return JS.read_text()


# ------------------------------------------------------------------ it is wired up

def test_every_selector_in_the_js_exists_in_the_html(html, js):
    """A selector pointing at a renamed element fails silently — the feature just stops
    working, with no error anyone sees."""
    ids_in_html = set(re.findall(r'id="([^"]+)"', html))
    ids_used = set(re.findall(r'\$\("#([a-zA-Z0-9_-]+)"\)', js))
    ids_used |= set(re.findall(r'getElementById\("([a-zA-Z0-9_-]+)"\)', js))
    missing = sorted(ids_used - ids_in_html)
    assert missing == [], f"app.js references ids that do not exist in index.html: {missing}"


def test_every_fetched_file_exists(js):
    for path in re.findall(r'loadJSON\("([^"]+)"\)', js):
        assert (WEB / path).is_file(), f"app.js fetches {path}, which is not present"


def test_the_stylesheet_and_script_are_linked(html):
    assert 'href="styles.css"' in html and 'src="app.js"' in html
    assert CSS.is_file() and JS.is_file()


def test_every_class_the_js_sets_is_styled(js):
    """A class with no rule renders as unstyled text — most visibly, the caveat boxes."""
    css = CSS.read_text()
    used = set(re.findall(r'className = "([a-z0-9 -]+)"', js))
    tokens = {t for group in used for t in group.split()}
    missing = sorted(t for t in tokens if f".{t}" not in css)
    assert missing == [], f"classes used by app.js with no CSS rule: {missing}"


# ------------------------------------------------------------------ it computes nothing

def test_the_web_tier_does_no_arithmetic_on_displayed_values(js):
    """The moment this page calculates a displayed number it becomes a second source of truth
    that can drift from the model — the exact failure the contract architecture prevents.

    Formatting is allowed; aggregation is not.
    """
    banned = ["reduce(", ".sum(", "Math.round(", "* 100", "/ 100", "+= value", "sum +="]
    found = [b for b in banned if b in js]
    assert found == [], f"app.js appears to compute displayed values: {found}"


def test_the_js_reads_only_generated_files(js):
    """No hardcoded numbers. Every value must come from the contract export."""
    assert "provenance_v1.json" in js and "operations.json" in js
    # A bare 3- or 4-digit literal in a render path would be a smuggled figure.
    render_section = js.split("function renderSites")[1].split("function renderOperations")[0]
    literals = re.findall(r"(?<![\w.\-])\d{3,}(?![\w.])", render_section)
    assert literals == [], f"renderSites contains numeric literals: {literals}"


# ------------------------------------------------------------------ it stays honest

def test_the_page_states_the_placeholder_caveat_before_any_number(html):
    """A reader who scrolls to the table and leaves has still been told the headline
    limitation, because the banner sits above it and is not dismissible."""
    banner_start = html.index('class="banner"')
    banner = html[banner_start:html.index("</div>", banner_start)]
    assert "placeholder at all twelve sites" in banner
    assert "approved, funded or permitted" in banner

    # No dismiss CONTROL -- checked structurally, not by searching for the word.
    #
    # The first version of this test searched the whole file for "dismiss" and failed on the
    # HTML comment that explains the banner is not dismissible. Matching text where the
    # meaning is what matters is a trap this project has fallen into four times; a comment
    # saying "not dismissible" is evidence FOR the property, not against it.
    for control in ["<button", "onclick", "data-dismiss", 'role="button"']:
        assert control not in banner, f"the banner contains a {control} control"

    # And nothing hides it later.
    js = JS.read_text()
    assert ".banner" not in js, "app.js manipulates the banner; it must be static"


def test_the_page_names_all_four_engines_and_does_not_conflate_them(html):
    """Python, MathWorks MATLAB, GNU Octave and Simulink must be distinguishable on screen."""
    for badge in ["badge-python", "badge-matlab", "badge-octave", "badge-simulink"]:
        assert badge in html, f"missing engine badge: {badge}"
    assert "Not MATLAB" in html, "the page must say Octave is not MATLAB"
    assert "synthetic fixture" in html.lower()
    assert "never seen these twelve sites" in html


def test_the_field_data_section_says_it_is_empty_and_why(html):
    section = html.split('id="field-state"')[1].split("</div>")[0]
    assert "No field observations have been received" in section
    assert "honest state, not" in section


def test_there_is_no_unknown_fallback_for_an_unexplained_number(js):
    """A number with no provenance is NOT rendered. 'unknown' looks like an answer."""
    assert "not available" in js
    assert "no resolvable provenance" in js


# ------------------------------------------------------------------ the generated data

@pytest.fixture(scope="module")
def operations_json() -> dict:
    return json.loads((WEB / "operations.json").read_text())


def test_operations_json_matches_the_registry(operations_json):
    """Generated, never hand-written, so the page cannot offer a capability that does not
    exist or omit one that does."""
    assert operations_json["operations"] == ops.for_tier(ops.TIER_BOTH)


def test_operations_json_lists_every_operation_with_reasons(operations_json):
    entries = operations_json["operations"]
    assert len(entries) == len(ops.OPERATIONS)
    for entry in entries:
        if not entry["available"]:
            assert entry["unavailable_reason"], f"{entry['id']} unavailable with no reason"


def test_the_generated_data_rebuilds_identically():
    import subprocess
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/build_platform_web.py"), "--check"],
        cwd=REPO, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_web_tier_carries_no_credentials():
    """Nothing in a public artifact may carry a token, key or AWS account id."""
    suspicious = re.compile(r"(?i)(aws_secret|aws_access|api[_-]?key\s*[:=]|bearer\s+[a-z0-9]{16}|\b\d{12}\b)")
    for path in [HTML, JS, CSS, WEB / "operations.json"]:
        text = path.read_text()
        assert not suspicious.search(text), f"{path.name} looks credential-bearing"

"""The live-vs-main check and the deploy's preflight say what they are for.

Why this file exists
--------------------
Audit F-14 found production matching no commit, and nothing that would have noticed.
`scripts/check_live_vs_main.py` is that check, and it is only worth having if it fails when live
differs. The same day, a full deploy from a checkout without the vendored CesiumJS would have
had its `--delete` sync remove the 377 files the live explorer loads. That sync went with the
gated platform (DEC-030); `deploy_platform.py` now publishes the public site alone, never passes
`--delete`, and refuses any deletion a sync reports. Both are tested here without the network:
the parts that decide are pure, and the network only feeds them.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / f"scripts/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check = load("check_live_vs_main")
deploy = load("deploy_platform")


def test_every_published_folder_maps_to_the_paths_the_site_serves():
    files = check.expected_files("HEAD", deploy.public_trees())
    for path in ("/index.html", "/results.html", "/img/sites/PWC003.jpg", "/t/PWC003", "/f/FFX001",
                 "/errors/404.html"):
        assert path in files, path
    assert files["/t/PWC004"] == ("site/nfc-landing/PWC004",
                                  (REPO / "site/nfc-landing/PWC004").read_bytes())
    tracked = sum(len(check.git("ls-tree", "-r", "--name-only", "HEAD", "--", folder).split())
                  for folder in deploy.public_trees())
    assert len(files) == tracked


def test_a_byte_that_differs_is_reported_and_identical_files_are_not():
    expected = {"/a.html": ("site/www/a.html", b"same"), "/b.html": ("site/www/b.html", b"want")}
    live = {"/a.html": (200, b"same"), "/b.html": (200, b"got!")}
    problems = check.compare(expected, live.__getitem__)
    assert len(problems) == 1 and problems[0].startswith("/b.html: live is 4 bytes")


def test_a_missing_page_is_a_difference():
    problems = check.compare({"/gone.html": ("site/www/gone.html", b"x")}, lambda path: (404, b""))
    assert problems == ["/gone.html: HTTP 404, expected site/www/gone.html"]


def test_the_marker_is_read_only_when_it_names_a_commit():
    sha = "61adffa" + "0" * 33
    assert check.marker_commit(200, json.dumps({"commit": sha}).encode()) == sha
    assert check.marker_commit(404, b"") is None
    assert check.marker_commit(200, b"not json") is None
    assert check.marker_commit(200, b'{"commit": 7}') is None


def test_the_marker_must_account_for_the_ref():
    trees = deploy.public_trees()
    head = check.git("rev-parse", "HEAD").decode().strip()
    assert check.marker_problem(head, head, "HEAD", "deployed.json", trees) is None
    assert "missing or unreadable" in check.marker_problem(None, head, "HEAD", "deployed.json", trees)
    unknown = "0123456" + "f" * 33
    assert "does not have" in check.marker_problem(unknown, head, "HEAD", "deployed.json", trees)
    assert check.published_trees_equal(head, head, trees) is True


def test_a_sync_that_deletes_anything_is_refused_and_one_that_only_writes_is_not():
    """The public syncs never pass --delete. If one ever reports a deletion anyway, the deploy
    stops: a checkout lacks every vendored file that is fetched rather than committed."""
    bucket = f"s3://{deploy.MAIN_BUCKET}/"
    listing = "\n".join([f"(dryrun) upload: site/www/index.html to {bucket}index.html",
                         f"(dryrun) delete: {bucket}explorer/vendor/Cesium/Cesium.js",
                         f"(dryrun) delete: {bucket}old-page.html"])
    deletions = deploy.deletions_from(listing)
    assert deletions == [f"{bucket}explorer/vendor/Cesium/Cesium.js", f"{bucket}old-page.html"]
    reason = deploy.deletion_refusal(deletions)
    assert reason and "2 deletion(s)" in reason and "1 of them under a vendor/ folder" in reason
    assert deploy.deletion_refusal(deploy.deletions_from(
        f"upload: site/www/a.html to {bucket}a.html\n")) is None


def test_no_sync_in_the_deploy_is_ever_given_delete():
    """Asserted against the source: the property is that the flag is absent, everywhere."""
    source = (REPO / "scripts/deploy_platform.py").read_text()
    code = [line for line in source.splitlines()
            if line.strip() and not line.strip().startswith("#")]
    assert not any('"--delete"' in line for line in code)


def test_only_uploads_and_deletions_are_counted_never_progress_lines():
    listing = ("Completed 1.2 MiB/3.0 MiB (2.1 MiB/s) with 12 file(s) remaining\r"
               "upload: site/www/index.html to s3://bucket/index.html\n"
               "Completed 2.0 MiB/3.0 MiB (2.0 MiB/s) with 11 file(s) remaining\n"
               "(dryrun) upload: site/www/a.html to s3://bucket/a.html\n"
               "(dryrun) delete: s3://bucket/old.html\n")
    assert deploy.sync_changes(listing) == (2, 1)


def test_field_pages_are_published_as_html():
    """They have no extension; without a named type S3 would serve the NFC pages as binary."""
    assert deploy.FIELD_HEADERS[:2] == ["--content-type", "text/html;charset=utf-8"]
    assert set(deploy.FIELD_TREES) == {"site/nfc-landing", "site/nfc-capture", "site/errors"}

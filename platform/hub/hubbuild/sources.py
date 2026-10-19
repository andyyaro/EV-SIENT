"""The input registry (platform/hub/sources.json) and the download cache.

Downloads land in their own cache directory (`platform/hub/cache/`, ignored by git), one
subdirectory per dataset, with a `.meta.json` beside each file recording where and when it came
from. Downloaded files are data: they are parsed, never imported or executed.

A pinned file (one with a sha256 in sources.json) is checked on every build; a mismatch stops
the build. A live snapshot (AFDC) is reused from the cache until `--refresh` asks for a new one,
so two builds from one cache read the same bytes.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

USER_AGENT = "evsient-hub-builder/1 (+https://app.futurecity.andyyaro.com)"


class SourceError(RuntimeError):
    """An input could not be obtained or does not match its pin."""


@dataclass
class Input:
    """One downloaded input, as a release records it."""

    dataset: str
    path: Path
    url: str
    sha256: str
    bytes: int
    retrieved_utc: str
    last_modified: str | None
    spec: dict

    def record(self) -> dict:
        s = self.spec
        out = {
            "dataset": self.dataset, "title": s["title"], "publisher": s["publisher"],
            "vintage": s["vintage"], "published": s.get("published"), "licence": s["licence"],
            "licenceUrl": s.get("licence_url"), "landing": s.get("landing"), "url": self.url,
            "file": s["file"], "sha256": self.sha256, "bytes": self.bytes,
            "retrievedUtc": self.retrieved_utc, "lastModified": self.last_modified,
            "label": s.get("label", ""),
        }
        if s.get("published_note"):
            out["publishedNote"] = s["published_note"]
        return out


def load_registry(path: Path) -> dict:
    registry = json.loads(path.read_text())
    if registry.get("schema") != "evsient-hub-sources/1":
        raise SourceError(f"{path} is not an evsient-hub-sources/1 registry")
    return registry


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def public_url(url: str) -> str:
    """The URL as recorded: any api_key parameter removed, so no key reaches a manifest."""
    parts = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if k.lower() != "api_key"]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


def _download(url: str, dest: Path) -> str | None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=600) as response, open(tmp, "wb") as out:
            last_modified = response.headers.get("Last-Modified")
            while True:
                block = response.read(1 << 20)
                if not block:
                    break
                out.write(block)
    except OSError as e:
        tmp.unlink(missing_ok=True)
        raise SourceError(f"could not download {public_url(url)}: {e}") from None
    tmp.replace(dest)
    return last_modified


def _iso(http_date: str | None) -> str | None:
    if not http_date:
        return None
    try:
        return parsedate_to_datetime(http_date).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


def fetch(dataset: str, spec: dict, cache: Path, *, offline: bool = False,
          refresh: bool = False) -> Input:
    """The dataset's file from the cache, downloading it first if needed and allowed."""
    path = cache / dataset / spec["file"]
    meta_path = path.with_name(path.name + ".meta.json")
    pinned = spec.get("sha256")
    url = spec["url"]
    if spec.get("url_needs_api_key"):
        key = os.environ.get("NLR_API_KEY", "DEMO_KEY")
        url = f"{url}&api_key={urllib.parse.quote(key)}"

    have = path.is_file() and (pinned or meta_path.is_file())
    if not have or (refresh and not pinned):
        if offline:
            raise SourceError(f"{dataset}: {path} is not in the cache and --offline was given")
        last_modified = _download(url, path)
        meta = {"url": public_url(url), "retrievedUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "lastModified": _iso(last_modified)}
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    meta = json.loads(meta_path.read_text()) if meta_path.is_file() else {}

    digest = sha256_file(path)
    if pinned and digest != pinned:
        raise SourceError(f"{dataset}: {path.name} has SHA-256 {digest}, but sources.json pins {pinned}. "
                          f"The upstream file changed: review it, then update the pin deliberately.")
    return Input(dataset=dataset, path=path, url=public_url(spec["url"]), sha256=digest,
                 bytes=path.stat().st_size, retrieved_utc=meta.get("retrievedUtc", ""),
                 last_modified=meta.get("lastModified"), spec=spec)

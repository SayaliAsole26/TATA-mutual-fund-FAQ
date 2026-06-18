"""Fetch Groww scheme pages or load pre-saved HTML + JSON snapshots."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.core.corpus_registry import SchemeEntry
from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

RAW_FORMAT_VERSION = 2


@dataclass(frozen=True)
class FetchedContent:
    scheme_id: str
    source_url: str
    content: str
    fetched_at: datetime
    from_snapshot: bool
    raw_html: str | None = None
    html_path: Path | None = None
    json_path: Path | None = None
    cleaned_path: Path | None = None


class RateLimiter:
    """Simple delay-based rate limiter between HTTP requests."""

    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = delay_seconds
        self._last_request_at: float | None = None

    def wait(self) -> None:
        if self._last_request_at is None:
            self._last_request_at = time.monotonic()
            return
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)
        self._last_request_at = time.monotonic()


def raw_html_path_for(scheme_id: str, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.raw_dir / f"{scheme_id}.html"


def raw_json_path_for(scheme_id: str, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.raw_dir / f"{scheme_id}.json"


def raw_cleaned_path_for(scheme_id: str, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.raw_dir / f"{scheme_id}.cleaned.txt"


def build_parser_content(
    text: str,
    *,
    source_url: str,
    scheme_name: str,
) -> str:
    """Normalize plain text with a source header for the parser."""
    header = (
        f"Source URL: {source_url}\n"
        f"Title: {scheme_name} - NAV, Mutual Fund Performance & Portfolio\n\n"
    )
    return header + text


def load_snapshot(
    scheme_id: str,
    *,
    settings: Settings | None = None,
    scheme_name: str | None = None,
) -> FetchedContent | None:
    """Load pre-saved raw HTML + JSON manifest from data/raw/."""
    settings = settings or get_settings()
    json_path = raw_json_path_for(scheme_id, settings)
    html_path = raw_html_path_for(scheme_id, settings)

    if not json_path.is_file() or not html_path.is_file():
        return None

    manifest: dict[str, Any] = json.loads(json_path.read_text(encoding="utf-8"))
    raw_html = html_path.read_text(encoding="utf-8")
    source_url = manifest.get("source_url", "")
    name = scheme_name or manifest.get("scheme_name", scheme_id)
    cleaned_path = raw_cleaned_path_for(scheme_id, settings)

    if cleaned_path.is_file():
        content = cleaned_path.read_text(encoding="utf-8")
    else:
        text = html_to_text(raw_html)
        content = build_parser_content(text, source_url=source_url, scheme_name=name)

    fetched_at = datetime.fromisoformat(manifest["fetched_at"])

    return FetchedContent(
        scheme_id=scheme_id,
        source_url=source_url,
        content=content,
        fetched_at=fetched_at,
        from_snapshot=True,
        raw_html=raw_html,
        html_path=html_path,
        json_path=json_path,
        cleaned_path=cleaned_path if cleaned_path.is_file() else None,
    )


def save_snapshot(
    fetched: FetchedContent,
    *,
    settings: Settings | None = None,
    scheme_name: str | None = None,
    status_code: int = 200,
) -> Path:
    """Persist raw HTML, cleaned text, and JSON manifest to data/raw/."""
    settings = settings or get_settings()
    settings.raw_dir.mkdir(parents=True, exist_ok=True)

    html_path = raw_html_path_for(fetched.scheme_id, settings)
    json_path = raw_json_path_for(fetched.scheme_id, settings)
    cleaned_path = raw_cleaned_path_for(fetched.scheme_id, settings)

    if not fetched.raw_html:
        raise ValueError("save_snapshot requires raw_html on FetchedContent")

    html_path.write_text(fetched.raw_html, encoding="utf-8")
    cleaned_path.write_text(fetched.content, encoding="utf-8")

    manifest = {
        "format_version": RAW_FORMAT_VERSION,
        "scheme_id": fetched.scheme_id,
        "scheme_name": scheme_name or fetched.scheme_id,
        "source_url": fetched.source_url,
        "fetched_at": fetched.fetched_at.isoformat(),
        "content_type": "text/html",
        "status_code": status_code,
        "html_file": html_path.name,
        "cleaned_file": cleaned_path.name,
    }
    json_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return json_path


def fetch_live(
    scheme: SchemeEntry,
    *,
    settings: Settings | None = None,
    rate_limiter: RateLimiter | None = None,
    client: httpx.Client | None = None,
) -> FetchedContent:
    """Fetch a live Groww scheme page; retain raw HTML and parser-ready text."""
    settings = settings or get_settings()
    limiter = rate_limiter or RateLimiter(settings.fetch_delay_seconds)

    limiter.wait()
    owns_client = client is None
    http = client or httpx.Client(
        timeout=settings.fetch_timeout_seconds,
        headers={
            "User-Agent": settings.groww_user_agent,
            "Accept": "text/html,application/xhtml+xml",
        },
        follow_redirects=True,
    )

    try:
        response = http.get(scheme.source_url)
        response.raise_for_status()
        raw_html = response.text
        text = html_to_text(raw_html)
        content = build_parser_content(
            text,
            source_url=scheme.source_url,
            scheme_name=scheme.scheme_name,
        )
        return FetchedContent(
            scheme_id=scheme.scheme_id,
            source_url=scheme.source_url,
            content=content,
            fetched_at=datetime.now(timezone.utc),
            from_snapshot=False,
            raw_html=raw_html,
        )
    finally:
        if owns_client:
            http.close()


def fetch_scheme(
    scheme: SchemeEntry,
    *,
    settings: Settings | None = None,
    force_live: bool = False,
    save_after_live_fetch: bool = True,
    rate_limiter: RateLimiter | None = None,
    client: httpx.Client | None = None,
) -> FetchedContent:
    """
    Load scheme content from local raw HTML+JSON or fetch live from Groww.

    When prefer_local_snapshots is True (default), uses data/raw/<scheme_id>.html
    and data/raw/<scheme_id>.json unless force_live is True or snapshots are missing.
    """
    settings = settings or get_settings()

    if not force_live and settings.prefer_local_snapshots:
        snapshot = load_snapshot(
            scheme.scheme_id,
            settings=settings,
            scheme_name=scheme.scheme_name,
        )
        if snapshot is not None:
            logger.info("Loaded snapshot for %s", scheme.scheme_id)
            return snapshot

    logger.info("Fetching live page for %s", scheme.scheme_id)
    fetched = fetch_live(
        scheme,
        settings=settings,
        rate_limiter=rate_limiter,
        client=client,
    )
    if save_after_live_fetch:
        save_snapshot(fetched, settings=settings, scheme_name=scheme.scheme_name)
    return fetched


def regenerate_cleaned_txt(
    scheme: SchemeEntry,
    *,
    settings: Settings | None = None,
) -> Path | None:
    """Build cleaned.txt from an existing raw HTML snapshot and update the manifest."""
    settings = settings or get_settings()
    html_path = raw_html_path_for(scheme.scheme_id, settings)
    json_path = raw_json_path_for(scheme.scheme_id, settings)
    if not html_path.is_file():
        return None

    manifest: dict[str, Any] = {}
    if json_path.is_file():
        manifest = json.loads(json_path.read_text(encoding="utf-8"))

    source_url = manifest.get("source_url", scheme.source_url)
    name = manifest.get("scheme_name", scheme.scheme_name)
    raw_html = html_path.read_text(encoding="utf-8")
    content = build_parser_content(
        html_to_text(raw_html),
        source_url=source_url,
        scheme_name=name,
    )
    cleaned_path = raw_cleaned_path_for(scheme.scheme_id, settings)
    cleaned_path.write_text(content, encoding="utf-8")

    manifest.update(
        {
            "format_version": RAW_FORMAT_VERSION,
            "scheme_id": scheme.scheme_id,
            "scheme_name": name,
            "source_url": source_url,
            "fetched_at": manifest.get(
                "fetched_at",
                datetime.now(timezone.utc).isoformat(),
            ),
            "content_type": "text/html",
            "status_code": manifest.get("status_code", 200),
            "html_file": html_path.name,
            "cleaned_file": cleaned_path.name,
        }
    )
    json_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return cleaned_path


def html_to_text(html: str) -> str:
    """Convert Groww HTML to cleaned newline-separated plain text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines()]
    collapsed = "\n".join(line for line in lines if line)
    return _drop_navigation_noise(collapsed)


def _drop_navigation_noise(text: str) -> str:
    """Remove common Groww chrome lines from cleaned text."""
    skip_prefixes = (
        "Invest in Stocks",
        "Invest in Mutual Funds",
        "Trade in Futures",
        "SIP calculator",
        "SWP calculator",
        "Download the App",
        "About Us",
        "Show More",
        "Home>",
    )
    kept: list[str] = []
    for line in text.splitlines():
        if any(line.startswith(prefix) for prefix in skip_prefixes):
            continue
        kept.append(line)
    return "\n".join(kept)

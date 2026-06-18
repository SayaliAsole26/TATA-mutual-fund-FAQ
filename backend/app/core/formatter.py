"""Format and validate assistant responses."""

from __future__ import annotations

import re
from datetime import datetime

from app.core.corpus_registry import load_corpus_registry
from app.core.retriever import RetrievedChunk

GROWW_URL_PATTERN = re.compile(r"^https://groww\.in/mutual-funds/[a-z0-9-]+$")

AMFI_INVESTOR_CORNER = "https://www.amfiindia.com/investor-corner"
SEBI_INVESTOR_EDUCATION = "https://investor.sebi.gov.in/"

EDUCATIONAL_URLS = frozenset({AMFI_INVESTOR_CORNER, SEBI_INVESTOR_EDUCATION})

FOOTER_DATE_PATTERN = re.compile(
    r"^Last updated from sources:\s*.+$",
    re.MULTILINE | re.IGNORECASE,
)


def format_footer_date(iso_timestamp: str) -> str:
    """Format extracted_at / last_ingested_at as 'DD Mon YYYY'."""
    if not iso_timestamp:
        return "Unknown"
    try:
        normalized = iso_timestamp.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        return dt.strftime("%d %b %Y")
    except ValueError:
        return iso_timestamp[:10]


def is_allowed_source_url(url: str) -> bool:
    if not GROWW_URL_PATTERN.match(url):
        return False
    allowed = {scheme.source_url for scheme in load_corpus_registry()}
    return url in allowed


def is_allowed_citation_url(url: str) -> bool:
    """Groww corpus URL or approved AMFI/SEBI educational link."""
    if url in EDUCATIONAL_URLS:
        return True
    return is_allowed_source_url(url)


def extract_answer_body(answer_text: str) -> str:
    return answer_text.split("\n\nSource:")[0].strip()


def extract_source_url(answer_text: str) -> str | None:
    match = re.search(r"^Source:\s*(.+)$", answer_text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def has_valid_footer(answer_text: str) -> bool:
    return bool(FOOTER_DATE_PATTERN.search(answer_text))


def truncate_answer_body(answer_text: str, *, max_sentences: int = 3) -> str:
    body = extract_answer_body(answer_text)
    if not body:
        return body
    sentences = re.split(r"(?<=[.!?])\s+", body)
    kept = [s for s in sentences if s.strip()][:max_sentences]
    return " ".join(kept).strip()


def build_formatted_answer(body: str, source_url: str, extracted_at: str) -> str:
    """Build the canonical user-visible answer block."""
    footer_date = format_footer_date(extracted_at)
    body = body.strip()
    return f"{body}\n\nSource: {source_url}\n\nLast updated from sources: {footer_date}"


def format_from_structured(chunk: RetrievedChunk, user_question: str) -> str:
    """Format a direct answer from structured / retrieved chunk without LLM."""
    body = chunk.content
    if not body.endswith((".", "!", "?")):
        body = f"{body}."
    return build_formatted_answer(body, chunk.source_url, chunk.extracted_at)


def normalize_llm_output(raw: str, fallback_url: str, fallback_date: str) -> str:
    """
    Ensure LLM output has Source and footer lines; fix URL if needed.
    """
    text = raw.strip()
    source_match = re.search(r"^Source:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    footer_match = re.search(
        r"^Last updated from sources:\s*(.+)$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )

    if source_match and footer_match:
        url = source_match.group(1).strip()
        if not is_allowed_citation_url(url):
            text = re.sub(
                r"^Source:\s*.+$",
                f"Source: {fallback_url}",
                text,
                count=1,
                flags=re.MULTILINE | re.IGNORECASE,
            )
        body = extract_answer_body(text)
        if count_answer_sentences(text) > 3:
            body = truncate_answer_body(text, max_sentences=3)
            url = extract_source_url(text) or fallback_url
            if not is_allowed_citation_url(url):
                url = fallback_url
            return build_formatted_answer(body, url, fallback_date)
        return text

    # Split body from trailing metadata if partially formatted
    parts = re.split(r"\n\s*\nSource:", text, maxsplit=1, flags=re.IGNORECASE)
    body = truncate_answer_body(parts[0].strip(), max_sentences=3) if parts[0].strip() else parts[0].strip()
    return build_formatted_answer(body, fallback_url, fallback_date)


def count_answer_sentences(answer_text: str) -> int:
    """Count sentences in the answer body (before Source line)."""
    body = extract_answer_body(answer_text)
    if not body:
        return 0
    sentences = re.split(r"(?<=[.!?])\s+", body)
    return len([s for s in sentences if s.strip()])

"""
Semantic-first chunking for FAQ RAG (Phase 1.1.3).

Primary source: section text from data/processed/<scheme_id>.json.
Fallback: anchor-based extraction from data/raw/<scheme_id>.cleaned.txt
for sections missing after live HTML parse (exit_load, tax, fund_managers, etc.).

Chunks stay topic-pure and small for BGE-large retrieval; long fallback blocks
are split under MAX_EMBED_TOKENS with sentence-aware overlap.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app.ingestion.parser import SECTION_IDS
from app.ingestion.processed_store import load_processed_document
from app.ingestion.fetcher import raw_cleaned_path_for
from config.settings import Settings, get_settings

ChunkSource = Literal["processed", "cleaned_fallback"]

# BGE-large-en-v1.5 hard limit is 512 tokens; keep a safety margin.
MAX_EMBED_TOKENS = 450
OVERLAP_TOKENS = 60
CHARS_PER_TOKEN = 4

MAX_EMBED_CHARS = MAX_EMBED_TOKENS * CHARS_PER_TOKEN
OVERLAP_CHARS = OVERLAP_TOKENS * CHARS_PER_TOKEN

# Sections often missing from live HTML processed JSON — try cleaned.txt fallback.
FALLBACK_SECTION_IDS = frozenset(
    {
        "exit_load",
        "tax",
        "stamp_duty",
        "fund_managers",
        "investment_objective",
    }
)

SECTION_LABELS: dict[str, str] = {
    "expense_ratio": "Expense ratio",
    "exit_load": "Exit load",
    "min_sip": "Minimum SIP",
    "min_lumpsum": "Minimum lumpsum",
    "riskometer": "Riskometer",
    "benchmark": "Benchmark",
    "fund_managers": "Fund managers",
    "tax": "Tax implication",
    "stamp_duty": "Stamp duty",
    "elss_lock_in": "ELSS lock-in",
    "investment_objective": "Investment objective",
    "nav": "NAV",
    "aum": "AUM",
}

# Stop markers when extracting bounded blocks from cleaned Groww text.
_BLOCK_END_MARKERS = (
    "Compare similar funds",
    "Also manages these schemes",
    "Investment Objective",
    "Fund benchmark",
    "Holdings",
    "Return calculator",
    "Returns and rankings",
)


@dataclass
class Chunk:
    chunk_id: str
    scheme_id: str
    scheme_name: str
    source_url: str
    section: str
    content: str
    extracted_at: str
    chunk_index: int
    chunk_source: ChunkSource
    section_label: str = field(default="")

    def __post_init__(self) -> None:
        if not self.section_label:
            self.section_label = SECTION_LABELS.get(self.section, self.section)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def estimate_tokens(text: str) -> int:
    """Rough token count for BGE length guards (English ~4 chars/token)."""
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, len(stripped) // CHARS_PER_TOKEN)


def build_embed_text(chunk: Chunk | dict[str, Any]) -> str:
    """
    Enrich short passages for BGE-large embedding.

    Stored ``content`` stays minimal; embed_index should call this before encode.
    """
    if isinstance(chunk, dict):
        content = chunk["content"]
        scheme_name = chunk["scheme_name"]
        section = chunk["section"]
        section_label = chunk.get("section_label") or SECTION_LABELS.get(section, section)
    else:
        content = chunk.content
        scheme_name = chunk.scheme_name
        section_label = chunk.section_label

    if estimate_tokens(content) >= 50:
        return content
    return f"{scheme_name} | {section_label} | {content}"


def chunks_path_for(scheme_id: str, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.processed_dir / f"{scheme_id}_chunks.json"


def chunk_scheme(
    scheme_id: str,
    *,
    settings: Settings | None = None,
    processed: dict[str, Any] | None = None,
    cleaned_text: str | None = None,
) -> list[Chunk]:
    """Build chunks for one scheme from processed JSON + optional cleaned.txt."""
    settings = settings or get_settings()
    doc = processed if processed is not None else load_processed_document(scheme_id, settings=settings)
    if doc is None:
        raise FileNotFoundError(f"No processed document for scheme_id={scheme_id!r}")

    if cleaned_text is None:
        cleaned_path = raw_cleaned_path_for(scheme_id, settings)
        cleaned_text = cleaned_path.read_text(encoding="utf-8") if cleaned_path.is_file() else ""

    extracted_at = doc.get("parsed_at") or datetime.now(timezone.utc).isoformat()
    scheme_name = doc.get("scheme_name", scheme_id)
    source_url = doc.get("source_url", "")
    sections: dict[str, str] = dict(doc.get("sections") or {})

    fallback = extract_fallback_sections(cleaned_text) if cleaned_text else {}
    for section_id, text in fallback.items():
        if section_id not in sections and text.strip():
            sections[section_id] = text

    chunks: list[Chunk] = []
    for section_id in SECTION_IDS:
        content = sections.get(section_id)
        if not content or not content.strip():
            continue

        source: ChunkSource = (
            "processed" if section_id in (doc.get("sections") or {}) else "cleaned_fallback"
        )
        parts = split_long_text(content.strip())
        for index, part in enumerate(parts):
            chunk_id = f"{scheme_id}__{section_id}__{index}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    scheme_id=scheme_id,
                    scheme_name=scheme_name,
                    source_url=source_url,
                    section=section_id,
                    content=part,
                    extracted_at=extracted_at,
                    chunk_index=index,
                    chunk_source=source,
                )
            )

    return chunks


def chunk_all_schemes(*, settings: Settings | None = None) -> dict[str, list[Chunk]]:
    """Chunk every scheme that has a processed JSON file."""
    settings = settings or get_settings()
    result: dict[str, list[Chunk]] = {}
    for path in sorted(settings.processed_dir.glob("tata-*.json")):
        if path.name.endswith("_chunks.json"):
            continue
        scheme_id = path.stem
        result[scheme_id] = chunk_scheme(scheme_id, settings=settings)
    return result


def save_scheme_chunks(
    chunks: list[Chunk],
    scheme_id: str,
    *,
    settings: Settings | None = None,
    path: Path | None = None,
) -> Path:
    """Write data/processed/<scheme_id>_chunks.json for manual review."""
    settings = settings or get_settings()
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = path or chunks_path_for(scheme_id, settings)
    payload = {
        "scheme_id": scheme_id,
        "chunk_count": len(chunks),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "chunks": [c.to_dict() for c in chunks],
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def chunk_and_save_scheme(
    scheme_id: str,
    *,
    settings: Settings | None = None,
    processed: dict[str, Any] | None = None,
    cleaned_text: str | None = None,
) -> tuple[list[Chunk], Path]:
    """Build chunks for one scheme and write data/processed/<scheme_id>_chunks.json."""
    chunks = chunk_scheme(
        scheme_id,
        settings=settings,
        processed=processed,
        cleaned_text=cleaned_text,
    )
    path = save_scheme_chunks(chunks, scheme_id, settings=settings)
    return chunks, path


def save_all_scheme_chunks(*, settings: Settings | None = None) -> dict[str, Path]:
    """Chunk every processed scheme and write *_chunks.json files."""
    settings = settings or get_settings()
    paths: dict[str, Path] = {}
    for scheme_id, chunks in chunk_all_schemes(settings=settings).items():
        paths[scheme_id] = save_scheme_chunks(chunks, scheme_id, settings=settings)
    return paths


def load_scheme_chunks(
    scheme_id: str,
    *,
    settings: Settings | None = None,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """Load previously saved chunk JSON for a scheme."""
    settings = settings or get_settings()
    file_path = path or chunks_path_for(scheme_id, settings)
    if not file_path.is_file():
        return []
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    return list(payload.get("chunks") or [])


def extract_fallback_sections(cleaned_text: str) -> dict[str, str]:
    """Pull FAQ sections from Groww cleaned plain text when parser output is incomplete."""
    sections: dict[str, str] = {}
    fees = _extract_fees_and_tax_block(cleaned_text)
    sections.update(fees)

    if managers := _extract_fund_managers_block(cleaned_text):
        sections["fund_managers"] = managers

    if objective := _extract_investment_objective_block(cleaned_text):
        sections["investment_objective"] = objective

    return {k: v for k, v in sections.items() if k in FALLBACK_SECTION_IDS and v.strip()}


def split_long_text(text: str) -> list[str]:
    """Split text that exceeds BGE-large safe length; otherwise return a single part."""
    if len(text) <= MAX_EMBED_CHARS:
        return [text]

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(sentences) <= 1:
        return _split_by_char_window(text)

    parts: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence_len = len(sentence) + (1 if current else 0)
        if current and current_len + sentence_len > MAX_EMBED_CHARS:
            parts.append(" ".join(current))
            overlap: list[str] = []
            overlap_len = 0
            for prev in reversed(current):
                if overlap_len + len(prev) + 1 > OVERLAP_CHARS:
                    break
                overlap.insert(0, prev)
                overlap_len += len(prev) + 1
            current = overlap + [sentence]
            current_len = sum(len(s) for s in current) + max(0, len(current) - 1)
        else:
            current.append(sentence)
            current_len += sentence_len

    if current:
        parts.append(" ".join(current))

    return parts if parts else [text[:MAX_EMBED_CHARS]]


def _split_by_char_window(text: str) -> list[str]:
    """Fallback splitter when sentence boundaries are unavailable."""
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + MAX_EMBED_CHARS, len(text))
        parts.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - OVERLAP_CHARS, start + 1)
    return [p for p in parts if p]


def _find_block_end(text: str, start: int) -> int:
    positions = [text.find(marker, start) for marker in _BLOCK_END_MARKERS]
    valid = [p for p in positions if p >= 0]
    return min(valid) if valid else len(text)


def _extract_between(text: str, start_marker: str, start: int = 0) -> str | None:
    idx = text.find(start_marker, start)
    if idx < 0:
        return None
    block_start = idx + len(start_marker)
    block_end = _find_block_end(text, block_start)
    return text[block_start:block_end].strip()


def _extract_fees_and_tax_block(text: str) -> dict[str, str]:
    """Parse exit load / stamp duty / tax from the Groww fees block."""
    heading = "Exit load, stamp duty and tax"
    if heading not in text:
        return {}

    start = text.find(heading)
    block_end = _find_block_end(text, start + len(heading))
    block = text[start:block_end]
    sections: dict[str, str] = {}

    exit_load = _read_label_value_block(block, "Exit load", stop_labels=("Stamp duty",))
    if exit_load:
        sections["exit_load"] = f"Exit load: {_normalize_fee_value(exit_load)}"

    stamp = _read_stamp_duty_from_block(block)
    if stamp:
        sections["stamp_duty"] = f"Stamp duty: {stamp}"

    tax = _read_label_value_block(block, "Tax implication", stop_labels=())
    if tax:
        tax = re.sub(r"\s*Check past data\s*$", "", tax, flags=re.IGNORECASE)
        sections["tax"] = f"Tax implication: {_collapse_whitespace(tax)}"

    return sections


def _read_stamp_duty_from_block(block: str) -> str | None:
    match = re.search(
        r"Stamp duty on investment:\s*\n?\s*(.+?)(?=\n(?:from July|Tax implication|Check past|Compare similar)|\Z)",
        block,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return _collapse_whitespace(match.group(1))
    return _read_label_value_block(block, "Stamp duty", stop_labels=("Tax implication",))


def _read_label_value_block(
    block: str,
    label: str,
    *,
    stop_labels: tuple[str, ...],
) -> str | None:
    pattern = rf"(?:^|\n){re.escape(label)}\s*\n+"
    match = re.search(pattern, block, re.IGNORECASE)
    if not match:
        return None

    rest = block[match.end() :]
    end = len(rest)
    for stop in stop_labels:
        stop_match = re.search(rf"(?:^|\n){re.escape(stop)}\b", rest, re.IGNORECASE)
        if stop_match:
            end = min(end, stop_match.start())

    value = _collapse_whitespace(rest[:end])
    if not value or value.lower() in {"view details", "check past data"}:
        return None
    return value


def _normalize_fee_value(value: str) -> str:
    cleaned = _collapse_whitespace(value)
    if cleaned in {"--", "—"}:
        return "Nil"
    return cleaned


def _extract_fund_managers_block(text: str) -> str | None:
    marker = "Fund management"
    if marker not in text:
        return None

    raw = _extract_between(text, marker)
    if not raw:
        return None

    # Drop bios and cross-scheme lists — keep manager name + tenure only.
    cut = raw
    for stop in ("Also manages these schemes", "Education", "View details"):
        pos = cut.find(stop)
        if pos >= 0:
            cut = cut[:pos]

    managers: list[str] = []
    lines = [ln.strip() for ln in cut.splitlines() if ln.strip()]
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.fullmatch(r"[A-Z]{1,3}", line):
            i += 1
            continue
        if re.search(r"view details|education|experience|also manages", line, re.I):
            i += 1
            continue

        if i + 2 < len(lines) and re.match(r"[A-Za-z]{3}\s+\d{4}", lines[i + 1]):
            name = line
            tenure = f"{lines[i + 1]} {lines[i + 2]}".replace("  ", " ").strip()
            tenure = re.sub(r"\s+", " ", tenure)
            if len(name) >= 4 and not name.isupper():
                managers.append(f"{name} ({tenure})")
            i += 3
            continue

        tenure_match = re.match(
            r"^([A-Z][A-Za-z.\s]{2,})\n+([A-Za-z]{3}\s+\d{4}\s*-\s*Present)$",
            f"{line}\n{lines[i + 1]}" if i + 1 < len(lines) else line,
            re.MULTILINE,
        )
        if tenure_match:
            managers.append(
                f"{tenure_match.group(1).strip()} ({tenure_match.group(2).strip()})"
            )
            i += 2
            continue

        i += 1

    if not managers:
        about = re.search(
            r"([A-Z][A-Za-z.\s]+)\s+is the Current Fund Manager of",
            text,
        )
        if about:
            return f"Fund manager(s): {about.group(1).strip()}"

    if not managers:
        return None

    return f"Fund manager(s): {'; '.join(managers)}"


def _extract_investment_objective_block(text: str) -> str | None:
    marker = "Investment Objective"
    body = _extract_between(text, marker)
    if not body:
        return None

    objective = body.split("Fund benchmark")[0].strip()
    objective = _collapse_whitespace(objective)
    if not objective:
        return None
    return f"Investment objective: {objective}"


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()

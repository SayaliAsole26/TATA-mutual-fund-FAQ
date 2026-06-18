"""Extract FAQ-relevant sections from Groww scheme page text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.ingestion.fetcher import FetchedContent

SECTION_IDS = (
    "expense_ratio",
    "exit_load",
    "min_sip",
    "min_lumpsum",
    "riskometer",
    "benchmark",
    "fund_managers",
    "tax",
    "stamp_duty",
    "elss_lock_in",
    "investment_objective",
    "nav",
    "aum",
)


@dataclass
class ParsedSchemeDocument:
    scheme_id: str
    source_url: str
    scheme_name: str
    sections: dict[str, str] = field(default_factory=dict)
    structured_fields: dict[str, str] = field(default_factory=dict)

    def get_section(self, section_id: str) -> str | None:
        return self.sections.get(section_id)


def parse_scheme_content(
    fetched: FetchedContent,
    *,
    scheme_name: str | None = None,
) -> ParsedSchemeDocument:
    """Parse FAQ-relevant sections from fetched Groww page text."""
    text = fetched.content
    name = scheme_name or _extract_scheme_name(text) or fetched.scheme_id

    structured: dict[str, str] = {}
    sections: dict[str, str] = {}

    if expense := _extract_expense_ratio(text):
        structured["expense_ratio"] = expense
        sections["expense_ratio"] = f"Expense ratio: {expense}"

    if min_sip := _extract_label_value(text, r"Min\. for SIP"):
        structured["min_sip"] = min_sip
        sections["min_sip"] = f"Minimum SIP amount: {min_sip}"

    if min_lumpsum := _extract_label_value(text, r"Min\. for 1st investment"):
        structured["min_lumpsum"] = min_lumpsum
        sections["min_lumpsum"] = f"Minimum first investment (lumpsum): {min_lumpsum}"

    if exit_load := _extract_exit_load(text):
        structured["exit_load"] = exit_load
        sections["exit_load"] = f"Exit load: {exit_load}"

    if tax := _extract_tax_implication(text):
        structured["tax"] = tax
        sections["tax"] = f"Tax implication: {tax}"

    if stamp := _extract_stamp_duty(text):
        structured["stamp_duty"] = stamp
        sections["stamp_duty"] = f"Stamp duty: {stamp}"

    if benchmark := _extract_benchmark(text):
        structured["benchmark"] = benchmark
        sections["benchmark"] = f"Benchmark: {benchmark}"

    if risk := _extract_riskometer(text):
        structured["riskometer"] = risk
        sections["riskometer"] = f"Riskometer: {risk}"

    if objective := _extract_investment_objective(text):
        structured["investment_objective"] = objective
        sections["investment_objective"] = f"Investment objective: {objective}"

    if nav := _extract_nav(text):
        structured["nav"] = nav
        sections["nav"] = f"Latest NAV: {nav}"

    if aum := _extract_aum(text):
        structured["aum"] = aum
        sections["aum"] = f"Fund size (AUM): {aum}"

    if lock_in := _extract_elss_lock_in(text):
        structured["elss_lock_in"] = lock_in
        sections["elss_lock_in"] = f"ELSS lock-in period: {lock_in}"

    managers = _extract_fund_managers(text)
    if managers:
        structured["fund_managers"] = managers
        sections["fund_managers"] = f"Fund manager(s): {managers}"

    return ParsedSchemeDocument(
        scheme_id=fetched.scheme_id,
        source_url=fetched.source_url or _extract_source_url(text) or "",
        scheme_name=name,
        sections=sections,
        structured_fields=structured,
    )


def _extract_scheme_name(text: str) -> str | None:
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def _extract_source_url(text: str) -> str | None:
    match = re.search(r"^Source URL:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def _extract_label_value(text: str, label_pattern: str) -> str | None:
    pattern = rf"{label_pattern}\s*\n\s*(.+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    value = match.group(1).strip()
    if value in {"--", "—"}:
        return None
    return value


def _extract_expense_ratio(text: str) -> str | None:
    value = _extract_label_value(text, r"Expense ratio")
    if value and re.search(r"[\d.]+%", value):
        return value
    match = re.search(
        r"Expense ratio\s*\n\s*([\d.]+%)",
        text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _extract_exit_load(text: str) -> str | None:
    match = re.search(
        r"###\s*Exit load, stamp duty and tax\s*\n+####\s*Exit load\s*\n+(.+?)"
        r"(?=\n####\s|\nCheck past data|\n###\s|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    body = _collapse_whitespace(match.group(1))
    if body in {"--", "—"}:
        return "Nil"
    return body or None


def _extract_tax_implication(text: str) -> str | None:
    match = re.search(
        r"###\s*Exit load, stamp duty and tax\s*\n+####\s*Tax implication\s*\n+(.+?)"
        r"(?=\n####\s|\nCheck past data|\n###\s|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return _extract_subsection(text, "Tax implication")
    return _collapse_whitespace(match.group(1)) or None


def _extract_subsection(text: str, heading: str) -> str | None:
    pattern = rf"####\s*{re.escape(heading)}\s*\n+(.+?)(?=\n####\s|\nCheck past data|\n###\s|\Z)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    body = _collapse_whitespace(match.group(1))
    if body in {"--", "—"}:
        return "Nil"
    return body or None


def _extract_stamp_duty(text: str) -> str | None:
    match = re.search(
        r"####\s*Stamp duty[^\n]*\n+(.+?)(?=\n####\s|\nCheck past data|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return _collapse_whitespace(match.group(1))
    match = re.search(
        r"Stamp duty on investment:\s*(.+)",
        text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _extract_benchmark(text: str) -> str | None:
    match = re.search(r"Fund benchmark\s*(.+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(
        r"####\s*Investment Objective\s*\n.+?Fund benchmark\s*(.+)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else None


def _extract_riskometer(text: str) -> str | None:
    about = re.search(
        r"###\s*About .+?is rated\s+(.+?)\s+risk\.",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if about:
        return about.group(1).strip()

    match = re.search(
        r"(Very\s+(?:High|Low)\s+Risk|Moderately\s+High\s+Risk|Moderate\s+Risk|Low\s+Risk)",
        text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _extract_investment_objective(text: str) -> str | None:
    match = re.search(
        r"####\s*Investment Objective\s*\n+(.+?)(?=\nFund benchmark|\n####\s|\n###\s|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    return _collapse_whitespace(match.group(1)) if match else None


def _extract_nav(text: str) -> str | None:
    match = re.search(
        r"Latest NAV as of [^is]+\s+is\s+(₹[\d,.]+)",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    match = re.search(r"NAV:\s*[^\n]+\n+(₹[\d,.]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_aum(text: str) -> str | None:
    value = _extract_label_value(text, r"Fund size \(AUM\)")
    if value:
        return value
    match = re.search(
        r"Asset Under Management\(AUM\) of\s+(₹[\d,.]+\s*Cr)",
        text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _extract_elss_lock_in(text: str) -> str | None:
    match = re.search(r"ELSS\s*•\s*([^E\n]+?Lock-in)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"(\d+\s*Y(?:ear)?s?\s*Lock-in)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_fund_managers(text: str) -> str | None:
    block_match = re.search(
        r"###\s*Fund management\s*(.+?)(?=\n###\s*About |\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not block_match:
        return None

    block = block_match.group(1)
    managers: list[str] = []
    for match in re.finditer(
        r"^([A-Z][A-Za-z.\s]+)\n+([A-Za-z]{3}\s+\d{4}\s*\\?-\s*Present)\s*$",
        block,
        re.MULTILINE,
    ):
        name = match.group(1).strip()
        tenure = match.group(2).replace("\\-", "-")
        if name in {"View details", "Education", "Experience"}:
            continue
        if len(name) < 4 or name.isupper() and len(name) <= 3:
            continue
        managers.append(f"{name} ({tenure})")

    if not managers:
        about = re.search(
            r"Current Fund Manager of .+? fund\.\s*(.+?)\s+is the Current Fund Manager",
            text,
            re.IGNORECASE,
        )
        if about:
            return about.group(1).strip()
        about2 = re.search(
            r"([A-Z][A-Za-z\s.]+)\s+is the Current Fund Manager of",
            text,
        )
        if about2:
            return about2.group(1).strip()

    return "; ".join(managers) if managers else None


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()

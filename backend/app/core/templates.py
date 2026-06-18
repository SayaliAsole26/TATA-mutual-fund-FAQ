"""Refusal and safe-fallback message templates (Phase 3)."""

from __future__ import annotations

from datetime import datetime, timezone

AMFI_INVESTOR_CORNER = "https://www.amfiindia.com/investor-corner"
SEBI_INVESTOR_EDUCATION = "https://investor.sebi.gov.in/"

REFUSAL_REASONS = frozenset(
    {
        "advisory",
        "comparative",
        "pii",
        "performance",
        "out_of_corpus",
        "out_of_scope",
    }
)


def _today_footer() -> str:
    return datetime.now(timezone.utc).strftime("%d %b %Y")


def build_refusal_answer(body: str, citation_url: str) -> str:
    """Canonical refusal text with exactly one Source line and footer."""
    body = body.strip()
    if not body.endswith((".", "!", "?")):
        body = f"{body}."
    return (
        f"{body}\n\n"
        f"Source: {citation_url}\n\n"
        f"Last updated from sources: {_today_footer()}"
    )


def advisory_refusal() -> tuple[str, str]:
    body = (
        "I am a facts-only assistant and cannot provide investment advice, "
        "recommendations, or opinions. For general mutual fund education, "
        "please visit the AMFI Investor Corner."
    )
    return build_refusal_answer(body, AMFI_INVESTOR_CORNER), AMFI_INVESTOR_CORNER


def comparative_refusal() -> tuple[str, str]:
    body = (
        "I cannot compare or rank mutual fund schemes. "
        "I can only share objective facts about one Tata Mutual Fund scheme at a time. "
        "For investor education, see the SEBI investor resources."
    )
    return build_refusal_answer(body, SEBI_INVESTOR_EDUCATION), SEBI_INVESTOR_EDUCATION


def pii_refusal() -> tuple[str, str]:
    body = (
        "Please do not share personal or financial identifiers such as PAN, "
        "Aadhaar, phone numbers, or account details. "
        "I can only answer factual questions about the 15 Tata Mutual Fund schemes "
        "without collecting personal data."
    )
    return build_refusal_answer(body, AMFI_INVESTOR_CORNER), AMFI_INVESTOR_CORNER


def performance_refusal(scheme_name: str, scheme_url: str) -> tuple[str, str]:
    body = (
        f"I cannot calculate, estimate, or quote historical returns or performance. "
        f"For published data about {scheme_name}, please see the official scheme page."
    )
    return build_refusal_answer(body, scheme_url), scheme_url


def performance_refusal_generic() -> tuple[str, str]:
    body = (
        "I cannot calculate or quote fund returns or performance. "
        "Please name one of the 15 Tata Mutual Fund schemes so I can point you "
        "to the official scheme page."
    )
    return build_refusal_answer(body, AMFI_INVESTOR_CORNER), AMFI_INVESTOR_CORNER


def out_of_corpus_refusal() -> tuple[str, str]:
    body = (
        "I can only answer questions about the 15 Tata Mutual Fund schemes "
        "listed in this assistant (Groww pages). "
        "For broader mutual fund education, visit the AMFI Investor Corner."
    )
    return build_refusal_answer(body, AMFI_INVESTOR_CORNER), AMFI_INVESTOR_CORNER


def out_of_scope_refusal() -> tuple[str, str]:
    body = (
        "That question is outside the scope of this facts-only FAQ assistant. "
        "I can help with objective scheme attributes for the 15 Tata Mutual Fund schemes."
    )
    return build_refusal_answer(body, SEBI_INVESTOR_EDUCATION), SEBI_INVESTOR_EDUCATION


def refusal_response(reason: str, *, scheme_name: str = "", scheme_url: str = "") -> dict:
    """Build API JSON for a refusal."""
    if reason == "advisory":
        answer, url = advisory_refusal()
    elif reason == "comparative":
        answer, url = comparative_refusal()
    elif reason == "pii":
        answer, url = pii_refusal()
    elif reason == "performance":
        if scheme_name and scheme_url:
            answer, url = performance_refusal(scheme_name, scheme_url)
        else:
            answer, url = performance_refusal_generic()
    elif reason == "out_of_corpus":
        answer, url = out_of_corpus_refusal()
    elif reason == "out_of_scope":
        answer, url = out_of_scope_refusal()
    else:
        answer, url = advisory_refusal()
        reason = "advisory"

    payload: dict = {
        "type": "refusal",
        "reason": reason,
        "answer": answer,
        "source_url": url,
    }
    if scheme_name:
        payload["scheme_name"] = scheme_name
    return payload

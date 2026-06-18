"""Pydantic models for the chat API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class ChatAnswerResponse(BaseModel):
    type: Literal["answer"] = "answer"
    answer: str
    scheme_id: str
    scheme_name: str
    source_url: str
    last_updated: str | None = None
    sections_used: list[str] = Field(default_factory=list)
    retrieval_source: str


class ChatClarificationResponse(BaseModel):
    type: Literal["clarification"] = "clarification"
    message: str
    schemes: list[str]


class ChatErrorResponse(BaseModel):
    type: Literal["error"] = "error"
    message: str


class ChatRefusalResponse(BaseModel):
    type: Literal["refusal"] = "refusal"
    reason: str
    answer: str
    source_url: str
    scheme_name: str | None = None


class IngestResponse(BaseModel):
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    index: dict


class SchemeItem(BaseModel):
    scheme_id: str
    scheme_name: str
    source_url: str
    category: str


class SchemesResponse(BaseModel):
    amc: str
    schemes: list[SchemeItem]

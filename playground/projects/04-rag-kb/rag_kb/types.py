"""Shared typed records for the RAG pipeline."""

from dataclasses import dataclass
from typing import TypedDict


class AssistantMessage(TypedDict):
    role: str
    content: str


class Citation(TypedDict):
    source: str
    chunk_id: str
    snippet: str
    score: float


class Answer(TypedDict):
    answer: str
    citations: list[Citation]
    refused: bool


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    text: str
    source: str
    metadata: dict[str, str]


@dataclass(frozen=True, slots=True)
class SearchResult:
    chunk: Chunk
    score: float

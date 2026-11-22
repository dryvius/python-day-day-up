"""In-memory cosine index with metadata filtering and deterministic ordering."""

from collections.abc import Mapping, Sequence

from rag_kb.embedding import FakeEmbedding
from rag_kb.types import Chunk, SearchResult


class InMemoryIndex:
    def __init__(self, embedding: FakeEmbedding) -> None:
        self._embedding = embedding
        self._records: list[tuple[Chunk, list[float]]] = []

    def add(self, chunks: Sequence[Chunk]) -> None:
        vectors = self._embedding.embed_many([chunk.text for chunk in chunks])
        self._records.extend(zip(chunks, vectors, strict=True))

    def clear(self) -> None:
        self._records.clear()

    def search(
        self,
        query: str,
        *,
        top_k: int = 3,
        metadata_filter: Mapping[str, str] | None = None,
    ) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        query_vector = self._embedding.embed(query)
        scored = [
            SearchResult(chunk=chunk, score=_dot(query_vector, vector))
            for chunk, vector in self._records
            if _matches(chunk, metadata_filter)
        ]
        scored.sort(key=lambda result: (-result.score, result.chunk.chunk_id))
        return scored[:top_k]

    def __len__(self) -> int:
        return len(self._records)


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _matches(chunk: Chunk, expected: Mapping[str, str] | None) -> bool:
    if expected is None:
        return True
    return all(chunk.metadata.get(key) == value for key, value in expected.items())

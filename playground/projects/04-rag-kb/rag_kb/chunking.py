"""Character-based text chunking with explicit overlap."""

from rag_kb.types import Chunk


def chunk_text(
    text: str,
    *,
    source: str,
    chunk_size: int = 240,
    overlap: int = 40,
    metadata: dict[str, str] | None = None,
) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")

    normalized = "\n".join(line.strip() for line in text.splitlines()).strip()
    if not normalized:
        return []

    chunks: list[Chunk] = []
    start = 0
    step = chunk_size - overlap
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        body = normalized[start:end].strip()
        if body:
            index = len(chunks)
            chunks.append(
                Chunk(
                    chunk_id=f"{source}#{index}",
                    text=body,
                    source=source,
                    metadata={
                        **(metadata or {}),
                        "source": source,
                        "chunk_index": str(index),
                    },
                )
            )
        if end == len(normalized):
            break
        start += step
    return chunks

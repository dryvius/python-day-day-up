"""End-to-end document ingestion and grounded question answering."""

from pathlib import Path

from rag_kb.chunking import chunk_text
from rag_kb.embedding import FakeEmbedding
from rag_kb.index import InMemoryIndex
from rag_kb.llm import FakeLLM
from rag_kb.types import Answer, Citation, SearchResult

REFUSAL = "知识库中没有足够资料回答该问题。"


class RAGPipeline:
    def __init__(
        self,
        *,
        chunk_size: int = 240,
        overlap: int = 40,
        top_k: int = 3,
        min_score: float = 0.15,
    ) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.top_k = top_k
        self.min_score = min_score
        self.index = InMemoryIndex(FakeEmbedding())
        self.llm = FakeLLM()

    def ingest(self, directory: Path) -> int:
        self.index.clear()
        chunks = []
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                continue
            source = path.relative_to(directory).as_posix()
            chunks.extend(
                chunk_text(
                    path.read_text(encoding="utf-8"),
                    source=source,
                    chunk_size=self.chunk_size,
                    overlap=self.overlap,
                    metadata={"extension": path.suffix.lower()},
                )
            )
        self.index.add(chunks)
        return len(chunks)

    def retrieve(self, question: str) -> list[SearchResult]:
        return [
            result
            for result in self.index.search(question, top_k=self.top_k)
            if result.score >= self.min_score
        ]

    async def ask(self, question: str) -> Answer:
        results = self.retrieve(question)
        if not results:
            return {"answer": REFUSAL, "citations": [], "refused": True}

        citations: list[Citation] = [
            {
                "source": result.chunk.source,
                "chunk_id": result.chunk.chunk_id,
                "snippet": result.chunk.text[:160],
                "score": round(result.score, 6),
            }
            for result in results
        ]
        context = "\n".join(
            f"- [{citation['source']}] {citation['snippet']}" for citation in citations
        )
        assistant = await self.llm.complete(
            [
                {
                    "role": "system",
                    "content": "仅依据以下知识库片段回答：\n" + context,
                },
                {"role": "user", "content": question},
            ]
        )
        return {
            "answer": assistant["content"],
            "citations": citations,
            "refused": False,
        }

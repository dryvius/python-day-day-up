import asyncio
import subprocess
import sys
from pathlib import Path

from rag_kb.chunking import chunk_text
from rag_kb.embedding import FakeEmbedding
from rag_kb.pipeline import REFUSAL, RAGPipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_embedding_is_deterministic_in_current_and_new_process() -> None:
    embedding = FakeEmbedding()
    expected = embedding.embed("stable 向量")
    code = (
        "from rag_kb.embedding import FakeEmbedding;"
        "print(FakeEmbedding().embed('stable 向量'))"
    )
    actual = subprocess.check_output(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        text=True,
    ).strip()
    assert actual == repr(expected)


def test_chunking_respects_size_overlap_and_metadata() -> None:
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = chunk_text(text, source="demo.txt", chunk_size=10, overlap=3)
    assert [chunk.text for chunk in chunks] == [
        "abcdefghij",
        "hijklmnopq",
        "opqrstuvwx",
        "vwxyz",
    ]
    assert chunks[0].metadata["source"] == "demo.txt"
    assert chunks[1].chunk_id == "demo.txt#1"


def test_retrieve_returns_expected_source_and_top_k() -> None:
    pipeline = RAGPipeline(top_k=2)
    pipeline.ingest(PROJECT_ROOT / "data" / "sample_docs")
    results = pipeline.retrieve("pytest 测试框架")
    assert 0 < len(results) <= 2
    assert results[0].chunk.source == "python.md"
    assert results == sorted(
        results,
        key=lambda result: (-result.score, result.chunk.chunk_id),
    )


def test_ask_returns_citations() -> None:
    pipeline = RAGPipeline()
    pipeline.ingest(PROJECT_ROOT / "data" / "sample_docs")
    answer = asyncio.run(pipeline.ask("RAG 默认 chunk 字符和 overlap 是多少？"))
    assert answer["refused"] is False
    assert answer["citations"]
    assert answer["citations"][0]["source"] == "rag.md"


def test_ask_refuses_without_relevant_evidence() -> None:
    pipeline = RAGPipeline()
    pipeline.ingest(PROJECT_ROOT / "data" / "sample_docs")
    answer = asyncio.run(pipeline.ask("火星基地的氧气产量是多少？"))
    assert answer == {"answer": REFUSAL, "citations": [], "refused": True}

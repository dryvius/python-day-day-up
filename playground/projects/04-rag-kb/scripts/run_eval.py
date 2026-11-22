"""Run retrieval Hit@K and refusal evaluation as separate metrics."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import TypedDict, cast

from rag_kb.pipeline import RAGPipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class EvalCase(TypedDict):
    id: str
    question: str
    expected_source: str | None
    expect_refusal: bool


async def evaluate(cases_path: Path) -> tuple[int, int, int, int]:
    cases = cast(
        list[EvalCase],
        json.loads(cases_path.read_text(encoding="utf-8")),
    )
    pipeline = RAGPipeline()
    pipeline.ingest(PROJECT_ROOT / "data" / "sample_docs")

    hit_passed = hit_total = refusal_passed = refusal_total = 0
    for case in cases:
        answer = await pipeline.ask(case["question"])
        if case["expect_refusal"]:
            refusal_total += 1
            refusal_passed += int(answer["refused"])
            continue
        hit_total += 1
        sources = {citation["source"] for citation in answer["citations"]}
        hit_passed += int(case["expected_source"] in sources)

    return hit_passed, hit_total, refusal_passed, refusal_total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cases",
        type=Path,
        default=PROJECT_ROOT / "eval" / "cases.json",
    )
    args = parser.parse_args()
    hit_passed, hit_total, refusal_passed, refusal_total = asyncio.run(
        evaluate(args.cases)
    )
    print(f"Retrieval Hit@K: {hit_passed}/{hit_total}")
    print(f"Refusal accuracy: {refusal_passed}/{refusal_total}")
    return int(hit_passed != hit_total or refusal_passed != refusal_total)


if __name__ == "__main__":
    raise SystemExit(main())

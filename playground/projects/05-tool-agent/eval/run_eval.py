from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from tool_agent import FakeLLM, MemoryStore, ToolAgent, ToolRegistry

ROOT = Path(__file__).resolve().parent


def load_cases() -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (ROOT / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


async def evaluate() -> dict[str, Any]:
    cases = load_cases()
    passed = 0
    details: list[dict[str, Any]] = []
    for case in cases:
        agent = ToolAgent(FakeLLM(), ToolRegistry(MemoryStore()))
        result = await agent.run(case["input"], role=case["role"], tenant_id="eval")
        ok = (
            result.status == case["expect_status"]
            and case["answer_contains"] in result.answer
        )
        passed += int(ok)
        details.append({"id": case["id"], "ok": ok, "status": result.status})
    return {
        "total": len(cases),
        "passed": passed,
        "pass_rate": passed / len(cases),
        "details": details,
    }


def main() -> None:
    report = asyncio.run(evaluate())
    baseline = json.loads((ROOT / "baseline.json").read_text(encoding="utf-8"))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["pass_rate"] < baseline["minimum_pass_rate"]:
        raise SystemExit("evaluation regression")


if __name__ == "__main__":
    main()

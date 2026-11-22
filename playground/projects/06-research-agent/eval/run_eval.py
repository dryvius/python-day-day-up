from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from research_agent import (
    BudgetLimits,
    CreateJobRequest,
    FakeLLM,
    MemoryStore,
    ResearchRuntime,
    ToolRegistry,
)
from research_agent.core import BudgetExceeded, JobStore

HERE = Path(__file__).resolve().parent


def load_cases() -> list[dict[str, str]]:
    return [
        json.loads(line)
        for line in (HERE / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


async def evaluate_case(case: dict[str, str]) -> tuple[bool, str]:
    memory = MemoryStore()
    tools = ToolRegistry(memory)
    store = JobStore(memory)
    limits = (
        BudgetLimits(max_steps=1, max_tool_calls=8, max_units=4000)
        if case["kind"] == "budget"
        else BudgetLimits()
    )
    job, _ = store.create(
        CreateJobRequest(
            topic=case["topic"],
            namespace="eval",
            idempotency_key=case["id"],
            budget=limits,
        )
    )
    if case["kind"] == "acl":
        result = await tools.execute(
            "fetch_url",
            {"url": "https://evil.example/private"},
            role="researcher",
            job=job,
        )
        return result.get("error") == "unauthorized", str(result.get("reason"))

    runtime = ResearchRuntime(FakeLLM(), tools)
    if case["kind"] == "gap":
        job.plan = [
            step
            for step in await FakeLLM().plan(job.topic, job.namespace)
            if step.tool != "fetch_url"
        ]
    try:
        await runtime.run(job, auto_approve=True)
    except BudgetExceeded as exc:
        return case["expect"] == "budget_exceeded", str(exc)

    report = job.report or ""
    checks = {
        "citation": "## Citations" in report,
        "material_gap": "材料缺口" in report,
        "refusal": "安全策略拒绝" in report,
    }
    passed = checks.get(case["expect"], False)
    return passed, case["expect"]


async def run() -> dict[str, Any]:
    results = []
    for case in load_cases():
        passed, detail = await evaluate_case(case)
        results.append({"id": case["id"], "passed": passed, "detail": detail})
    passed_count = sum(bool(item["passed"]) for item in results)
    return {
        "case_count": len(results),
        "passed": passed_count,
        "pass_rate": passed_count / len(results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Research Agent evals")
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(run())
    baseline_path = HERE / "baseline.json"
    if args.write_baseline:
        baseline_path.write_text(
            json.dumps(
                {
                    "case_count": report["case_count"],
                    "pass_rate": report["pass_rate"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    regressions = []
    if report["case_count"] < baseline["case_count"]:
        regressions.append("case_count")
    if report["pass_rate"] < baseline["pass_rate"]:
        regressions.append("pass_rate")
    report["regressions"] = regressions
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if regressions or report["passed"] != report["case_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

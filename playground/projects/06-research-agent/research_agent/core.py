from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from research_agent.models import (
    TERMINAL_STATUSES,
    CreateJobRequest,
    JobStatus,
    PlanStep,
    ResearchJob,
)

LOGGER = logging.getLogger("research_agent")
ALLOWED_LOG_FIELDS = frozenset(
    {"event", "trace_id", "job_id", "status", "tool", "reason", "namespace"}
)
BLOCKED_MEMORY_TERMS = (
    "ignore previous",
    "system prompt",
    "developer message",
    "api key",
    "password",
    "密码",
    "sk-",
)


def audit_log(event: str, **fields: str | int | bool | None) -> None:
    record: dict[str, str | int | bool | None] = {"event": event}
    record.update({key: value for key, value in fields.items() if key in ALLOWED_LOG_FIELDS})
    LOGGER.info(json.dumps(record, ensure_ascii=False, sort_keys=True))


class BudgetExceeded(RuntimeError):
    pass


class HumanApprovalRequired(RuntimeError):
    def __init__(self, tool: str) -> None:
        super().__init__(tool)
        self.tool = tool


class JobNotFound(KeyError):
    pass


class IdempotencyConflict(ValueError):
    pass


class SearchKbArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=2, max_length=300)
    namespace: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")


class FetchUrlArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(min_length=8, max_length=500)


class WriteNoteArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=2, max_length=1000)
    namespace: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")


class FinalizeReportArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=2, max_length=200)


class FakeLLM:
    """Deterministic planner/renderer; no network or secret is required."""

    async def plan(self, topic: str, namespace: str) -> list[PlanStep]:
        normalized = topic.casefold()
        if any(term in normalized for term in ("运行 shell", "execute shell", "制作恶意软件")):
            return []
        return [
            PlanStep("search_kb", {"query": topic, "namespace": namespace}),
            PlanStep("fetch_url", {"url": "https://docs.example.com/research-method"}),
            PlanStep(
                "write_note",
                {"text": f"研究主题：{topic}", "namespace": namespace},
            ),
            PlanStep("finalize_report", {"title": topic}, risk="high"),
        ]

    async def render_report(
        self,
        topic: str,
        materials: list[dict[str, str]],
        notes: list[str],
    ) -> str:
        if not materials:
            return (
                f"# {topic}\n\n## 结论\n现有材料不足，无法形成可靠结论。\n\n"
                "## 材料缺口\n- 未检索到可验证来源，需要补充权威资料。\n"
            )
        findings = "\n".join(f"- {item['summary']}" for item in materials)
        citations = "\n".join(
            f"- [{item['citation']}]({item['url']})" for item in materials
        )
        note_line = f"\n\n研究备注：{notes[-1]}" if notes else ""
        return (
            f"# {topic}\n\n## 结论\n{findings}{note_line}\n\n"
            f"## Citations\n{citations}\n"
        )


class Planner(Protocol):
    async def plan(self, topic: str, namespace: str) -> list[PlanStep]: ...

    async def render_report(
        self,
        topic: str,
        materials: list[dict[str, str]],
        notes: list[str],
    ) -> str: ...


@dataclass
class MemoryStore:
    _records: dict[str, list[tuple[datetime, str]]] = field(default_factory=dict)
    _revoked: set[str] = field(default_factory=set)

    def write(self, namespace: str, text: str) -> dict[str, Any]:
        if namespace in self._revoked:
            return {"ok": False, "error": "namespace_revoked"}
        normalized = text.casefold()
        if any(term.casefold() in normalized for term in BLOCKED_MEMORY_TERMS):
            return {"ok": False, "error": "memory_pollution"}
        records = self._records.setdefault(namespace, [])
        records.append((datetime.now(UTC), text))
        return {"ok": True, "record_id": f"note-{len(records)}", "text": text}

    def list(self, namespace: str) -> list[str]:
        return [text for _, text in self._records.get(namespace, [])]

    def revoke(self, namespace: str) -> int:
        self._revoked.add(namespace)
        return len(self._records.pop(namespace, []))

    def purge_before(self, namespace: str, before: datetime) -> int:
        records = self._records.get(namespace, [])
        retained = [(created, text) for created, text in records if created >= before]
        self._records[namespace] = retained
        return len(records) - len(retained)


@dataclass
class AccessPolicy:
    allowed_hosts: frozenset[str] = frozenset({"docs.example.com"})
    role_tools: Mapping[str, frozenset[str]] = field(
        default_factory=lambda: {
            "researcher": frozenset(
                {"search_kb", "fetch_url", "write_note", "finalize_report"}
            )
        }
    )

    def authorize(
        self,
        role: str,
        tool: str,
        arguments: Mapping[str, Any],
        namespace: str,
    ) -> tuple[bool, str]:
        if tool not in self.role_tools.get(role, frozenset()):
            return False, "tool_not_allowed"
        supplied_namespace = arguments.get("namespace")
        if supplied_namespace is not None and supplied_namespace != namespace:
            return False, "namespace_mismatch"
        if tool == "fetch_url":
            parsed = urlparse(str(arguments.get("url", "")))
            if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
                return False, "url_not_allowed"
            if not parsed.path.startswith("/"):
                return False, "path_not_allowed"
        return True, "ok"


ARGUMENT_MODELS: dict[str, type[BaseModel]] = {
    "search_kb": SearchKbArgs,
    "fetch_url": FetchUrlArgs,
    "write_note": WriteNoteArgs,
    "finalize_report": FinalizeReportArgs,
}

KB_DOCUMENTS = [
    {
        "keywords": ("agent", "安全", "safety", "研究", "research"),
        "summary": "生产 Agent 应组合工具 ACL、预算硬顶与人工审批。",
        "citation": "kb:agent-production",
        "url": "kb://agent-production",
    },
    {
        "keywords": ("python", "async", "队列", "queue"),
        "summary": "长任务应通过队列与独立 Worker 执行，并暴露可轮询状态。",
        "citation": "kb:async-jobs",
        "url": "kb://async-jobs",
    },
]


@dataclass
class ToolRegistry:
    memory: MemoryStore
    policy: AccessPolicy = field(default_factory=AccessPolicy)

    async def execute(
        self,
        tool: str,
        raw_arguments: Mapping[str, Any],
        *,
        role: str,
        job: ResearchJob,
    ) -> dict[str, Any]:
        model = ARGUMENT_MODELS.get(tool)
        if model is None:
            return {"ok": False, "error": "unknown_tool"}
        allowed, reason = self.policy.authorize(
            role, tool, raw_arguments, job.namespace
        )
        if not allowed:
            audit_log(
                "tool_denied",
                trace_id=job.trace_id,
                job_id=job.id,
                tool=tool,
                reason=reason,
            )
            return {"ok": False, "error": "unauthorized", "reason": reason}
        try:
            arguments = model.model_validate(raw_arguments)
        except ValidationError as exc:
            return {"ok": False, "error": "validation_error", "detail": exc.errors()}

        if isinstance(arguments, SearchKbArgs):
            terms = arguments.query.casefold().split()
            items = [
                {key: value for key, value in document.items() if key != "keywords"}
                for document in KB_DOCUMENTS
                if any(keyword in arguments.query.casefold() for keyword in document["keywords"])
                or any(term in " ".join(document["keywords"]).casefold() for term in terms)
            ]
            return {"ok": True, "items": items}
        if isinstance(arguments, FetchUrlArgs):
            return {
                "ok": True,
                "item": {
                    "summary": "Mock 网页建议研究结论必须可追溯到明确来源。",
                    "citation": "web:research-method",
                    "url": arguments.url,
                },
            }
        if isinstance(arguments, WriteNoteArgs):
            return self.memory.write(arguments.namespace, arguments.text)
        if isinstance(arguments, FinalizeReportArgs):
            report = await FakeLLM().render_report(job.topic, job.materials, job.notes)
            return {"ok": True, "report": report}
        return {"ok": False, "error": "unsupported_tool"}


def estimate_units(arguments: Mapping[str, Any]) -> int:
    return max(25, len(json.dumps(arguments, ensure_ascii=False)) // 2)


def consume_budget(job: ResearchJob, arguments: Mapping[str, Any]) -> None:
    next_steps = job.usage.steps + 1
    next_calls = job.usage.tool_calls + 1
    next_units = job.usage.units + estimate_units(arguments)
    if next_steps > job.limits.max_steps:
        raise BudgetExceeded("max_steps")
    if next_calls > job.limits.max_tool_calls:
        raise BudgetExceeded("max_tool_calls")
    if next_units > job.limits.max_units:
        raise BudgetExceeded("max_units")
    job.usage.steps = next_steps
    job.usage.tool_calls = next_calls
    job.usage.units = next_units


@dataclass
class ResearchRuntime:
    planner: Planner
    tools: ToolRegistry
    tool_timeout_seconds: float = 2.0

    async def run(self, job: ResearchJob, *, auto_approve: bool = False) -> None:
        if not job.plan:
            job.plan = await self.planner.plan(job.topic, job.namespace)
            if not job.plan:
                job.report = "请求被安全策略拒绝：不执行 shell 或恶意操作。"
                job.status = JobStatus.SUCCEEDED
                job.touch()
                return

        while job.cursor < len(job.plan):
            step = job.plan[job.cursor]
            approved = auto_approve or job.approved_cursor == job.cursor
            if step.risk == "high" and not approved:
                job.pending_tool = step.tool
                job.status = JobStatus.PENDING_HUMAN
                job.touch()
                raise HumanApprovalRequired(step.tool)

            try:
                consume_budget(job, step.arguments)
            except BudgetExceeded as exc:
                job.status = JobStatus.BUDGET_EXCEEDED
                job.error = str(exc)
                job.touch()
                raise
            result = await asyncio.wait_for(
                self.tools.execute(
                    step.tool, step.arguments, role="researcher", job=job
                ),
                timeout=self.tool_timeout_seconds,
            )
            audit_log(
                "tool_completed",
                trace_id=job.trace_id,
                job_id=job.id,
                tool=step.tool,
                status="ok" if result.get("ok") else "rejected",
            )
            if not result.get("ok"):
                job.status = JobStatus.FAILED
                job.error = str(result.get("error", "tool_failed"))
                job.touch()
                return
            if "items" in result:
                job.materials.extend(result["items"])
            if "item" in result:
                job.materials.append(result["item"])
            if step.tool == "write_note":
                job.notes.append(str(result["text"]))
            if "report" in result:
                job.report = str(result["report"])
            job.cursor += 1
            job.approved_cursor = None
            job.pending_tool = None
            job.touch()

        job.status = JobStatus.SUCCEEDED
        job.touch()


@dataclass
class JobStore:
    memory: MemoryStore
    _jobs: dict[str, ResearchJob] = field(default_factory=dict)
    _idempotency: dict[tuple[str, str], tuple[str, str]] = field(default_factory=dict)
    _revoked_namespaces: set[str] = field(default_factory=set)

    def create(self, request: CreateJobRequest) -> tuple[ResearchJob, bool]:
        if request.namespace in self._revoked_namespaces:
            raise ValueError("namespace_revoked")
        key = (request.namespace, request.idempotency_key)
        digest = hashlib.sha256(
            json.dumps(
                {
                    "topic": request.topic,
                    "ttl_seconds": request.ttl_seconds,
                    "budget": request.budget.model_dump(),
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode()
        ).hexdigest()
        existing = self._idempotency.get(key)
        if existing:
            stored_digest, job_id = existing
            if stored_digest != digest:
                raise IdempotencyConflict("idempotency_key_reused")
            return self._jobs[job_id], True
        job = ResearchJob(
            topic=request.topic,
            namespace=request.namespace,
            idempotency_key=request.idempotency_key,
            limits=request.budget,
            ttl_seconds=request.ttl_seconds,
        )
        self._jobs[job.id] = job
        self._idempotency[key] = (digest, job.id)
        return job, False

    def get(self, job_id: str, namespace: str) -> ResearchJob:
        job = self._jobs.get(job_id)
        if job is None or job.namespace != namespace:
            raise JobNotFound(job_id)
        if job.status not in TERMINAL_STATUSES and datetime.now(UTC) >= job.expires_at:
            job.status = JobStatus.EXPIRED
            job.error = "ttl_expired"
            job.touch()
        return job

    def revoke(self, job_id: str, namespace: str) -> ResearchJob:
        job = self.get(job_id, namespace)
        if job.status not in TERMINAL_STATUSES:
            job.status = JobStatus.REVOKED
            job.error = "revoked_by_user"
            job.touch()
        return job

    def revoke_namespace(self, namespace: str) -> int:
        self._revoked_namespaces.add(namespace)
        changed = 0
        for job in self._jobs.values():
            if job.namespace == namespace and job.status not in TERMINAL_STATUSES:
                job.status = JobStatus.REVOKED
                job.error = "namespace_revoked"
                job.touch()
                changed += 1
        self.memory.revoke(namespace)
        return changed

    def purge_expired(self, namespace: str) -> int:
        now = datetime.now(UTC)
        expired_ids = [
            job_id
            for job_id, job in self._jobs.items()
            if job.namespace == namespace and now >= job.expires_at
        ]
        for job_id in expired_ids:
            job = self._jobs.pop(job_id)
            self._idempotency.pop((job.namespace, job.idempotency_key), None)
        return len(expired_ids)


@dataclass
class JobRunner:
    store: JobStore
    runtime: ResearchRuntime
    worker_count: int = 1
    queue: asyncio.Queue[str] = field(default_factory=asyncio.Queue)
    _tasks: list[asyncio.Task[None]] = field(default_factory=list)
    _stopping: bool = False

    async def start(self) -> None:
        self._stopping = False
        self._tasks = [
            asyncio.create_task(self._worker(), name=f"research-worker-{index}")
            for index in range(self.worker_count)
        ]

    async def stop(self) -> None:
        self._stopping = True
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def enqueue(self, job: ResearchJob) -> None:
        if job.status not in TERMINAL_STATUSES:
            job.status = JobStatus.QUEUED
            job.touch()
            await self.queue.put(job.id)

    async def approve(self, job_id: str, namespace: str) -> ResearchJob:
        job = self.store.get(job_id, namespace)
        if job.status != JobStatus.PENDING_HUMAN:
            raise ValueError("job_not_pending_human")
        job.approved_cursor = job.cursor
        await self.enqueue(job)
        return job

    async def _worker(self) -> None:
        while not self._stopping:
            job_id = await self.queue.get()
            try:
                job = self.store._jobs.get(job_id)
                if job is None or job.status in TERMINAL_STATUSES:
                    continue
                job.status = JobStatus.RUNNING
                job.touch()
                audit_log(
                    "job_running",
                    trace_id=job.trace_id,
                    job_id=job.id,
                    status=job.status,
                    namespace=job.namespace,
                )
                try:
                    await self.runtime.run(job)
                except HumanApprovalRequired as exc:
                    audit_log(
                        "approval_required",
                        trace_id=job.trace_id,
                        job_id=job.id,
                        tool=exc.tool,
                        status=job.status,
                    )
                except BudgetExceeded as exc:
                    job.status = JobStatus.BUDGET_EXCEEDED
                    job.error = str(exc)
                    job.touch()
                # Worker 是 Job 与未分类 runtime 故障的边界：统一落 FAILED，
                # 避免异常击穿消费循环；对外只暴露稳定的 internal_error。
                except Exception:
                    job.status = JobStatus.FAILED
                    job.error = "internal_error"
                    job.touch()
                    audit_log(
                        "job_failed",
                        trace_id=job.trace_id,
                        job_id=job.id,
                        status=job.status,
                        reason="internal_error",
                    )
            finally:
                self.queue.task_done()


def build_services() -> tuple[JobStore, JobRunner]:
    memory = MemoryStore()
    store = JobStore(memory)
    runtime = ResearchRuntime(FakeLLM(), ToolRegistry(memory))
    return store, JobRunner(store, runtime)

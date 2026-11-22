from __future__ import annotations

import ast
import json
import operator
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, ClassVar, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

Message = dict[str, Any]
ToolHandler = Callable[[BaseModel, str], Awaitable[Any]]


class LLMClient(Protocol):
    async def complete(
        self,
        messages: list[Message],
        tools: list[Message] | None = None,
        **kwargs: Any,
    ) -> Message: ...


class CalculatorArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expression: str = Field(min_length=1, max_length=200)


class GetTimeArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timezone: str = Field(default="UTC", pattern=r"^UTC$")


class SearchMemoryArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=200)
    limit: int = Field(default=3, ge=1, le=10)


class RememberArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=500)
    idempotency_key: str = Field(min_length=1, max_length=128)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_model: type[BaseModel]
    handler: ToolHandler
    side_effect: bool = False

    def schema(self) -> Message:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.args_model.model_json_schema(),
            },
        }


class MemoryStore:
    """Self-contained tenant-scoped store with a defensive write gate."""

    BLOCKED_TERMS = ("ignore previous", "system prompt", "password", "密码", "sk-")

    def __init__(self) -> None:
        self._records: dict[str, list[str]] = {}

    def write(self, tenant_id: str, text: str) -> dict[str, Any]:
        normalized = text.casefold()
        if any(term.casefold() in normalized for term in self.BLOCKED_TERMS):
            return {"ok": False, "error": "memory_pollution"}
        records = self._records.setdefault(tenant_id, [])
        records.append(text)
        return {"ok": True, "record_id": f"mem-{len(records)}", "text": text}

    def search(self, tenant_id: str, query: str, limit: int) -> list[str]:
        needle = query.casefold()
        return [
            item
            for item in self._records.get(tenant_id, [])
            if needle in item.casefold()
        ][:limit]


_BINARY_OPERATORS: Mapping[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY_OPERATORS: Mapping[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        return _BINARY_OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate(node.operand))
    raise ValueError("unsupported_expression")


def calculate(expression: str) -> int | float:
    value = _evaluate(ast.parse(expression, mode="eval"))
    return int(value) if value.is_integer() else value


class AccessPolicy:
    ROLE_TOOLS: ClassVar[dict[str, frozenset[str]]] = {
        "viewer": frozenset({"calculator", "get_time", "search_memory"}),
        "editor": frozenset({"calculator", "get_time", "search_memory", "remember"}),
    }

    def authorize(
        self,
        *,
        role: str,
        tool_name: str,
        args: Mapping[str, Any],
        tenant_id: str,
    ) -> tuple[bool, str]:
        if tool_name not in self.ROLE_TOOLS.get(role, frozenset()):
            return False, "tool_not_allowed"
        supplied_tenant = args.get("tenant_id")
        if supplied_tenant is not None and supplied_tenant != tenant_id:
            return False, "tenant_mismatch"
        expression = str(args.get("expression", ""))
        if tool_name == "calculator" and len(expression) > 200:
            return False, "expression_too_long"
        return True, "ok"


@dataclass
class ToolRegistry:
    memory: MemoryStore
    policy: AccessPolicy = field(default_factory=AccessPolicy)
    _specs: dict[str, ToolSpec] = field(init=False, default_factory=dict)
    _idempotency: dict[tuple[str, str, str], tuple[str, Any]] = field(
        init=False, default_factory=dict
    )

    def __post_init__(self) -> None:
        async def calculator(args: BaseModel, tenant_id: str) -> Any:
            _ = tenant_id
            parsed = CalculatorArgs.model_validate(args)
            return {"value": calculate(parsed.expression)}

        async def get_time(args: BaseModel, tenant_id: str) -> Any:
            _ = tenant_id
            GetTimeArgs.model_validate(args)
            return {"timezone": "UTC", "iso": datetime.now(UTC).replace(microsecond=0).isoformat()}

        async def search_memory(args: BaseModel, tenant_id: str) -> Any:
            parsed = SearchMemoryArgs.model_validate(args)
            return {"items": self.memory.search(tenant_id, parsed.query, parsed.limit)}

        async def remember(args: BaseModel, tenant_id: str) -> Any:
            parsed = RememberArgs.model_validate(args)
            return self.memory.write(tenant_id, parsed.text)

        self.register(ToolSpec("calculator", "Evaluate basic arithmetic.", CalculatorArgs, calculator))
        self.register(ToolSpec("get_time", "Return current UTC time.", GetTimeArgs, get_time))
        self.register(ToolSpec("search_memory", "Search tenant-scoped memory.", SearchMemoryArgs, search_memory))
        self.register(ToolSpec("remember", "Persist safe tenant memory.", RememberArgs, remember, True))

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._specs:
            raise ValueError(f"duplicate tool: {spec.name}")
        self._specs[spec.name] = spec

    def definitions(self) -> list[Message]:
        return [spec.schema() for spec in self._specs.values()]

    async def execute(
        self,
        name: str,
        raw_args: Any,
        *,
        role: str,
        tenant_id: str,
    ) -> dict[str, Any]:
        spec = self._specs.get(name)
        if spec is None:
            return {"ok": False, "error": "unknown_tool", "tool": name}
        try:
            candidate = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError as exc:
            return {"ok": False, "error": "invalid_json", "detail": str(exc)}
        if not isinstance(candidate, dict):
            return {"ok": False, "error": "arguments_not_object"}
        allowed, reason = self.policy.authorize(
            role=role, tool_name=name, args=candidate, tenant_id=tenant_id
        )
        if not allowed:
            return {"ok": False, "error": "unauthorized", "reason": reason}
        try:
            args = spec.args_model.model_validate(candidate)
        except ValidationError as exc:
            return {"ok": False, "error": "validation_error", "detail": exc.errors()}

        key = getattr(args, "idempotency_key", None)
        cache_key = (tenant_id, name, str(key))
        args_digest = json.dumps(args.model_dump(), ensure_ascii=False, sort_keys=True)
        if spec.side_effect and key and cache_key in self._idempotency:
            stored_digest, stored_result = self._idempotency[cache_key]
            if stored_digest != args_digest:
                return {"ok": False, "error": "idempotency_conflict"}
            return {"ok": True, "result": stored_result, "replayed": True}
        try:
            result = await spec.handler(args, tenant_id)
        # Registry 是不可信工具与 Agent runtime 的故障边界；第三方 handler
        # 可抛出任意运行时异常，统一转成结构化 tool_error，避免击穿主循环。
        except Exception as exc:
            return {"ok": False, "error": "tool_error", "detail": str(exc)}
        if isinstance(result, dict) and result.get("ok") is False:
            return result
        if spec.side_effect and key:
            self._idempotency[cache_key] = (args_digest, result)
        return {"ok": True, "result": result, "replayed": False}


class FakeLLM:
    """Deterministic async assistant-message fake for demos, tests, and eval."""

    async def complete(
        self,
        messages: list[Message],
        tools: list[Message] | None = None,
        **kwargs: Any,
    ) -> Message:
        _ = tools, kwargs
        if messages and messages[-1].get("role") == "tool":
            return {"role": "assistant", "content": f"工具结果：{messages[-1]['content']}"}
        text = str(messages[-1].get("content", "")) if messages else ""
        call: tuple[str, dict[str, Any]] | None = None
        if "计算" in text:
            call = ("calculator", {"expression": text.split("计算", 1)[1].strip() or "1+1"})
        elif "时间" in text:
            call = ("get_time", {"timezone": "UTC"})
        elif "搜索记忆" in text:
            call = ("search_memory", {"query": text.split("搜索记忆", 1)[1].strip() or "偏好"})
        elif "记住" in text:
            value = text.split("记住", 1)[1].strip()
            call = ("remember", {"text": value, "idempotency_key": f"remember:{value}"})
        if call is None:
            return {"role": "assistant", "content": f"ECHO:{text}"}
        name, args = call
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": "call-1",
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)},
            }],
        }


@dataclass
class AgentResult:
    answer: str
    status: str
    messages: list[Message]
    trace: list[Message]


@dataclass
class ToolAgent:
    llm: LLMClient
    registry: ToolRegistry
    max_steps: int = 5

    async def run(
        self,
        user_input: str,
        *,
        role: str = "viewer",
        tenant_id: str = "default",
    ) -> AgentResult:
        messages: list[Message] = [{"role": "user", "content": user_input}]
        trace: list[Message] = []
        for step in range(1, self.max_steps + 1):
            assistant = await self.llm.complete(messages, tools=self.registry.definitions())
            messages.append(assistant)
            calls = assistant.get("tool_calls") or []
            trace.append({"event": "llm", "step": step, "tool_calls": len(calls)})
            if not calls:
                return AgentResult(str(assistant.get("content") or ""), "completed", messages, trace)
            for call in calls:
                function = call.get("function") or {}
                name = str(function.get("name") or "")
                payload = await self.registry.execute(
                    name,
                    function.get("arguments"),
                    role=role,
                    tenant_id=tenant_id,
                )
                tool_message = {
                    "role": "tool",
                    "tool_call_id": str(call.get("id") or "missing-id"),
                    "content": json.dumps(payload, ensure_ascii=False, default=str),
                }
                messages.append(tool_message)
                trace.append({"event": "tool", "step": step, "tool": name, "ok": payload["ok"]})
        return AgentResult("达到最大工具步数，已停止。", "max_steps", messages, trace)


@dataclass
class MCPBridge:
    """In-process MCP-shaped bridge; execution still passes through registry ACL."""

    registry: ToolRegistry

    async def list_tools(self) -> list[Message]:
        return self.registry.definitions()

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        role: str,
        tenant_id: str,
    ) -> dict[str, Any]:
        return await self.registry.execute(name, arguments, role=role, tenant_id=tenant_id)

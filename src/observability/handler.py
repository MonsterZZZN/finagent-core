"""
可观测性 callback handler。

继承 LangChain BaseCallbackHandler，重写钩子捕获全链路调用：
- LLM 调用：on_chat_model_start / on_llm_end / on_llm_error（延迟、token、错误）
- 工具调用：on_tool_start / on_tool_end / on_tool_error（延迟、错误）

用 run_id 作为 span_id，parent_run_id 作为 parent_span_id，自动构建调用树。
每个用户请求创建一个 handler 实例（带唯一 trace_id），挂到 agent.ainvoke 的 callbacks。
callbacks 会沿调用树传播，所以主 Agent + 工具 + 子 Agent 的调用都会被捕获。
"""

import time
from datetime import datetime
from typing import Any, Optional

from langchain_core.callbacks.base import BaseCallbackHandler

from observability.store import trace_store


class ObservabilityHandler(BaseCallbackHandler):
    """全链路埋点 handler。"""

    def __init__(
        self,
        trace_id: str,
        session_id: str = "",
        channel: str = "",
        service: str = "finagent-core",
    ) -> None:
        self.trace_id = trace_id
        self.session_id = session_id
        self.channel = channel
        self.service = service
        # run_id -> {开始时间, 类型, 名称, 父run_id}
        self._starts: dict[str, dict] = {}

    # ---------- LLM ----------
    def on_chat_model_start(self, serialized, messages, *, run_id, parent_run_id=None, **kwargs):
        self._starts[str(run_id)] = {
            "t": time.time(),
            "type": "llm",
            "name": self._model_name(serialized, kwargs),
            "parent": parent_run_id,
        }

    def on_llm_start(self, serialized, prompts, *, run_id, parent_run_id=None, **kwargs):
        # 非 chat 模型兜底
        self._starts[str(run_id)] = {
            "t": time.time(),
            "type": "llm",
            "name": self._model_name(serialized, kwargs),
            "parent": parent_run_id,
        }

    def on_llm_end(self, response, *, run_id, **kwargs):
        info = self._starts.pop(str(run_id), None)
        if not info:
            return
        usage = self._extract_usage(response)
        self._record(info, run_id, "success", usage)

    def on_llm_error(self, error, *, run_id, **kwargs):
        info = self._starts.pop(str(run_id), None)
        if not info:
            return
        self._record(info, run_id, "error", {
            "error_type": type(error).__name__,
            "error_message": str(error)[:500],
        })

    # ---------- 工具 ----------
    def on_tool_start(self, serialized, input_str, *, run_id, parent_run_id=None, **kwargs):
        name = (serialized or {}).get("name", "unknown")
        self._starts[str(run_id)] = {
            "t": time.time(),
            "type": "tool",
            "name": name,
            "parent": parent_run_id,
        }

    def on_tool_end(self, output, *, run_id, **kwargs):
        info = self._starts.pop(str(run_id), None)
        if not info:
            return
        self._record(info, run_id, "success", {})

    def on_tool_error(self, error, *, run_id, **kwargs):
        info = self._starts.pop(str(run_id), None)
        if not info:
            return
        self._record(info, run_id, "error", {
            "error_type": type(error).__name__,
            "error_message": str(error)[:500],
        })

    # ---------- 辅助 ----------
    def _model_name(self, serialized: Optional[dict], kwargs: dict) -> str:
        if serialized and isinstance(serialized.get("kwargs"), dict):
            m = serialized["kwargs"].get("model") or serialized["kwargs"].get("model_name")
            if m:
                return m
        inv = kwargs.get("invocation_params") or {}
        return inv.get("model") or inv.get("model_name") or "unknown"

    def _extract_usage(self, response: Any) -> dict:
        """从 LLMResult 里提取 token 用量（兼容多种格式）。"""
        usage = {}
        try:
            out = getattr(response, "llm_output", None) or {}
            tu = out.get("token_usage") or out.get("usage") or {}
            if tu:
                usage = {
                    "prompt_tokens": tu.get("prompt_tokens", 0),
                    "completion_tokens": tu.get("completion_tokens", 0),
                    "total_tokens": tu.get("total_tokens", 0),
                }
            else:
                # 退化到 generations 的 usage_metadata
                msg = response.generations[0][0].message
                um = getattr(msg, "usage_metadata", None) or {}
                if um:
                    usage = {
                        "prompt_tokens": um.get("input_tokens", 0),
                        "completion_tokens": um.get("output_tokens", 0),
                        "total_tokens": um.get("total_tokens", 0),
                    }
        except Exception:  # noqa: BLE001
            pass
        return usage

    def _record(self, info: dict, run_id, status: str, extra: dict) -> None:
        latency_ms = int((time.time() - info["t"]) * 1000)
        doc = {
            "trace_id": self.trace_id,
            "span_id": str(run_id),
            "parent_span_id": str(info["parent"]) if info.get("parent") else None,
            "type": info["type"],
            "name": info["name"],
            "session_id": self.session_id,
            "channel": self.channel,
            "service": self.service,
            "latency_ms": latency_ms,
            "status": status,
            "ts": datetime.utcnow(),
        }
        doc.update(extra or {})
        trace_store.save(doc)

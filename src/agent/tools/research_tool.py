"""
深度研究委派工具。

调用独立的 finagent-research 服务（HTTP /research/stream）做深度研究。

两种模式：
- 异步模式（飞书等真实渠道）：后台跑研究，立即返回"正在研究"，
  完成后通过 notifier 把报告推回当前会话
- 同步模式（CLI/测试，无 notifier）：直接等结果返回

notifier 由网关在处理消息时通过 contextvar 注入——agent 层不直接依赖网关。
"""

import asyncio
import json
from contextvars import ContextVar
from typing import Awaitable, Callable, Optional

import httpx
from langchain_core.tools import tool

from agent import config

# 由网关设置：一个 async 函数，把文本推送到"当前会话"
current_notifier: ContextVar[Optional[Callable[[str], Awaitable[None]]]] = ContextVar(
    "current_notifier", default=None
)


async def _run_research(query: str, max_iterations: int = 1) -> str:
    """调用 finagent-research /research/stream，收完 SSE 返回最终报告。"""
    base = config.RESEARCH_SERVICE_URL or "http://127.0.0.1:8001"
    payload = {"query": query, "max_iterations": max_iterations}

    async with httpx.AsyncClient(timeout=600) as client:
        async with client.stream("POST", f"{base}/research/stream", json=payload) as resp:
            event = None
            async for line in resp.aiter_lines():
                line = line.strip()
                if line.startswith("event:"):
                    event = line[6:].strip()
                elif line.startswith("data:"):
                    data = line[5:].strip()
                    if not data:
                        continue
                    obj = json.loads(data)
                    if event == "complete":
                        return obj.get("report", "") or "（研究未产出报告）"
                    if event == "error":
                        return f"深度研究出错：{obj.get('message')}"
    return "深度研究服务无响应。"


async def _research_and_notify(query: str, notifier: Callable[[str], Awaitable[None]]) -> None:
    """后台任务：跑研究，完成后推送报告。"""
    try:
        report = await _run_research(query)
        await notifier(f"📑 您的深度研究「{query}」完成：\n\n{report}")
    except Exception as e:  # noqa: BLE001
        await notifier(f"深度研究出错：{e}")


@tool
async def delegate_to_research(query: str) -> str:
    """
    委派给深度研究引擎（独立的 finagent-research 服务）。

    适用于需要多步搜索 + 综合分析的深度研究问题，例如：
    "深度分析贵州茅台的投资价值"、"对比白酒三巨头的竞争格局"、
    "研究新能源汽车行业的投资机会"。

    研究耗时较长（数分钟），会异步进行。

    Args:
        query: 用户的研究问题。

    Returns:
        异步模式返回"正在研究"提示；同步模式直接返回研究报告。
    """
    notifier = current_notifier.get()
    if notifier is not None:
        # 异步：后台研究，立即返回，完成后推送
        asyncio.create_task(_research_and_notify(query, notifier))
        return (
            "已为用户启动后台深度研究（约 2-3 分钟完成，完成后报告会自动推送给用户）。"
            "请回复用户：正在深度研究，稍后将发送完整报告，请耐心等待。"
        )
    # 同步：直接等结果（CLI/测试）
    return await _run_research(query)

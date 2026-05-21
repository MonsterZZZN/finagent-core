"""
Agent Runtime —— 平台无关的运行时封装。

把主 Agent 包成统一接口 `run_for_session(session_key, user_message, context)`，
任何渠道（飞书 / WebUI / 钉钉）的网关都通过这个接口跑 Agent，
完全不关心 Agent 内部细节。这是"一个 Agent 服务多端"的关键。

会话记忆：用 session_key 作为 thread_id，配合 checkpointer 实现多轮对话记忆。
（当前用内存 checkpointer；后续可换 MongoDB 持久化）
"""

from typing import Optional

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from agent.main_agent import build_main_agent


class AgentRuntime:
    """平台无关的 Agent 运行时。"""

    def __init__(self) -> None:
        # 内存 checkpointer：进程内多轮对话记忆（重启清空）
        # TODO: 生产可换 langgraph-checkpoint-mongodb 持久化
        self._checkpointer = MemorySaver()
        self._agent = build_main_agent(checkpointer=self._checkpointer)

    async def run_for_session(
        self,
        session_key: str,
        user_message: str,
        context: Optional[dict] = None,
    ) -> str:
        """
        在指定会话下运行 Agent，返回回复文本。

        Args:
            session_key: 会话标识（同一会话多轮对话共用，决定记忆归属）
            user_message: 用户消息
            context: 运行时上下文（用户身份/持仓等，预留，后续注入）

        Returns:
            Agent 的回复文本
        """
        config = {"configurable": {"thread_id": session_key}}
        result = await self._agent.ainvoke(
            {"messages": [HumanMessage(content=user_message)]},
            config=config,
        )
        return result["messages"][-1].content


# 全局单例（整个进程共用一个 Runtime / Agent / checkpointer）
_runtime: Optional[AgentRuntime] = None


def get_runtime() -> AgentRuntime:
    """获取全局 Runtime 单例。"""
    global _runtime
    if _runtime is None:
        _runtime = AgentRuntime()
    return _runtime

"""
主 Agent（Orchestrator）。

架构：LangGraph create_react_agent + Agent-as-Tool。
- 各专家子 Agent 被包成"委派工具"（delegate_to_*）
- 主 Agent 判断意图后调用对应委派工具
- 加新专家 = 加新委派工具，主 Agent 几乎不用改

当前已接入：
- delegate_to_risk_analyst（风险分析）
后续会加：market-pulse / report-writer / research-proxy
"""

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from agent.config import get_main_model
from agent.memory.prompts import system_prompt
from agent.subagents.risk_analyst import build_risk_analyst

# 子 Agent 单例（避免每次委派都重建，省时省 token）
_risk_analyst = None


def _get_risk_analyst():
    global _risk_analyst
    if _risk_analyst is None:
        _risk_analyst = build_risk_analyst()
    return _risk_analyst


@tool
async def delegate_to_risk_analyst(request: str) -> str:
    """
    委派给风险分析专家。

    适用于：持仓体检、风险评估、VaR、波动率、集中度、
    期货保证金占用、强平距离等。

    Args:
        request: 必须包含用户的完整需求 + 完整持仓数据
                （股票组合或期货账户的 JSON，原样附上）。

    Returns:
        风险分析专家生成的风险评估报告（文本）。
    """
    agent = _get_risk_analyst()
    result = await agent.ainvoke({"messages": [HumanMessage(content=request)]})
    return result["messages"][-1].content


def build_main_agent(checkpointer=None):
    """
    构建主 Agent。

    Args:
        checkpointer: 会话记忆存储（传入则支持多轮对话记忆）

    Returns:
        可调用 .ainvoke 的主 Agent
    """
    model = get_main_model()
    return create_react_agent(
        model=model,
        tools=[delegate_to_risk_analyst],
        prompt=system_prompt,
        checkpointer=checkpointer,
    )

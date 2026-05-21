"""
risk-analyst 子 Agent 端到端测试。

给它一个持仓，看它：
1. 调用 analyze_portfolio_risk 工具（确定性算数字）
2. 用大模型把数字解读成风险报告

这是第一次大模型真正"作为 Agent 跑起来"——会调用 DeepSeek（消耗少量额度）。

用法（服务器上，激活 venv，确保 .env 里 DEEPSEEK_API_KEY 已配）：
    python test_risk_agent.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from langchain_core.messages import HumanMessage  # noqa: E402

from agent.subagents.risk_analyst import build_risk_analyst  # noqa: E402

# 给一个结构化持仓（白酒重仓，故意集中）
USER_MESSAGE = """帮我做持仓风险评估。我的持仓数据（JSON）：
[
  {"ticker": "600519", "name": "贵州茅台", "market_value": 300000, "industry": "白酒"},
  {"ticker": "000858", "name": "五粮液",   "market_value": 200000, "industry": "白酒"},
  {"ticker": "300750", "name": "宁德时代", "market_value": 100000, "industry": "电池"}
]
"""


async def main():
    print("=" * 60)
    print("构建 risk-analyst 子 Agent...")
    agent = build_risk_analyst()

    print("发送持仓，等待 Agent 分析（会调工具 + 调大模型，约 10-30 秒）...\n")
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=USER_MESSAGE)]}
    )

    # 打印完整对话过程（看 Agent 怎么调工具、怎么解读）
    print("=" * 60)
    print("【Agent 执行过程】")
    print("=" * 60)
    for m in result["messages"]:
        role = m.type
        if role == "tool":
            content = (m.content or "")[:200]
            print(f"\n🔧 [工具返回] {content}...")
        elif role == "ai":
            if m.content:
                print(f"\n🤖 [Agent] {m.content}")
            # 工具调用
            tool_calls = getattr(m, "tool_calls", None)
            if tool_calls:
                for tc in tool_calls:
                    print(f"\n➡️  [调用工具] {tc['name']}")
        elif role == "human":
            print(f"👤 [用户] {m.content[:80]}...")

    print()
    print("=" * 60)
    print("✅ risk-analyst 子 Agent 测试完成（步骤6验证通过）")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

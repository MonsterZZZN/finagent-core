"""
market-pulse 子 Agent + 主 Agent 路由 测试。

验证：
1. 直接测 market-pulse 子 Agent（问大盘）
2. 测主 Agent 能否把市场问题路由给 market-pulse

用法（服务器上，激活 venv，确保 .env 配了 DEEPSEEK_API_KEY）：
    python test_market_pulse.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from langchain_core.messages import HumanMessage  # noqa: E402

from agent.subagents.market_pulse import build_market_pulse  # noqa: E402
from gateway.runtime import get_runtime  # noqa: E402


async def main():
    # ---- 1. 直接测子 Agent ----
    print("=" * 60)
    print("【1】直接测 market-pulse 子 Agent：今天大盘怎么样？")
    print("=" * 60)
    agent = build_market_pulse()
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="今天大盘整体怎么样？热点板块有哪些？")]}
    )
    print(f"🤖 {result['messages'][-1].content}\n")

    # ---- 2. 测主 Agent 路由 ----
    print("=" * 60)
    print("【2】测主 Agent 路由：把市场问题委派给 market-pulse")
    print("=" * 60)
    rt = get_runtime()
    reply = await rt.run_for_session("test-mp-001", "今天市场行情怎么样？")
    print(f"🤖 {reply}\n")

    print("=" * 60)
    print("✅ market-pulse 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

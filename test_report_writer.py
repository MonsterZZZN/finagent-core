"""
report-writer 子 Agent + 主 Agent 路由 测试。

验证：
1. 直接测 report-writer 生成早盘简报
2. 测主 Agent 把"生成早盘简报"路由给 report-writer

用法（服务器上，激活 venv，确保 .env 配了 DEEPSEEK_API_KEY）：
    python test_report_writer.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from langchain_core.messages import HumanMessage  # noqa: E402

from agent.subagents.report_writer import build_report_writer  # noqa: E402
from gateway.runtime import get_runtime  # noqa: E402


async def main():
    # ---- 1. 直接测子 Agent ----
    print("=" * 60)
    print("【1】直接测 report-writer：生成早盘简报")
    print("=" * 60)
    print("（要调多个数据工具 + 大模型，约 20-40 秒）...\n")
    agent = build_report_writer()
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="帮我生成一份今日早盘简报。")]}
    )
    print(f"🤖\n{result['messages'][-1].content}\n")

    # ---- 2. 测主 Agent 路由 ----
    print("=" * 60)
    print("【2】测主 Agent 路由：把'早盘简报'委派给 report-writer")
    print("=" * 60)
    rt = get_runtime()
    reply = await rt.run_for_session("test-rw-001", "给我来一份早盘简报")
    print(f"🤖\n{reply}\n")

    print("=" * 60)
    print("✅ report-writer 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

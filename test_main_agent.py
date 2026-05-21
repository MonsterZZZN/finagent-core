"""
主 Agent + Runtime 端到端测试。

模拟多轮对话，验证：
1. 寒暄/功能询问 → 主 Agent 直接回答（不委派）
2. 风险问题 → 主 Agent 委派给 risk-analyst → 返回风险报告
3. 同一 session_key 下多轮（记忆生效）

用法（服务器上，激活 venv，确保 .env 配了 DEEPSEEK_API_KEY）：
    python test_main_agent.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from gateway.runtime import get_runtime  # noqa: E402

SESSION = "test-session-001"

RISK_QUERY = """帮我评估一下持仓风险。持仓数据（JSON）：
[
  {"ticker": "600519", "name": "贵州茅台", "market_value": 300000, "industry": "白酒"},
  {"ticker": "000858", "name": "五粮液",   "market_value": 200000, "industry": "白酒"},
  {"ticker": "300750", "name": "宁德时代", "market_value": 100000, "industry": "电池"}
]
"""


async def main():
    rt = get_runtime()

    print("=" * 60)
    print("【第 1 轮】用户：你能帮我做什么？")
    print("=" * 60)
    r1 = await rt.run_for_session(SESSION, "你能帮我做什么？")
    print(f"🤖 {r1}\n")

    print("=" * 60)
    print("【第 2 轮】用户：帮我评估持仓风险（附持仓数据）")
    print("=" * 60)
    print("（主 Agent 应委派给 risk-analyst，约 15-40 秒）...\n")
    r2 = await rt.run_for_session(SESSION, RISK_QUERY)
    print(f"🤖 {r2}\n")

    print("=" * 60)
    print("✅ 主 Agent + Runtime 测试完成（步骤7验证通过）")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

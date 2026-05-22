"""
finagent-core → finagent-research 集成测试（同步模式）。

直接调研究工具的底层函数 _run_research，验证 core 能成功调用 research 服务。
（同步模式，不涉及异步推送）

前置：
1. finagent-research 服务已启动（端口 8001）
2. finagent-core 的 .env 配了 RESEARCH_SERVICE_URL=http://127.0.0.1:8001

用法（finagent-core 目录，激活 venv）：
    python test_research_integration.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from agent.tools.research_tool import _run_research  # noqa: E402


async def main():
    print("=" * 60)
    print("调用 finagent-research 做深度研究（约 1-2 分钟）...")
    print("=" * 60)
    report = await _run_research("分析贵州茅台的投资价值", max_iterations=1)
    print(report[:1500])
    print("...(报告略)")
    print("\n" + "=" * 60)
    if report and "出错" not in report and "无响应" not in report:
        print("✅ core → research 集成成功（R7 集成验证通过）")
    else:
        print("⚠️  调用失败，检查 research 服务是否启动 + RESEARCH_SERVICE_URL 配置")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

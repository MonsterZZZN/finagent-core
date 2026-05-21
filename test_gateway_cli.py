"""
网关 + CLI 渠道 测试入口。

启动网关，注册 CLI 渠道，在命令行和 Agent 对话。
验证整条网关链路：
  CLI 输入 → InboundMessage → Gateway.handle_inbound
  → Runtime.run_for_session → 主 Agent → (委派 risk-analyst)
  → 回复 → CLIChannel.send → 命令行打印

用法（服务器上，激活 venv，确保 .env 配了 DEEPSEEK_API_KEY）：
    python test_gateway_cli.py

可以试着输入：
  - 你能帮我做什么？
  - 帮我评估持仓风险。持仓JSON：[{"ticker":"600519","name":"贵州茅台","market_value":300000,"industry":"白酒"}]
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from gateway.channels.cli import CLIChannel  # noqa: E402
from gateway.gateway import Gateway  # noqa: E402


async def main():
    gateway = Gateway()
    cli = CLIChannel(on_inbound=gateway.handle_inbound)
    gateway.register_channel(cli)
    # CLI 渠道的 start() 会进入输入循环，直到用户退出
    await gateway.start_all()
    print("\n再见！")


if __name__ == "__main__":
    asyncio.run(main())

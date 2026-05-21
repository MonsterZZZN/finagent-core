"""
飞书机器人启动入口。

启动网关 + 飞书渠道，常驻运行。之后在飞书里 @机器人 或私聊，
就能和 FinAgent 对话（持仓风险评估等）。

用法（服务器上，激活 venv，确保 .env 配了 FEISHU_APP_ID/SECRET 和 DEEPSEEK_API_KEY）：
    python run_feishu.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from gateway.channels.feishu import FeishuChannel  # noqa: E402
from gateway.gateway import Gateway  # noqa: E402


async def main():
    gateway = Gateway()
    feishu = FeishuChannel(on_inbound=gateway.handle_inbound)
    gateway.register_channel(feishu)

    await gateway.start_all()

    print("=" * 56)
    print("FinAgent 飞书机器人运行中（Ctrl+C 退出）")
    print("在飞书里私聊机器人，或群里 @机器人 试试：")
    print('  帮我评估持仓风险。持仓JSON：[{"ticker":"600519",...}]')
    print("=" * 56)

    # 保持事件循环运行（飞书消息通过后台线程回调进来）
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await gateway.stop_all()
        print("\n已退出")


if __name__ == "__main__":
    asyncio.run(main())

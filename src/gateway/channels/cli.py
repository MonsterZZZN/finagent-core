"""
CLI 渠道 —— 命令行收发消息。

用途：本地验证网关流程，不依赖任何外部平台。
它实现了 ChannelPlugin 接口，和未来的飞书渠道是同一套契约：
  - start()：开启命令行输入循环
  - send()：把回复打印到命令行
  - 收到输入 → 转成 InboundMessage → 回调 on_inbound

这样在接飞书之前，就能在命令行把"网关 → Agent → 回复"整条链路跑通。
"""

import asyncio

from gateway.contracts import InboundHandler, InboundMessage, OutboundMessage


class CLIChannel:
    """命令行渠道。"""

    def __init__(self, on_inbound: InboundHandler) -> None:
        self._on_inbound = on_inbound
        self._running = False

    @property
    def id(self) -> str:
        return "cli"

    async def start(self) -> None:
        """开启命令行输入循环（输入 exit/quit 退出）。"""
        self._running = True
        print("\n" + "=" * 56)
        print("CLI 渠道已启动 —— 直接输入消息和 Agent 对话")
        print("（输入 exit 或 quit 退出）")
        print("=" * 56)

        while self._running:
            # 在线程里读 stdin，避免阻塞事件循环
            text = await asyncio.to_thread(input, "\n你: ")
            if text.strip().lower() in ("exit", "quit"):
                self._running = False
                break
            if not text.strip():
                continue

            msg = InboundMessage(
                channel="cli",
                sender_id="local_user",
                conversation_id="cli-conv-001",
                text=text,
                chat_type="dm",
            )
            # 交给网关 → Agent；回复会通过 send() 打印
            await self._on_inbound(msg)

    async def stop(self) -> None:
        self._running = False

    async def send(self, conversation_id: str, message: OutboundMessage) -> None:
        """把 Agent 回复打印到命令行。"""
        print(f"\n🤖 Agent: {message.text}")

"""
Gateway —— 网关调度中心。

借鉴 openclaw 的 _handle_inbound 设计：把任意渠道标准化后的消息，
统一交给 Agent Runtime 执行，再把回复原路发回对应渠道。

核心方法 handle_inbound：
  标准化消息 → 算 session_key → runtime.run_for_session → channel.send

Gateway 完全不关心消息来自哪个平台——这是"一个 Agent 服务多端"的关键。
"""

from gateway.contracts import InboundMessage, OutboundMessage
from gateway.registry import ChannelRegistry
from gateway.runtime import get_runtime


def resolve_session_key(message: InboundMessage) -> str:
    """
    由消息推导会话键（决定记忆归属）。

    用 渠道 + 会话 组合：同一渠道同一会话的多轮对话共用记忆。
    """
    return f"{message.channel}:{message.conversation_id}"


class Gateway:
    """网关：连接各渠道与 Agent Runtime。"""

    def __init__(self) -> None:
        self.registry = ChannelRegistry()
        self.runtime = get_runtime()

    def register_channel(self, channel) -> None:
        """注册一个渠道。"""
        self.registry.register(channel)

    async def handle_inbound(self, message: InboundMessage) -> None:
        """
        处理任意渠道标准化后的入站消息，跑完 Agent 后回写原渠道。

        这里接收的已经是标准 InboundMessage，不含平台细节，
        因此对 CLI / 飞书 / 未来其他渠道的处理完全一致。
        """
        session_key = resolve_session_key(message)

        # 进入统一 Agent 主线（不关心平台）
        reply_text = await self.runtime.run_for_session(
            session_key=session_key,
            user_message=message.text,
            context={
                "channel": message.channel,
                "sender_id": message.sender_id,
                "conversation_id": message.conversation_id,
            },
        )

        # 回复交给对应渠道（飞书会用 reply_to_id 回复原消息）
        channel = self.registry.get(message.channel)
        if channel:
            reply_to = message.raw.get("message_id")
            outbound = OutboundMessage(text=reply_text, reply_to_id=reply_to)
            await channel.send(message.conversation_id, outbound)

    async def start_all(self) -> None:
        """启动所有已注册渠道。"""
        for ch in self.registry.all():
            await ch.start()

    async def stop_all(self) -> None:
        """停止所有渠道。"""
        for ch in self.registry.all():
            await ch.stop()

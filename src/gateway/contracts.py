"""
网关契约层。

借鉴 openclaw 的"端口-适配器"设计：定义统一的消息结构和渠道接口，
让 Agent 核心与具体平台（飞书/钉钉/WebUI）完全解耦。

- InboundMessage：任意平台的入站消息，标准化后的统一格式
- OutboundMessage：发往任意平台的出站消息
- ChannelPlugin：所有渠道必须实现的接口（协议）

新增一个平台 = 写一个实现 ChannelPlugin 的类，Gateway/Agent 一行不改。
"""

from typing import Any, Awaitable, Callable, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class InboundMessage(BaseModel):
    """标准化入站消息（任意平台 → 统一格式）。"""

    channel: str                                  # 渠道标识：cli / feishu / ...
    sender_id: str                                # 发送者 ID
    conversation_id: str                          # 会话 ID（决定回复发到哪）
    text: str = ""                                # 消息文本
    account_id: str = "default"                   # 多账号支持（暂用 default）
    chat_type: str = "dm"                         # dm（单聊）/ group（群聊）
    raw: dict[str, Any] = Field(default_factory=dict)  # 平台原始数据（含 message_id 等）


class OutboundMessage(BaseModel):
    """标准化出站消息（统一格式 → 任意平台）。"""

    text: str = ""
    reply_to_id: Optional[str] = None             # 回复某条消息（群聊里有用）


# 渠道收到消息后回调此函数，把标准化消息交给 Gateway
InboundHandler = Callable[[InboundMessage], Awaitable[None]]


@runtime_checkable
class ChannelPlugin(Protocol):
    """所有渠道必须实现的接口。

    约定：渠道在构造时接收一个 on_inbound 回调，收到平台消息并标准化后调用它。
    """

    @property
    def id(self) -> str:
        """渠道唯一标识，如 'cli' / 'feishu'。"""
        ...

    async def start(self) -> None:
        """启动渠道（建立连接 / 订阅事件 / 开启监听）。"""
        ...

    async def stop(self) -> None:
        """停止渠道。"""
        ...

    async def send(self, conversation_id: str, message: OutboundMessage) -> None:
        """向指定会话发送消息。"""
        ...

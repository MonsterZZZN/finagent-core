"""
渠道注册表。

持有所有已注册的渠道（ChannelPlugin），供 Gateway 按 id 查找、统一启停。
"""

from gateway.contracts import ChannelPlugin


class ChannelRegistry:
    """渠道注册中心。"""

    def __init__(self) -> None:
        self._channels: dict[str, ChannelPlugin] = {}

    def register(self, channel: ChannelPlugin) -> None:
        self._channels[channel.id] = channel

    def get(self, channel_id: str) -> ChannelPlugin | None:
        return self._channels.get(channel_id)

    def all(self) -> list[ChannelPlugin]:
        return list(self._channels.values())

    def ids(self) -> list[str]:
        return list(self._channels.keys())

"""
飞书渠道 —— 用官方 lark-oapi SDK 接入飞书机器人。

收消息：WebSocket 长连接（lark.ws.Client）——不需要公网域名，适合服务器部署
发消息：飞书 Open API（lark.Client）

实现 ChannelPlugin 契约，和 CLI 渠道完全一致——网关/Agent 一行不用改。

线程模型（关键）：
- lark 的长连接是同步的，跑在自己的线程里
- 收到消息时在 lark 线程回调 → 用 run_coroutine_threadsafe 调度到主事件循环
- 发消息是同步 API → 用 asyncio.to_thread 包装，不阻塞事件循环
"""

import asyncio
import json
import threading
from typing import Optional

import lark_oapi as lark
from lark_oapi.api.im.v1 import (
    CreateMessageRequest,
    CreateMessageRequestBody,
    P2ImMessageReceiveV1,
    ReplyMessageRequest,
    ReplyMessageRequestBody,
)

from agent import env_utils
from gateway.contracts import InboundHandler, InboundMessage, OutboundMessage


class FeishuChannel:
    """飞书渠道（lark-oapi 长连接）。"""

    def __init__(self, on_inbound: InboundHandler) -> None:
        self._on_inbound = on_inbound
        self._app_id = env_utils.FEISHU_APP_ID
        self._app_secret = env_utils.FEISHU_APP_SECRET
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws_client = None
        # 发消息用的 API 客户端
        self._api = (
            lark.Client.builder()
            .app_id(self._app_id)
            .app_secret(self._app_secret)
            .build()
        )

    @property
    def id(self) -> str:
        return "feishu"

    # ---------- 收消息 ----------
    def _on_message_receive(self, data: P2ImMessageReceiveV1) -> None:
        """lark 在自己的线程里回调。标准化后调度到主事件循环执行 Agent。"""
        try:
            event = data.event
            message = event.message

            # 解析文本（飞书文本消息 content 是 JSON 字符串）
            content = json.loads(message.content or "{}")
            text = (content.get("text") or "").strip()
            # 群聊里去掉 @机器人 的占位符
            text = text.replace("@_user_1", "").replace("@_all", "").strip()

            chat_type = "group" if message.chat_type == "group" else "dm"

            # 群聊只在被 @ 时响应，避免读取群里所有消息
            mentions = getattr(message, "mentions", None) or []
            if chat_type == "group" and not mentions:
                return

            if not text:
                return

            sender_id = "unknown"
            try:
                sender_id = event.sender.sender_id.open_id
            except Exception:
                pass

            msg = InboundMessage(
                channel="feishu",
                sender_id=sender_id,
                conversation_id=message.chat_id,
                text=text,
                chat_type=chat_type,
                raw={"message_id": message.message_id},
            )

            if self._loop and self._on_inbound:
                # 把异步回调调度到主事件循环（跨线程）
                asyncio.run_coroutine_threadsafe(self._on_inbound(msg), self._loop)
        except Exception as e:  # noqa: BLE001
            print(f"[feishu] 处理消息出错: {e}")

    async def start(self) -> None:
        """启动飞书长连接（在后台线程跑同步的 ws client）。"""
        if not self._app_id or not self._app_secret:
            print("[feishu] ❌ 缺少 FEISHU_APP_ID / FEISHU_APP_SECRET，飞书渠道未启动")
            return

        self._loop = asyncio.get_running_loop()

        event_handler = (
            lark.EventDispatcherHandler.builder("", "")
            .register_p2_im_message_receive_v1(self._on_message_receive)
            .build()
        )
        self._ws_client = lark.ws.Client(
            self._app_id,
            self._app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.INFO,
        )

        # ws_client.start() 是阻塞的，放到 daemon 线程跑
        threading.Thread(target=self._ws_client.start, daemon=True).start()
        print("[feishu] ✅ 飞书长连接已启动，等待消息...")

    async def stop(self) -> None:
        # lark ws client 无干净 stop，daemon 线程随进程退出
        pass

    # ---------- 发消息 ----------
    async def send(self, conversation_id: str, message: OutboundMessage) -> None:
        """发送文本消息；有 reply_to_id 则回复原消息。"""

        def _do_send():
            content = json.dumps({"text": message.text})
            if message.reply_to_id:
                req = (
                    ReplyMessageRequest.builder()
                    .message_id(message.reply_to_id)
                    .request_body(
                        ReplyMessageRequestBody.builder()
                        .content(content)
                        .msg_type("text")
                        .build()
                    )
                    .build()
                )
                return self._api.im.v1.message.reply(req)
            else:
                req = (
                    CreateMessageRequest.builder()
                    .receive_id_type("chat_id")
                    .request_body(
                        CreateMessageRequestBody.builder()
                        .receive_id(conversation_id)
                        .msg_type("text")
                        .content(content)
                        .build()
                    )
                    .build()
                )
                return self._api.im.v1.message.create(req)

        resp = await asyncio.to_thread(_do_send)
        if not resp.success():
            print(f"[feishu] 发送失败: code={resp.code} msg={resp.msg}")

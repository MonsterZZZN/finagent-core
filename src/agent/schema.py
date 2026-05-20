"""
数据结构定义。

包含：运行时上下文（FinancialContext）、用户偏好、对话/SSE 模型。
用 dataclass 定义运行时上下文，用 pydantic 定义 API 模型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# 一、运行时上下文
# ============================================================
@dataclass
class FinancialContext:
    """
    运行时上下文，调用 Agent 时由调用方传入（不持久化）。
    用于让 Agent 知道"当前是谁、他的持仓和偏好"。
    """
    # 身份（必填）
    user_id: str
    username: str

    # 角色与风险偏好
    user_role: str = "retail"          # retail / trader / researcher / fund_manager
    risk_tolerance: str = "moderate"   # conservative / moderate / aggressive
    base_currency: str = "CNY"

    # 持仓与自选（运行时注入）
    portfolio: Optional[Dict[str, Any]] = None
    watchlist: List[str] = field(default_factory=list)

    # 行为偏好
    preferred_output: Optional[str] = None   # table / chart / markdown
    push_threshold: float = 0.5              # 异动推送阈值

    # 合规标记
    is_licensed_advisor: bool = False        # 是否持投顾牌照


# ============================================================
# 二、用户长期偏好
# ============================================================
@dataclass
class UserPreferences:
    """
    用户长期偏好，存在 /memories/{user_id}/preferences.md。
    随对话逐步学习更新，使助手越来越个性化。
    """
    preferred_output: Optional[str] = None       # table / chart / markdown
    preferred_chart_type: Optional[str] = None   # bar / line / pie ...
    base_currency: str = "CNY"
    preferred_language: str = "zh"
    watchlist: List[str] = field(default_factory=list)
    recent_queries: List[str] = field(default_factory=list)


# ============================================================
# 三、对话 API 模型
# ============================================================
class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., description="用户消息")
    thread_id: Optional[str] = Field(None, description="会话 ID，为空则新建")


class Message(BaseModel):
    """一条消息"""
    role: str = Field(..., description="user / assistant / tool")
    content: str = Field("", description="消息内容")
    created_at: datetime = Field(default_factory=datetime.now)
    source: Optional[str] = Field(None, description="来源：main 或子 Agent 名")


# ============================================================
# 四、SSE 流式事件（步骤 8 会细化各类型）
# ============================================================
class StreamEvent(BaseModel):
    """流式事件基础模型"""
    type: str = Field(..., description="token / tool_start / tool_result / done / error")
    content: str = Field("", description="内容")
    source: str = Field("main", description="来源")

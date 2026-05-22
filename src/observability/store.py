"""
追踪记录存储。

把每条 span（一次 LLM/工具调用）写入 MongoDB 的 agent_traces 集合。
观测不能拖垮业务：保存失败只打日志，不抛异常。
"""

from pymongo import MongoClient

from agent import config


class TraceStore:
    """span 记录存储（MongoDB）。"""

    def __init__(self) -> None:
        self._col = None

    @property
    def col(self):
        """惰性创建集合连接。"""
        if self._col is None:
            client = MongoClient(config.MONGODB_URI)
            self._col = client[config.MONGODB_DB_NAME]["agent_traces"]
            # 常用查询字段建索引（首次自动建）
            try:
                self._col.create_index("trace_id")
                self._col.create_index("session_id")
                self._col.create_index([("ts", -1)])
            except Exception:  # noqa: BLE001
                pass
        return self._col

    def save(self, doc: dict) -> None:
        """保存一条 span 记录。"""
        try:
            self.col.insert_one(doc)
        except Exception as e:  # noqa: BLE001
            print(f"[observability] 保存追踪记录失败: {e}")


# 全局单例
trace_store = TraceStore()

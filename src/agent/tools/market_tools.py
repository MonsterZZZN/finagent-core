"""
市场行情工具（LangChain @tool，in-process）。

把 market_data_tools 里的行情获取函数包装成 Agent 可调用的工具，
供 market-pulse 子 Agent 使用。
"""

import sys
from pathlib import Path

from langchain_core.tools import tool

_SRC_ROOT = Path(__file__).resolve().parents[2]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from mcp_server.tools.market_data_tools import (  # noqa: E402
    fetch_hot_sectors,
    fetch_index,
    fetch_market_overview,
    fetch_quote,
)


@tool
async def get_index_snapshot() -> dict:
    """获取主要指数实时快照（上证指数、深证成指、创业板指、沪深300）。"""
    return await fetch_index()


@tool
async def get_market_overview() -> dict:
    """获取大盘概览：上涨/下跌家数、涨停/跌停数、市场活跃度。"""
    return await fetch_market_overview()


@tool
async def get_hot_sectors() -> dict:
    """获取今日领涨/领跌行业板块。"""
    return await fetch_hot_sectors()


@tool
async def get_stock_quote(symbol: str) -> dict:
    """
    查询单只 A 股股票实时行情。

    Args:
        symbol: 6 位股票代码，如 600519（贵州茅台）
    """
    return await fetch_quote(symbol)

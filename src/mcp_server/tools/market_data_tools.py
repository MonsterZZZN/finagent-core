"""
行情数据 MCP 工具组（基于 AKShare 免费数据源）。

设计：
- "取数据的逻辑"（fetch_* 函数）与"注册为 MCP 工具"（register_*）分离，
  便于脱离 MCP 服务单独测试。
- AKShare 是同步库，用 asyncio.to_thread 包装，避免阻塞事件循环。
- 工具命名遵循 {组名}_{动作}，本组前缀 market_data_。

提供工具：
- market_data_quote  : 单只股票实时行情
- market_data_kline  : 股票 K 线历史
- market_data_index  : 主要指数实时快照
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

GROUP_NAME = "market_data"


async def _retry(func, *args, retries: int = 3, delay: float = 1.0, **kwargs):
    """
    带退避重试地在线程里执行同步函数。

    AKShare 数据源（东方财富等）偶发连接中断，连续请求时尤甚。
    用重试 + 递增延迟来抵抗瞬时网络错误。
    """
    last_err = None
    for attempt in range(retries):
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                await asyncio.sleep(delay * (attempt + 1))  # 1s, 2s, ...
    raise last_err


# ============================================================
# 一、核心数据获取逻辑（可独立测试）
# ============================================================

async def fetch_quote(symbol: str) -> dict:
    """
    获取单只 A 股股票实时行情。

    Args:
        symbol: 6 位股票代码，如 "600519"（贵州茅台）
    """
    import akshare as ak
    try:
        # stock_bid_ask_em 返回单只股票的盘口 + 关键行情，数据量小
        df = await _retry(ak.stock_bid_ask_em, symbol=symbol)
        # df 为 item/value 两列，转成字典
        data = dict(zip(df["item"], df["value"]))
        return {
            "symbol": symbol,
            "last": data.get("最新"),
            "change_pct": data.get("涨幅"),
            "change": data.get("涨跌"),
            "open": data.get("今开"),
            "high": data.get("最高"),
            "low": data.get("最低"),
            "prev_close": data.get("昨收"),
            "volume": data.get("总手"),
            "amount": data.get("金额"),
            "turnover_rate": data.get("换手"),
            "volume_ratio": data.get("量比"),
            "limit_up": data.get("涨停"),
            "limit_down": data.get("跌停"),
        }
    except Exception as e:
        return {"symbol": symbol, "error": f"获取行情失败: {e}"}


async def fetch_kline(
    symbol: str,
    period: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "qfq",
) -> dict:
    """
    获取股票 K 线历史数据。

    Args:
        symbol: 6 位股票代码
        period: daily / weekly / monthly
        start_date: 开始日期 YYYYMMDD，默认 60 天前
        end_date: 结束日期 YYYYMMDD，默认今天
        adjust: qfq(前复权) / hfq(后复权) / ""(不复权)
    """
    import akshare as ak
    try:
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")

        df = await _retry(
            ak.stock_zh_a_hist,
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )
        # 只返回最近 30 根，避免数据过大
        bars = df.tail(30).to_dict("records")
        return {"symbol": symbol, "period": period, "count": len(bars), "bars": bars}
    except Exception as e:
        return {"symbol": symbol, "error": f"获取K线失败: {e}"}


async def fetch_index() -> dict:
    """获取主要指数实时快照（上证/深证/创业板/沪深300）。"""
    import akshare as ak
    try:
        df = await _retry(ak.stock_zh_index_spot_em, symbol="沪深重要指数")
        majors = ["上证指数", "深证成指", "创业板指", "沪深300"]
        result = []
        for _, row in df.iterrows():
            if row.get("名称") in majors:
                result.append({
                    "name": row.get("名称"),
                    "code": row.get("代码"),
                    "last": row.get("最新价"),
                    "change_pct": row.get("涨跌幅"),
                    "change": row.get("涨跌额"),
                })
        return {"indices": result}
    except Exception as e:
        return {"error": f"获取指数失败: {e}"}


async def fetch_market_overview() -> dict:
    """获取大盘概览：上涨/下跌家数、涨停/跌停数、市场活跃度。"""
    import akshare as ak
    try:
        df = await _retry(ak.stock_market_activity_legu)
        # 返回 item/value 两列
        data = dict(zip(df["item"], df["value"]))
        return {
            "上涨家数": data.get("上涨"),
            "下跌家数": data.get("下跌"),
            "平盘": data.get("平盘"),
            "涨停": data.get("涨停"),
            "跌停": data.get("跌停"),
            "停牌": data.get("停牌"),
            "活跃度": data.get("活跃度"),
            "统计日期": data.get("统计日期"),
        }
    except Exception as e:
        return {"error": f"获取大盘概览失败: {e}"}


async def fetch_hot_sectors(top_n: int = 5) -> dict:
    """获取今日领涨/领跌行业板块。"""
    import akshare as ak
    try:
        df = await _retry(ak.stock_board_industry_name_em)
        df = df.sort_values("涨跌幅", ascending=False)
        cols = ["板块名称", "涨跌幅"]
        top = df.head(top_n)[cols].to_dict("records")
        bottom = df.tail(top_n)[cols].to_dict("records")
        return {"领涨板块": top, "领跌板块": bottom}
    except Exception as e:
        return {"error": f"获取热点板块失败: {e}"}


# ============================================================
# 二、注册为 MCP 工具
# ============================================================

def register_market_data_tools(mcp):
    """把行情工具注册到 MCP Server（mcp 为 FastMCP 实例）。"""

    @mcp.tool(name=f"{GROUP_NAME}_quote")
    async def market_data_quote(symbol: str) -> dict:
        """
        查询单只 A 股股票的实时行情（最新价、涨跌幅、量额、换手等）。

        Args:
            symbol: 6 位股票代码，如 600519（贵州茅台）
        """
        return await fetch_quote(symbol)

    @mcp.tool(name=f"{GROUP_NAME}_kline")
    async def market_data_kline(
        symbol: str,
        period: str = "daily",
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq",
    ) -> dict:
        """
        查询股票 K 线历史数据。

        Args:
            symbol: 6 位股票代码
            period: daily / weekly / monthly，默认 daily
            start_date: 开始日期 YYYYMMDD，可选（默认 60 天前）
            end_date: 结束日期 YYYYMMDD，可选（默认今天）
            adjust: qfq(前复权,默认) / hfq(后复权) / 空(不复权)
        """
        return await fetch_kline(symbol, period, start_date, end_date, adjust)

    @mcp.tool(name=f"{GROUP_NAME}_index")
    async def market_data_index() -> dict:
        """查询主要指数实时快照（上证指数、深证成指、创业板指、沪深300）。"""
        return await fetch_index()

    @mcp.tool(name=f"{GROUP_NAME}_overview")
    async def market_data_overview() -> dict:
        """查询大盘概览：上涨/下跌家数、涨停/跌停数、市场活跃度。"""
        return await fetch_market_overview()

    @mcp.tool(name=f"{GROUP_NAME}_hot_sectors")
    async def market_data_hot_sectors() -> dict:
        """查询今日领涨/领跌行业板块。"""
        return await fetch_hot_sectors()

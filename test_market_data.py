"""
行情工具测试脚本。

直接调用数据获取逻辑（fetch_*），验证 AKShare 能取到真实行情。
不需要启动 MCP Server，专注验证"取数据"这件事本身。

用法（服务器上，激活 venv，先 pip install akshare pandas）：
    python test_market_data.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mcp_server.tools.market_data_tools import fetch_quote, fetch_kline, fetch_index  # noqa: E402


async def main():
    print("=" * 56)
    print("【1】实时行情：贵州茅台 (600519)")
    print("=" * 56)
    quote = await fetch_quote("600519")
    if "error" in quote:
        print(f"  ❌ {quote['error']}")
    else:
        print(f"  最新价: {quote['last']}  涨跌幅: {quote['change_pct']}%")
        print(f"  今开: {quote['open']}  最高: {quote['high']}  最低: {quote['low']}")
        print(f"  成交额: {quote['amount']}  换手率: {quote['turnover_rate']}%")

    print()
    print("=" * 56)
    print("【2】K线：贵州茅台 最近日K（取最后5根）")
    print("=" * 56)
    kline = await fetch_kline("600519")
    if "error" in kline:
        print(f"  ❌ {kline['error']}")
    else:
        print(f"  共取到 {kline['count']} 根K线，最后5根：")
        for bar in kline["bars"][-5:]:
            print(f"    {bar.get('日期')}  收盘:{bar.get('收盘')}  涨跌幅:{bar.get('涨跌幅')}%")

    print()
    print("=" * 56)
    print("【3】主要指数实时快照")
    print("=" * 56)
    idx = await fetch_index()
    if "error" in idx:
        print(f"  ❌ {idx['error']}")
    else:
        for i in idx["indices"]:
            print(f"  {i['name']} ({i['code']})  最新:{i['last']}  涨跌幅:{i['change_pct']}%")

    print()
    print("=" * 56)
    print("✅ 行情工具测试完成（上面若全部有数据，步骤4验证通过）")
    print("=" * 56)


if __name__ == "__main__":
    asyncio.run(main())

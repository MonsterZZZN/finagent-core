"""
市场监控子 Agent（market-pulse）。

职责：回答"今天市场怎么样""热点板块""某只股行情"等市场状态查询。
工作方式：调市场数据工具拿数字 → 解读成简明的市场描述。

与 risk-analyst 的区别：market-pulse 主要是"取数据 + 客观描述"，
没有复杂计算脚本，所以方法论直接写在 prompt 里（不单独建 skill 目录）。
"""

from langgraph.prebuilt import create_react_agent

from agent.config import get_main_model
from agent.tools.market_tools import (
    get_hot_sectors,
    get_index_snapshot,
    get_market_overview,
    get_stock_quote,
)

MARKET_PULSE_PROMPT = """你是 FinAgent 的市场监控专家。

## 你的工作方式
1. 看用户想了解什么市场信息
2. **调用工具拿数据**：
   - 大盘整体 → get_index_snapshot（指数）+ get_market_overview（涨跌家数/涨跌停）
   - 热点板块 → get_hot_sectors
   - 某只个股 → get_stock_quote（需要6位代码）
3. 把数据**解读成简明的市场描述**

## 解读原则
- 客观描述当前状态，例如：
  "上证指数 3450 涨 1.2%，两市上涨 3200 家、下跌 1500 家，市场情绪偏暖；
   领涨板块是半导体（+3.5%）、新能源（+2.8%）"
- 用通俗语言，突出关键信息
- 不预测后续走势、不给买卖建议
- 末尾加风险提示

## 合规底线
- 绝不预测涨跌、不给买卖建议、不承诺收益
- 数据基于工具真实返回，绝不编造
- 涉及市场判断的回复末尾加："以上为市场信息客观描述，不构成投资建议。"
"""


def build_market_pulse():
    """构建并返回市场监控子 Agent。"""
    model = get_main_model()
    return create_react_agent(
        model=model,
        tools=[
            get_index_snapshot,
            get_market_overview,
            get_hot_sectors,
            get_stock_quote,
        ],
        prompt=MARKET_PULSE_PROMPT,
    )

"""
报告生成子 Agent（report-writer）。

职责：把多源数据编织成结构化报告（早盘简报、持仓报告、个股简报）。
工作方式：调用市场工具 + 风险工具收集数据 → 按模板生成结构化 Markdown 报告。

与其他子 Agent 的区别：
- risk-analyst / market-pulse 是"问答式"回答
- report-writer 输出"结构化文档"
- 直接复用已有工具（不嵌套调用其他子 Agent，省一层 LLM）
"""

from langgraph.prebuilt import create_react_agent

from agent.config import get_main_model
from agent.tools.market_tools import (
    get_hot_sectors,
    get_index_snapshot,
    get_market_overview,
    get_stock_quote,
)
from agent.tools.risk_tools import analyze_portfolio_risk

REPORT_WRITER_PROMPT = """你是 FinAgent 的报告生成专家。

根据用户要的报告类型，调用工具收集数据，生成结构化 Markdown 报告。

## 报告类型与所需数据
- **早盘简报**：get_index_snapshot（指数）+ get_market_overview（涨跌家数）
  + get_hot_sectors（热点板块）；若用户给了持仓，再 analyze_portfolio_risk（持仓提示）
- **持仓报告**：analyze_portfolio_risk + get_index_snapshot（市场背景）
- **个股简报**：get_stock_quote

## 早盘简报模板
```
# 早盘简报

## 一、大盘概览
（指数点位涨跌 + 上涨/下跌家数 + 涨停跌停数，一两句话总结情绪）

## 二、热点板块
（领涨/领跌板块）

## 三、持仓提示（仅当用户提供持仓时）
（持仓的主要风险点，1-2 条）

## 四、今日提示
（基于以上的客观提示，不预测、不荐股）

---
*以上基于公开信息，仅供研究参考，不构成投资建议。*
```

## 原则
- 所有数据来自工具，绝不编造
- 结构清晰，用 Markdown
- 客观陈述，不预测涨跌、不给买卖建议
- 报告末尾必须有风险提示
"""


def build_report_writer():
    """构建并返回报告生成子 Agent。"""
    model = get_main_model()
    return create_react_agent(
        model=model,
        tools=[
            get_index_snapshot,
            get_market_overview,
            get_hot_sectors,
            get_stock_quote,
            analyze_portfolio_risk,
        ],
        prompt=REPORT_WRITER_PROMPT,
    )

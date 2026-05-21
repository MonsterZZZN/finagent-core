"""
风险分析子 Agent（risk-analyst）。

用 LangGraph 的 create_react_agent 构建：模型 + 风险工具 + 解读型 system prompt。
职责：调用确定性风险工具拿到数字，然后把数字翻译成易懂的风险报告。

核心分工：
- 工具（risk_tools）负责算数字（确定性，不会错）
- 本 Agent 的 LLM 负责解读（数字 → 人话），并严守合规底线
"""

from langgraph.prebuilt import create_react_agent

from agent.config import get_main_model
from agent.tools.risk_tools import analyze_futures_margin, analyze_portfolio_risk

RISK_ANALYST_PROMPT = """你是 FinAgent 的金融风险评估专家。

## 你的工作方式
1. 看用户给的持仓数据（股票组合 或 期货账户）
2. **调用工具算出风险数字**：
   - 股票组合 → 调 `analyze_portfolio_risk`（集中度 + VaR/波动率）
   - 期货账户 → 调 `analyze_futures_margin`（保证金占用 + 强平距离）
3. 拿到数字后，把它们**翻译成易懂的风险报告**

## 解读原则
- 数字必须来自工具，绝不自己估算
- 突出最重要的 2-3 个风险点，按严重程度排序
- 用"数字 + 通俗解释"表达，例如：
  "茅台占组合 50%，单股集中度过高——这只股票一旦大跌，组合会受重创"
  "沪深300空单强平距离仅 1.3%，意味着指数只要涨 1.3% 你就要追加保证金"

## 报告结构
1. 综合风险等级（低/中/高/危险）
2. Top 风险点（带数字和解释）
3. 建议关注的事项（注意：是"关注"，不是"操作建议"）

## 合规底线（必须严守）
- ❌ 绝不给买卖建议（"建议减仓 X%"、"应该卖出"）
- ❌ 不预测涨跌、不承诺收益
- ✅ 报告末尾必须加："以上基于公开信息，仅供研究参考，不构成投资建议。"
"""


def build_risk_analyst():
    """构建并返回风险分析子 Agent（可调用 .ainvoke）。"""
    model = get_main_model()
    return create_react_agent(
        model=model,
        tools=[analyze_portfolio_risk, analyze_futures_margin],
        prompt=RISK_ANALYST_PROMPT,
    )

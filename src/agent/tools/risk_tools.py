"""
风险分析工具（LangChain @tool，in-process，无沙箱）。

设计原则（核心）：数字用确定性脚本算，LLM 只负责解读。
- 计算逻辑复用 skills/finance/risk-analysis/scripts/ 下的纯函数（单一事实来源）
- 这里把它们包装成 LangChain 工具，供子 Agent 直接调用

提供工具：
- analyze_portfolio_risk : 股票组合风险（集中度 + VaR/波动率，内部自动取K线）
- analyze_futures_margin : 期货账户风险（保证金占用 + 强平距离 + 方向性）
"""

import asyncio
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.tools import tool

# ---- 复用风险计算脚本（单一事实来源）----
_SRC_ROOT = Path(__file__).resolve().parents[2]          # src/
_SKILL_SCRIPTS = _SRC_ROOT / "skills" / "finance" / "risk-analysis" / "scripts"


def _load_script(name: str):
    """用 importlib 加载带连字符路径下的脚本。"""
    spec = importlib.util.spec_from_file_location(name, _SKILL_SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_conc = _load_script("concentration")
_var = _load_script("var_calculator")
_margin = _load_script("margin_analyzer")

# ---- 复用行情获取函数 ----
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
from mcp_server.tools.market_data_tools import fetch_kline  # noqa: E402


@tool
async def analyze_portfolio_risk(positions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    对股票持仓做全面风险分析（确定性计算，返回数字供解读）。

    会计算：集中度（单股/行业 HHI）、组合年化波动率、1日95% VaR/CVaR。
    内部会自动获取各持仓的历史K线来计算收益率，无需调用方提供行情。

    Args:
        positions: 持仓列表，每项形如
            {"ticker": "600519", "name": "贵州茅台", "market_value": 300000, "industry": "白酒"}
            ticker 和 market_value 必填。

    Returns:
        {"concentration": {...}, "var": {...}}
    """
    # 1) 集中度（纯计算）
    concentration = _conc.calc_concentration(positions)

    # 2) 取各股K线 → 算组合日收益率 → VaR
    closes: Dict[str, list] = {}
    for p in positions:
        k = await fetch_kline(p["ticker"])
        if "error" not in k and k.get("bars"):
            closes[p["ticker"]] = [b["收盘"] for b in k["bars"]]
        await asyncio.sleep(0.8)  # 对数据源友好，降低限流概率

    var_result: Dict[str, Any] = {}
    if len(closes) == len(positions) and positions:
        total = sum(p.get("market_value", 0) for p in positions)
        weights = {p["ticker"]: p.get("market_value", 0) / total for p in positions}
        n = min(len(v) for v in closes.values())
        port_returns = []
        for i in range(1, n):
            r = 0.0
            for t, cl in closes.items():
                r += weights[t] * (cl[-n + i] / cl[-n + i - 1] - 1)
            port_returns.append(r)
        var_result = _var.calc_var(port_returns)
    else:
        var_result = {"error": "部分持仓K线获取失败，VaR 暂不可用"}

    return {"concentration": concentration, "var": var_result}


@tool
def analyze_futures_margin(account: Dict[str, Any]) -> Dict[str, Any]:
    """
    对期货账户做保证金风险分析（确定性计算，返回数字供解读）。

    会计算：保证金占用率、各合约强平距离、最危险合约、单品种敞口、方向性集中。

    Args:
        account: 期货账户，形如
            {"account_equity": 200000, "positions": [
                {"contract":"RB2510","name":"螺纹钢","direction":"long","lots":5,
                 "entry_price":3250,"current_price":3180,"multiplier":10,"margin_rate":0.10}
            ]}

    Returns:
        保证金风险指标字典
    """
    return _margin.analyze_margin(account)

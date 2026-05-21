"""
风险分析 Skill 测试脚本（端到端，使用真实数据）。

流程：
1. 定义一个样本持仓（茅台/五粮液/宁德，故意集中在白酒+电池）
2. 用集中度脚本算集中度
3. 用真实 K 线算各股收益率 → 合成组合收益率 → 算 VaR/波动率
4. 对照阈值，输出风险提示

用法（服务器上，激活 venv）：
    python test_risk.py
"""

import asyncio
import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mcp_server.tools.market_data_tools import fetch_kline  # noqa: E402


def _load_script(rel_path: str, mod_name: str):
    """用 importlib 加载带连字符路径下的脚本（无法直接 import）。"""
    spec = importlib.util.spec_from_file_location(mod_name, ROOT / rel_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

SKILL = "src/skills/finance/risk-analysis"
conc = _load_script(f"{SKILL}/scripts/concentration.py", "concentration")
varc = _load_script(f"{SKILL}/scripts/var_calculator.py", "var_calculator")

# 样本持仓：故意集中（白酒占大头）
SAMPLE = [
    {"ticker": "600519", "name": "贵州茅台", "market_value": 300000, "industry": "白酒"},
    {"ticker": "000858", "name": "五粮液",   "market_value": 200000, "industry": "白酒"},
    {"ticker": "300750", "name": "宁德时代", "market_value": 100000, "industry": "电池"},
]


def check_threshold(value: float, key: str, thresholds: dict) -> str:
    """对照阈值分档。"""
    t = thresholds.get(key, {})
    if value >= t.get("danger", 999):
        return "🔴 危险"
    if value >= t.get("warn", 999):
        return "🟠 警示"
    if value >= t.get("watch", 999):
        return "🟡 关注"
    return "🟢 正常"


async def main():
    # 加载阈值
    with open(ROOT / f"{SKILL}/data/thresholds.yaml", encoding="utf-8") as f:
        thresholds = yaml.safe_load(f)

    print("=" * 56)
    print("【1】集中度分析")
    print("=" * 56)
    c = conc.calc_concentration(SAMPLE)
    print(f"  持仓数: {c['num_positions']}  总市值: {c['total_value']}")
    print(f"  单股最大: {c['max_single']['ticker']} {c['max_single']['weight']*100:.1f}%  "
          f"{check_threshold(c['max_single']['weight'], 'single_stock_concentration', thresholds)}")
    print(f"  行业HHI: {c['industry_hhi']}  "
          f"{check_threshold(c['industry_hhi'], 'industry_hhi', thresholds)}")
    print(f"  Top行业: {c['top_industry']['name']} {c['top_industry']['weight']*100:.1f}%")

    print()
    print("=" * 56)
    print("【2】VaR / 波动率（基于真实K线）")
    print("=" * 56)
    # 取各股收盘价
    closes = {}
    for p in SAMPLE:
        k = await fetch_kline(p["ticker"])
        if "error" in k:
            print(f"  ❌ {p['name']} K线获取失败: {k['error']}")
            return
        closes[p["ticker"]] = [b["收盘"] for b in k["bars"]]

    # 合成组合日收益率
    total = sum(p["market_value"] for p in SAMPLE)
    weights = {p["ticker"]: p["market_value"] / total for p in SAMPLE}
    n = min(len(v) for v in closes.values())
    port_returns = []
    for i in range(1, n):
        r = 0.0
        for t, cl in closes.items():
            r += weights[t] * (cl[-n + i] / cl[-n + i - 1] - 1)
        port_returns.append(r)

    v = varc.calc_var(port_returns)
    print(f"  样本天数: {v['num_samples']}")
    print(f"  年化波动率: {v['volatility_annual']*100:.1f}%  "
          f"{check_threshold(v['volatility_annual'], 'volatility_annual', thresholds)}")
    print(f"  1日95% VaR: {v['var_1d']*100:.2f}%  "
          f"{check_threshold(v['var_1d'], 'var_1d_95', thresholds)}")
    print(f"  1日95% CVaR: {v['cvar_1d']*100:.2f}%")

    print()
    print("=" * 56)
    print("✅ 风险分析 Skill 测试完成（步骤5a验证通过）")
    print("=" * 56)


if __name__ == "__main__":
    asyncio.run(main())

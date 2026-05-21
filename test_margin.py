"""
期货保证金分析测试脚本。

用一个故意构造的"危险账户"演示：
- 高保证金占用率（接近满仓）
- 黑色系（螺纹+铁矿）同方向做多 → 方向性集中
- 股指期货重仓 → 单品种敞口过大、强平距离近

用法（服务器上，激活 venv）：
    python test_margin.py
"""

import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
SKILL = "src/skills/finance/risk-analysis"


def _load_script(rel_path: str, mod_name: str):
    spec = importlib.util.spec_from_file_location(mod_name, ROOT / rel_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

margin = _load_script(f"{SKILL}/scripts/margin_analyzer.py", "margin_analyzer")

# 故意构造的危险期货账户
ACCOUNT = {
    "account_equity": 200000,
    "positions": [
        {"contract": "RB2510", "name": "螺纹钢", "direction": "long",
         "lots": 5, "entry_price": 3250, "current_price": 3180,
         "multiplier": 10, "margin_rate": 0.10, "exchange": "SHFE"},
        {"contract": "I2509", "name": "铁矿石", "direction": "long",
         "lots": 3, "entry_price": 780, "current_price": 760,
         "multiplier": 100, "margin_rate": 0.12, "exchange": "DCE"},
        {"contract": "IF2509", "name": "沪深300", "direction": "short",
         "lots": 1, "entry_price": 3900, "current_price": 3920,
         "multiplier": 300, "margin_rate": 0.12, "exchange": "CFFEX"},
    ],
}


def check_margin_usage(ratio, t):
    if ratio >= t["danger"]:
        return "🔴 危险"
    if ratio >= t["warn"]:
        return "🟠 警示"
    if ratio >= t["watch"]:
        return "🟡 关注"
    return "🟢 正常"


def check_liq_distance(d, t):
    if d is None:
        return ""
    if d < t["danger"]:
        return "🔴 危险"
    if d < t["warn"]:
        return "🟠 警示"
    if d < t["watch"]:
        return "🟡 关注"
    return "🟢 正常"


def main():
    with open(ROOT / f"{SKILL}/data/exchange_margin_rules.yaml", encoding="utf-8") as f:
        rules = yaml.safe_load(f)
    mu_t = rules["margin_usage_thresholds"]
    ld_t = rules["liquidation_distance_thresholds"]

    r = margin.analyze_margin(ACCOUNT)

    print("=" * 60)
    print("【期货账户保证金分析】")
    print("=" * 60)
    print(f"  动态权益: {r['account_equity']}  占用保证金: {r['total_margin_used']}")
    print(f"  可用资金: {r['available_funds']}  浮动盈亏: {r['total_floating_pnl']}")
    print(f"  保证金占用率: {r['margin_usage_ratio']*100:.1f}%  "
          f"{check_margin_usage(r['margin_usage_ratio'], mu_t)}")
    print()
    print("  各合约强平距离（还能反向波动多少触发追保）:")
    for p in r["positions"]:
        d = p["liquidation_distance_pct"]
        d_str = f"{d*100:.2f}%" if d is not None else "N/A"
        print(f"    {p['name']}({p['contract']}) {p['direction']}  "
              f"浮盈:{p['pnl']:>8}  强平距离:{d_str:>7}  {check_liq_distance(d, ld_t)}")
    print()
    md = r["most_dangerous"]
    print(f"  ⚠️  最危险合约: {md['name']}（强平距离仅 {md['liquidation_distance_pct']*100:.2f}%）")
    print(f"  单品种最大敞口: {r['max_commodity_exposure']['name']} "
          f"{r['max_commodity_exposure']['ratio']*100:.1f}%")
    net = r["net_direction_ratio"]
    direction = "偏多" if net > 0.3 else ("偏空" if net < -0.3 else "多空均衡")
    print(f"  方向性: 净方向比率 {net:.2f}（{direction}）")
    print()
    print("=" * 60)
    print("✅ 期货保证金分析测试完成（步骤5b验证通过）")
    print("=" * 60)


if __name__ == "__main__":
    main()

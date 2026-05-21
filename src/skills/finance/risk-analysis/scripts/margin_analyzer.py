"""
期货保证金风险分析脚本。

输入期货账户（动态权益 + 各持仓），输出：
- 每个合约：合约价值、占用保证金、浮动盈亏、强平距离
- 账户层面：保证金占用率、可用资金、最危险合约
- 集中度：单品种最大敞口、方向性（净多/净空）

纯计算：账户数据由调用方提供，本脚本不取数据。

期货账户数据格式：
{
  "account_equity": 200000,         # 动态权益（已含浮动盈亏）
  "positions": [
    {
      "contract": "RB2510", "name": "螺纹钢",
      "direction": "long",          # long / short
      "lots": 5,                    # 手数
      "entry_price": 3250,          # 开仓均价
      "current_price": 3180,        # 当前价
      "multiplier": 10,             # 合约乘数（每点价值）
      "margin_rate": 0.10,          # 保证金比例
      "exchange": "SHFE"
    }
  ]
}

两种用法：
1. 函数导入：from margin_analyzer import analyze_margin
2. 脚本运行：python margin_analyzer.py /data/futures_account.json

强平距离说明（近似）：在仅该合约反向波动、其他不变的假设下，
价格还能反向移动多少（%）才会把账户缓冲耗尽、触发追保/强平。
"""

import json
import sys
from typing import Dict


def analyze_margin(account: Dict) -> Dict:
    """分析期货账户保证金风险。"""
    equity = account.get("account_equity", 0)
    positions = account.get("positions", [])
    if equity <= 0 or not positions:
        return {"error": "账户权益非法或无持仓"}

    pos_results = []
    total_margin = 0.0
    total_pnl = 0.0
    commodity_exposure: Dict[str, float] = {}
    net_direction_value = 0.0  # 净多(正) / 净空(负)，按合约价值

    for p in positions:
        sign = 1 if p["direction"] == "long" else -1
        contract_value = p["current_price"] * p["multiplier"] * p["lots"]
        margin = contract_value * p["margin_rate"]
        pnl = (p["current_price"] - p["entry_price"]) * p["multiplier"] * p["lots"] * sign

        total_margin += margin
        total_pnl += pnl
        commodity_exposure[p["name"]] = commodity_exposure.get(p["name"], 0) + contract_value
        net_direction_value += sign * contract_value

        pos_results.append({
            "contract": p["contract"],
            "name": p["name"],
            "direction": p["direction"],
            "contract_value": round(contract_value, 2),
            "margin": round(margin, 2),
            "pnl": round(pnl, 2),
            "_loss_per_point": p["multiplier"] * p["lots"],
            "_current_price": p["current_price"],
        })

    # 账户缓冲（可用资金）：动态权益 - 占用保证金
    buffer = equity - total_margin
    margin_usage = total_margin / equity

    # 每个合约的强平距离（仅该合约反向波动的近似）
    for pr in pos_results:
        lpp = pr.pop("_loss_per_point")
        cur = pr.pop("_current_price")
        if buffer <= 0:
            pr["liquidation_distance_pct"] = 0.0  # 已无缓冲
        elif lpp > 0:
            max_adverse_points = buffer / lpp
            pr["liquidation_distance_pct"] = round(max_adverse_points / cur, 4)
        else:
            pr["liquidation_distance_pct"] = None

    # 最危险合约（强平距离最近）
    valid = [pr for pr in pos_results if pr["liquidation_distance_pct"] is not None]
    most_dangerous = min(valid, key=lambda x: x["liquidation_distance_pct"]) if valid else None

    # 集中度与方向性
    gross = sum(commodity_exposure.values())
    max_commodity = max(commodity_exposure.items(), key=lambda x: x[1])
    net_direction_ratio = net_direction_value / gross if gross else 0

    return {
        "account_equity": equity,
        "total_margin_used": round(total_margin, 2),
        "margin_usage_ratio": round(margin_usage, 4),
        "available_funds": round(buffer, 2),
        "total_floating_pnl": round(total_pnl, 2),
        "positions": pos_results,
        "most_dangerous": {
            "name": most_dangerous["name"],
            "contract": most_dangerous["contract"],
            "liquidation_distance_pct": most_dangerous["liquidation_distance_pct"],
        } if most_dangerous else None,
        "max_commodity_exposure": {
            "name": max_commodity[0],
            "ratio": round(max_commodity[1] / gross, 4) if gross else 0,
        },
        "net_direction_ratio": round(net_direction_ratio, 4),  # 接近+1全多，-1全空
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "用法: python margin_analyzer.py <futures_account.json>"}, ensure_ascii=False))
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        account = json.load(f)
    result = analyze_margin(account)
    print(json.dumps(result, ensure_ascii=False, indent=2))

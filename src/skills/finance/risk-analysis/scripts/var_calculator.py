"""
VaR / 波动率计算脚本。

输入"组合日收益率序列"，输出 VaR、CVaR、年化波动率。
纯计算：收益率由调用方提供（通常由 K 线收盘价算得），本脚本不取数据。

方法：默认用历史模拟法（金融场景最稳，不假设正态分布）。

两种用法：
1. 函数导入：from var_calculator import calc_var
2. 脚本运行（沙箱内）：python var_calculator.py /data/returns.json
   returns.json 格式：{"returns": [0.01, -0.02, ...]}

指标说明（均为正数表示"潜在损失比例"）：
- var_1d   : 1 日 VaR，X% 表示"最差 (1-置信度) 的情况下，可能损失 X%"
- cvar_1d  : 条件 VaR（超过 VaR 那部分的平均损失），比 VaR 更保守
- vol_annual: 年化波动率
"""

import json
import sys
from typing import Dict, List


def calc_var(returns: List[float], confidence: float = 0.95) -> Dict:
    """
    计算 VaR / CVaR / 波动率。

    Args:
        returns: 组合日收益率序列（如 [0.01, -0.02, 0.005, ...]）
        confidence: 置信度，默认 0.95

    Returns:
        风险指标字典
    """
    import numpy as np

    if not returns or len(returns) < 5:
        return {"error": f"收益率样本太少（{len(returns) if returns else 0} 个），至少需要 5 个"}

    arr = np.array(returns, dtype=float)

    # 历史模拟法 VaR：取分位数（损失为负，取下分位再变正）
    var_1d = float(-np.percentile(arr, (1 - confidence) * 100))
    var_1d = max(var_1d, 0.0)  # VaR 不应为负

    # CVaR：低于 -VaR 的那部分收益的平均（即尾部平均损失）
    tail = arr[arr <= -var_1d]
    cvar_1d = float(-tail.mean()) if tail.size > 0 else var_1d

    # 波动率
    vol_daily = float(arr.std(ddof=1))
    vol_annual = float(vol_daily * (252 ** 0.5))

    return {
        "confidence": confidence,
        "num_samples": len(returns),
        "var_1d": round(var_1d, 4),
        "cvar_1d": round(cvar_1d, 4),
        "volatility_daily": round(vol_daily, 4),
        "volatility_annual": round(vol_annual, 4),
        "mean_return_daily": round(float(arr.mean()), 5),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "用法: python var_calculator.py <returns.json>"}, ensure_ascii=False))
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)
    returns = data.get("returns", data) if isinstance(data, dict) else data
    result = calc_var(returns)
    print(json.dumps(result, ensure_ascii=False, indent=2))

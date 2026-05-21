"""
集中度分析脚本。

计算持仓的集中度风险：单股集中度、股票 HHI、行业 HHI、Top 行业。
纯计算：输入持仓列表，输出集中度指标，不涉及数据获取。

两种用法：
1. 作为函数导入：from concentration import calc_concentration
2. 作为脚本运行（沙箱内）：python concentration.py /data/positions.json
   读取 JSON 持仓文件，打印 JSON 结果。

HHI（赫芬达尔指数）= 各权重平方和，越大越集中：
  <0.15 分散 / 0.15-0.25 适度 / 0.25-0.40 较集中 / >0.40 高度集中
"""

import json
import sys
from typing import List, Dict


def calc_concentration(positions: List[Dict]) -> Dict:
    """
    计算持仓集中度指标。

    Args:
        positions: [{"ticker","name","market_value","industry"}, ...]

    Returns:
        集中度指标字典
    """
    if not positions:
        return {"error": "持仓为空"}

    total = sum(p.get("market_value", 0) for p in positions)
    if total <= 0:
        return {"error": "持仓总市值为 0 或非法"}

    # 个股权重
    weights = {p["ticker"]: p.get("market_value", 0) / total for p in positions}
    # 单股最大集中度
    max_ticker = max(weights, key=weights.get)
    max_single_weight = weights[max_ticker]
    # 股票 HHI
    stock_hhi = sum(w ** 2 for w in weights.values())

    # 行业聚合
    industry_mv: Dict[str, float] = {}
    for p in positions:
        ind = p.get("industry", "未知")
        industry_mv[ind] = industry_mv.get(ind, 0) + p.get("market_value", 0)
    industry_weights = {k: v / total for k, v in industry_mv.items()}
    industry_hhi = sum(w ** 2 for w in industry_weights.values())
    top_ind = max(industry_weights, key=industry_weights.get)

    return {
        "total_value": total,
        "num_positions": len(positions),
        "max_single": {"ticker": max_ticker, "weight": round(max_single_weight, 4)},
        "stock_hhi": round(stock_hhi, 4),
        "industry_hhi": round(industry_hhi, 4),
        "top_industry": {"name": top_ind, "weight": round(industry_weights[top_ind], 4)},
        "stock_weights": {k: round(v, 4) for k, v in weights.items()},
        "industry_weights": {k: round(v, 4) for k, v in industry_weights.items()},
    }


if __name__ == "__main__":
    # 沙箱内运行：python concentration.py <positions.json>
    if len(sys.argv) < 2:
        print(json.dumps({"error": "用法: python concentration.py <positions.json>"}, ensure_ascii=False))
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        positions = json.load(f)
    result = calc_concentration(positions)
    print(json.dumps(result, ensure_ascii=False, indent=2))

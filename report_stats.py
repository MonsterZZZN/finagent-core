"""
平台监控报表。

从 agent_traces 聚合出整个 FinAgent 平台（core + research）的健康度报表：
总览 / 按服务 / 按组件（延迟+token+失败率）/ 失败分析。

用法（finagent-core 目录，激活 venv）：
    python report_stats.py              # 默认看最近 24 小时
    python report_stats.py 168          # 看最近 7 天
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from observability import metrics  # noqa: E402


def main():
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24

    ov = metrics.overview(hours)
    print("=" * 64)
    print(f"  FinAgent 平台监控报表（最近 {hours} 小时）")
    print("=" * 64)

    # ---- 总览 ----
    print("\n【总览】")
    print(f"  请求数(trace)   : {ov['requests']}")
    print(f"  调用数(span)    : {ov['spans']}")
    print(f"  失败率          : {ov['failure_rate'] * 100:.1f}%  ({ov['errors']} 次失败)")
    print(f"  Token 总消耗    : {ov['total_tokens']:,}")
    print(f"  估算成本        : ¥{ov['total_cost_rmb']}")

    # ---- 按服务 ----
    print("\n【按服务】")
    print(f"  {'服务':<22}{'调用数':>8}{'token':>10}{'失败':>6}")
    for svc, d in ov["by_service"].items():
        print(f"  {svc:<22}{d['spans']:>8}{d['tokens']:>10}{d['errors']:>6}")

    # ---- 按组件 ----
    print("\n【按组件】(调用数/平均延迟/p95延迟/token/失败率)")
    print(f"  {'组件':<26}{'类型':<6}{'次数':>5}{'avg':>8}{'p95':>8}{'token':>9}{'失败率':>7}")
    for c in metrics.by_component(hours):
        print(
            f"  {c['name'][:25]:<26}{c['type']:<6}{c['count']:>5}"
            f"{c['avg_latency_ms']:>7}ms{c['p95_latency_ms']:>6}ms"
            f"{c['total_tokens']:>9}{c['error_rate'] * 100:>6.1f}%"
        )

    # ---- 失败分析 ----
    print("\n【失败分析】")
    fa = metrics.failure_analysis(hours)
    if not fa:
        print("  ✅ 无失败记录")
    else:
        for et, d in sorted(fa.items(), key=lambda x: -x[1]["count"]):
            print(f"  {et}: {d['count']} 次")
            for s in d["samples"]:
                print(f"      例: {s}")

    print("\n" + "=" * 64)


if __name__ == "__main__":
    main()

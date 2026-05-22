"""
可观测性埋点测试。

跑一次对话（会触发主 Agent + 可能的工具/子 Agent 调用），
然后从 MongoDB 查出本次捕获的 span，验证埋点生效。

用法（finagent-core 目录，激活 venv，.env 配了 DEEPSEEK_API_KEY）：
    python test_observability.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from gateway.runtime import get_runtime  # noqa: E402
from observability.store import trace_store  # noqa: E402

SESSION = "obs-test-001"


async def main():
    rt = get_runtime()

    print("=" * 60)
    print("跑一次会带工具调用的对话（持仓风险评估）...")
    print("=" * 60)
    msg = (
        "帮我评估持仓风险。持仓JSON："
        '[{"ticker":"600519","name":"贵州茅台","market_value":300000,"industry":"白酒"},'
        '{"ticker":"000858","name":"五粮液","market_value":200000,"industry":"白酒"}]'
    )
    reply = await rt.run_for_session(SESSION, msg, context={"channel": "test"})
    print(f"\n回复（前100字）: {reply[:100]}...\n")

    # 查本次会话捕获的 span
    spans = list(trace_store.col.find({"session_id": SESSION}).sort("ts", 1))
    print("=" * 60)
    print(f"捕获 {len(spans)} 条 span：")
    print("=" * 60)
    total_tokens = 0
    for s in spans:
        line = f"  [{s['type']:4}] {s['name']:30} {s['latency_ms']:>6}ms  {s['status']}"
        if s.get("total_tokens"):
            line += f"  tokens={s['total_tokens']}"
            total_tokens += s["total_tokens"]
        if s["status"] == "error":
            line += f"  ❌ {s.get('error_type')}"
        print(line)

    print("\n" + "=" * 60)
    print(f"本次总 token 消耗: {total_tokens}")
    if spans:
        print("✅ 可观测性埋点生效（O1 验证通过）")
    else:
        print("⚠️  没捕获到 span，检查 handler 是否挂上")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

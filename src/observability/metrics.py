"""
可观测性聚合指标。

从 agent_traces（两个项目共用）的原始 span 聚合出监控指标：
- 总览：请求数、调用数、失败率、token、成本
- 按服务：core / research 分别统计
- 按组件：每个模型/工具的调用数、avg/p95 延迟、token、失败率
- 失败分析：按 error_type 分组

成本按 token 单价估算（PRICE 可调）。
"""

from datetime import datetime, timedelta

from observability.store import trace_store

# DeepSeek 价格参考（元 / 1M tokens，会变，按需调整）
PRICE = {
    "deepseek-chat": {"input": 2.0, "output": 8.0},
    "deepseek-reasoner": {"input": 4.0, "output": 16.0},
}
DEFAULT_PRICE = {"input": 2.0, "output": 8.0}


def _percentile(values: list, p: int) -> int:
    if not values:
        return 0
    s = sorted(values)
    k = min(int(len(s) * p / 100), len(s) - 1)
    return s[k]


def _cost(name: str, prompt: int, completion: int) -> float:
    pr = PRICE.get(name, DEFAULT_PRICE)
    return prompt / 1e6 * pr["input"] + completion / 1e6 * pr["output"]


def query_spans(hours: int = 24, service: str | None = None) -> list:
    """取最近 N 小时的 span。"""
    q = {"ts": {"$gte": datetime.utcnow() - timedelta(hours=hours)}}
    if service:
        q["service"] = service
    return list(trace_store.col.find(q))


def overview(hours: int = 24) -> dict:
    """平台总览。"""
    spans = query_spans(hours)
    total = len(spans)
    errors = sum(1 for s in spans if s.get("status") == "error")
    requests = len(set(s.get("trace_id") for s in spans))
    tokens = sum(s.get("total_tokens", 0) for s in spans)
    cost = sum(
        _cost(s.get("name", ""), s.get("prompt_tokens", 0), s.get("completion_tokens", 0))
        for s in spans
        if s.get("type") == "llm"
    )

    by_service: dict = {}
    for s in spans:
        svc = s.get("service", "?")
        d = by_service.setdefault(svc, {"spans": 0, "tokens": 0, "errors": 0})
        d["spans"] += 1
        d["tokens"] += s.get("total_tokens", 0)
        if s.get("status") == "error":
            d["errors"] += 1

    return {
        "hours": hours,
        "requests": requests,
        "spans": total,
        "errors": errors,
        "failure_rate": errors / total if total else 0,
        "total_tokens": tokens,
        "total_cost_rmb": round(cost, 4),
        "by_service": by_service,
    }


def by_component(hours: int = 24) -> list:
    """按组件（模型/工具）聚合。"""
    spans = query_spans(hours)
    comp: dict = {}
    for s in spans:
        name = s.get("name", "?")
        c = comp.setdefault(
            name, {"type": s.get("type"), "count": 0, "latencies": [], "tokens": 0, "errors": 0}
        )
        c["count"] += 1
        c["latencies"].append(s.get("latency_ms", 0))
        c["tokens"] += s.get("total_tokens", 0)
        if s.get("status") == "error":
            c["errors"] += 1

    result = []
    for name, c in comp.items():
        lat = c["latencies"]
        result.append(
            {
                "name": name,
                "type": c["type"],
                "count": c["count"],
                "avg_latency_ms": int(sum(lat) / len(lat)) if lat else 0,
                "p95_latency_ms": _percentile(lat, 95),
                "total_tokens": c["tokens"],
                "error_rate": round(c["errors"] / c["count"], 3) if c["count"] else 0,
            }
        )
    return sorted(result, key=lambda x: -x["count"])


def failure_analysis(hours: int = 24) -> dict:
    """失败分析：按 error_type 分组。"""
    spans = query_spans(hours)
    errs: dict = {}
    for s in spans:
        if s.get("status") == "error":
            et = s.get("error_type", "unknown")
            d = errs.setdefault(et, {"count": 0, "samples": []})
            d["count"] += 1
            if len(d["samples"]) < 2:
                d["samples"].append(s.get("error_message", "")[:120])
    return errs

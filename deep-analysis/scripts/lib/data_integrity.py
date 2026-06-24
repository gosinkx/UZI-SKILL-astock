"""Post-Task-1 data integrity validator.

After Task 1 (raw data collection) finishes, run `validate(raw)` to check
that all critical fields used by downstream rules are populated. Returns a
report with missing/fallback dimensions and a `critical_missing` flag.

If critical_missing is True, the caller should retry the affected fetchers
or mark the report with a warning banner.
"""
from __future__ import annotations

from typing import Any


# (dim_key, data_path, label, critical)
# data_path is a dotted path into dim["data"][...]
CRITICAL_CHECKS = [
    # Dimension 0 · Basic
    ("0_basic",        "name",               "公司名称",         True),
    ("0_basic",        "price",              "当前股价",         True),
    ("0_basic",        "industry",           "所属行业",         True),
    ("0_basic",        "market_cap",         "总市值",           True),
    ("0_basic",        "pe_ttm",             "PE-TTM",           False),
    ("0_basic",        "pb",                 "PB",               False),

    # Dimension 1 · Financials
    ("1_financials",   "roe_history",        "ROE 历史",         True),
    ("1_financials",   "revenue_history",    "营收历史",         False),
    ("1_financials",   "net_profit_history", "净利历史",         False),
    ("1_financials",   "financial_health",   "财务健康度",        False),

    # Dimension 2 · Kline
    ("2_kline",        "stage",              "K 线阶段",         True),
    ("2_kline",        "ma_align",           "均线多空",         False),
    ("2_kline",        "macd",               "MACD",             False),

    # Dimension 10 · Valuation
    ("10_valuation",   "pe",                 "PE",               False),
    ("10_valuation",   "pe_quantile",        "PE 5 年分位",       False),
    ("10_valuation",   "pb_quantile",        "PB 5 年分位",       False),

    # Dimension 7 · Industry
    ("7_industry",     "growth",             "行业增速",          False),

    # Dimension 14 · Moat
    ("14_moat",        "scores",             "护城河评分",        False),
]

# Fetchers that provide qualitative enrichment — should have any data at all
# Keys must match the actual dim keys used by run_real_test.collect_raw_data
ENRICHMENT_DIMS = [
    ("3_macro",     "宏观周期"),
    ("4_peers",     "同业对标"),
    ("5_chain",     "上下游"),
    ("6_research",  "券商研报"),
    ("7_industry",  "行业景气"),
    ("8_materials", "原材料"),
    ("9_futures",   "期货关联"),
    ("11_governance", "治理/减持"),
    ("12_capital_flow", "北向/两融"),
    ("13_policy",   "政策环境"),
    ("14_moat",     "护城河"),
    ("15_events",   "事件驱动"),
    ("16_lhb",      "龙虎榜/游资"),
    ("17_sentiment","大V舆情"),
    ("18_trap",     "杀猪盘"),
    ("19_contests", "实盘比赛"),
]


def _get(obj: dict, path: str) -> Any:
    cur = obj
    for key in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _is_missing(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and v.strip() in ("", "—", "-", "N/A", "None", "0", "0.0"):
        return True
    if isinstance(v, (list, dict)) and len(v) == 0:
        return True
    return False


def validate(raw: dict) -> dict:
    """Validate raw data. Returns:
        {
            "ok": bool,
            "critical_missing": bool,
            "missing_critical": [...],      # list of missing critical fields
            "missing_optional": [...],
            "missing_enrichment": [...],    # dims with no data at all
            "fallback_dims": [...],         # dims flagged fallback=True
            "coverage_pct": 0-100,
        }
    """
    dims = raw.get("dimensions", {}) or {}

    missing_critical: list[dict] = []
    missing_optional: list[dict] = []
    total_checks = 0
    passed_checks = 0

    for dim_key, path, label, critical in CRITICAL_CHECKS:
        total_checks += 1
        dim = dims.get(dim_key) or {}
        data = dim.get("data") or {}
        value = _get(data, path)
        if _is_missing(value):
            entry = {"dim": dim_key, "path": path, "label": label}
            if critical:
                missing_critical.append(entry)
            else:
                missing_optional.append(entry)
        else:
            passed_checks += 1

    # Enrichment coverage
    missing_enrichment: list[dict] = []
    for dim_key, label in ENRICHMENT_DIMS:
        dim = dims.get(dim_key) or {}
        data = dim.get("data") or {}
        # Check if the dim has any non-empty string/list/number in its values
        has_content = False
        for v in data.values() if isinstance(data, dict) else []:
            if not _is_missing(v):
                has_content = True
                break
        if not has_content:
            missing_enrichment.append({"dim": dim_key, "label": label})

    # Fallback dim detection
    fallback_dims = [
        {"dim": k, "reason": (v or {}).get("fallback_reason", "unknown")}
        for k, v in dims.items()
        if isinstance(v, dict) and v.get("fallback") is True
    ]

    coverage_pct = round(passed_checks / total_checks * 100, 0) if total_checks else 0

    critical_missing = len(missing_critical) > 0
    return {
        "ok": not critical_missing and len(missing_enrichment) < 7,
        "critical_missing": critical_missing,
        "missing_critical": missing_critical,
        "missing_optional": missing_optional,
        "missing_enrichment": missing_enrichment,
        "fallback_dims": fallback_dims,
        "coverage_pct": coverage_pct,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
    }


# ═══════════════════════════════════════════════════════════════
# Recovery task generation
# ═══════════════════════════════════════════════════════════════

# Per-field recovery hints · used by agents to prioritize retry strategy.
# Order matters — browser > MX > WebSearch > inference.
_RECOVERY_HINTS: dict[tuple[str, str], list[str]] = {
    ("0_basic", "name"):         ["mx: '{code} 公司简称'", "browser: https://xueqiu.com/S/{code_raw}", "ws: '{code} 公司简介'"],
    ("0_basic", "price"):        ["mx: '{code} 最新价'", "browser: https://xueqiu.com/S/{code_raw}", "ws: '{code} 股价 2026'"],
    ("0_basic", "industry"):     ["mx: '{code} 所属申万行业'", "browser: https://xueqiu.com/S/{code_raw}/F10", "ws: '{code} 所属行业'"],
    ("0_basic", "market_cap"):   ["mx: '{code} 总市值'", "browser: https://quote.eastmoney.com/{eastmoney_code}.html", "ws: '{code} 市值'"],
    ("0_basic", "pe_ttm"):       ["mx: '{code} 市盈率TTM'", "browser: https://xueqiu.com/S/{code_raw}", "infer: 市值 / 归母净利润"],
    ("0_basic", "pb"):           ["mx: '{code} 市净率'", "browser: https://xueqiu.com/S/{code_raw}"],
    ("1_financials", "roe_history"):        ["mx: '{code} 最近5年ROE'", "browser: https://xueqiu.com/S/{code_raw}/F10/main"],
    ("1_financials", "revenue_history"):    ["mx: '{code} 最近5年营业收入'", "browser: https://xueqiu.com/S/{code_raw}/F10/main"],
    ("1_financials", "net_profit_history"): ["mx: '{code} 最近5年净利润'", "browser: https://xueqiu.com/S/{code_raw}/F10/main"],
    ("1_financials", "financial_health"):   ["infer: 从 ROE/debt_ratio/fcf 综合判断", "mx: '{code} 财务健康度'"],
    ("2_kline", "stage"):        ["infer: 从 ma20/ma60 多空排列推断 Wyckoff stage", "browser: https://xueqiu.com/S/{code_raw}"],
    ("10_valuation", "pe"):            ["mx: '{code} 市盈率'", "browser: https://xueqiu.com/S/{code_raw}"],
    ("10_valuation", "pe_quantile"):   ["mx: '{code} PE 5年分位数'", "ws: '{code} PE历史分位'"],
    ("10_valuation", "pb_quantile"):   ["mx: '{code} PB 5年分位数'", "ws: '{code} PB历史分位'"],
    ("7_industry", "growth"):    ["mx: '{industry} 行业增速 2026'", "ws: '{industry} 行业规模 增速 2026'"],
    ("14_moat", "scores"):       ["agent: Porter 5 Forces + web search 护城河评分"],
}

# Enrichment dim recovery hints (when a whole dim is empty).
_ENRICHMENT_HINTS: dict[str, list[str]] = {
    "3_macro":        ["ws: '中国 {industry} 宏观环境 利率 2026'"],
    "4_peers":        ["mx: '{industry} 同行业公司 市值排名'", "ws: '{name} 同行业竞争者 对比'"],
    "5_chain":        ["browser: https://xueqiu.com/S/{code_raw}/F10", "ws: '{name} 上下游产业链'"],
    "6_research":     ["mx: '{code} 券商研报 目标价'", "ws: '{name} 最新研报 2026'"],
    "7_industry":     ["mx: '{industry} 行业规模 TAM'", "ws: '{industry} 行业景气 2026'"],
    "8_materials":    ["ws: '{name} 原材料 成本构成'"],
    "9_futures":      ["ws: '{industry} 期货 相关品种'"],
    "11_governance":  ["mx: '{code} 股东结构 高管减持'", "browser: https://quote.eastmoney.com/{eastmoney_code}.html"],
    "12_capital_flow":["mx: '{code} 北向持仓 融资融券'", "browser: https://data.eastmoney.com/zlsj/{code_raw}.html"],
    "13_policy":      ["ws: '{industry} 最新政策 2026'"],
    "14_moat":        ["ws: '{name} 核心竞争力 技术壁垒 市场份额'"],
    "15_events":      ["mx: '{code} 最新公告'", "ws: '{name} {code} 最新公告 中标 研发 2026'"],
    "16_lhb":         ["mx: '{code} 龙虎榜'", "browser: https://data.eastmoney.com/stock/lhb/{code_raw}.html"],
    "17_sentiment":   ["browser: https://xueqiu.com/S/{code_raw}", "ws: 'site:xueqiu.com {code}'"],
    "18_trap":        ["infer: 从龙虎榜+换手率+涨跌幅综合判断"],
    "19_contests":    ["ws: '{code} 实盘比赛 持仓'"],
}


def generate_recovery_tasks(raw: dict, integrity: dict) -> list[dict]:
    """Turn an integrity report into agent-actionable recovery tasks.

    Each task is self-contained with context (code, industry, name) baked in,
    so an agent can execute it without re-reading raw_data. Severity ordering
    lets the agent focus on critical gaps first.

    Returns:
        list[{"dim", "field", "label", "severity", "suggested_actions", "status"}]
    """
    dims = raw.get("dimensions", {}) or {}
    basic = (dims.get("0_basic") or {}).get("data") or {}
    code = basic.get("code") or raw.get("ticker") or ""
    industry = (dims.get("7_industry") or {}).get("data", {}).get("industry") or basic.get("industry") or "综合"
    name = basic.get("name") or raw.get("ticker") or code
    code_raw = code.split(".")[0] if "." in code else code
    # EastMoney uses 0/1 prefix for SZ/SH
    eastmoney_code = (("1." if code.endswith(".SH") else "0.") + code_raw) if code_raw else ""

    ctx = {
        "code": code,
        "code_raw": code_raw,
        "eastmoney_code": eastmoney_code,
        "name": name,
        "industry": industry,
    }

    def _render(actions: list[str]) -> list[str]:
        rendered = []
        for a in actions:
            try:
                rendered.append(a.format(**ctx))
            except (KeyError, IndexError):
                rendered.append(a)
        return rendered

    tasks: list[dict] = []

    # Critical + optional missing fields
    for entry in integrity.get("missing_critical", []) + integrity.get("missing_optional", []):
        key = (entry["dim"], entry["path"])
        hints = _RECOVERY_HINTS.get(key, ["ws: '{name} {label}'".format(name=name, label=entry["label"])])
        severity = "critical" if entry in integrity.get("missing_critical", []) else "optional"
        tasks.append({
            "dim": entry["dim"],
            "field": entry["path"],
            "label": entry["label"],
            "severity": severity,
            "suggested_actions": _render(hints),
            "status": "pending",
        })

    # Whole-dim enrichment gaps
    for entry in integrity.get("missing_enrichment", []):
        hints = _ENRICHMENT_HINTS.get(entry["dim"], ["ws: '{name} {label}'".format(name=name, label=entry["label"])])
        tasks.append({
            "dim": entry["dim"],
            "field": "_entire_dim",
            "label": entry["label"],
            "severity": "enrichment",
            "suggested_actions": _render(hints),
            "status": "pending",
        })

    return tasks


def format_report(report: dict) -> str:
    """Human-readable integrity report for console output."""
    lines: list[str] = []
    status = "✅ OK" if report["ok"] else ("🔴 CRITICAL" if report["critical_missing"] else "🟡 WARNING")
    lines.append(f"[data_integrity] {status} coverage={report['coverage_pct']}% ({report['passed_checks']}/{report['total_checks']})")

    if report["missing_critical"]:
        lines.append(f"  🔴 critical missing ({len(report['missing_critical'])}):")
        for m in report["missing_critical"]:
            lines.append(f"     - {m['label']} ({m['dim']}.{m['path']})")

    if report["missing_optional"]:
        lines.append(f"  🟡 optional missing ({len(report['missing_optional'])}):")
        for m in report["missing_optional"][:8]:
            lines.append(f"     - {m['label']} ({m['dim']}.{m['path']})")

    if report["missing_enrichment"]:
        labels = ", ".join(m["label"] for m in report["missing_enrichment"])
        lines.append(f"  🟡 enrichment dims empty ({len(report['missing_enrichment'])}): {labels}")

    if report["fallback_dims"]:
        labels = ", ".join(f["dim"] for f in report["fallback_dims"])
        lines.append(f"  ⚠️  fallback dims: {labels}")

    return "\n".join(lines)


if __name__ == "__main__":
    import json
    import sys
    # Optional — validate a saved raw JSON file
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if path:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        report = validate(raw)
        print(format_report(report))
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("Usage: python -m lib.data_integrity <raw.json>")

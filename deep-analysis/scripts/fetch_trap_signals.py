"""Dimension 18 · 杀猪盘检测 — 真实 web search 扫描 8 信号."""
from __future__ import annotations

import json
import sys

from lib import data_sources as ds
from lib.market_router import parse_ticker
from lib.web_search import search


SIGNALS = [
    {
        "id": 1, "name": "大量低质量账号同时推荐",
        "queries": ["{name} 强烈推荐 必涨", "{name} 内部消息 暴涨"],
        "positive_kws": ["必涨", "强烈推荐", "内部", "稳赚"],
    },
    {
        "id": 2, "name": "推荐话术模板化",
        "queries": ["{name} 主力建仓完毕 即将爆发", "{name} 翻倍 目标价"],
        "positive_kws": ["即将爆发", "主力建仓完毕", "翻倍", "目标翻倍"],
    },
    {
        "id": 3, "name": "付费社群/VIP直播间引流",
        "queries": ["{name} 股票 微信群", "{name} 老师 带单 VIP 直播间"],
        "positive_kws": ["微信群", "VIP 直播", "老师带", "收费群", "加入群聊"],
    },
    {
        "id": 4, "name": "基本面与热度脱节",
        "queries": ["{name} 业绩亏损 推荐 暴涨", "{name} ST 推荐 拉升"],
        "positive_kws": ["亏损但推荐", "ST", "垃圾股 推荐"],
    },
    {
        "id": 5, "name": "K线异常配合",
        "queries": ["{name} 异动 操纵 拉升"],
        "positive_kws": ["异动", "操纵", "快速拉升", "直线拉升"],
    },
    {
        "id": 6, "name": "老师/股神人设推广",
        "queries": ["{name} 老师 股神 跟单", "{name} 实盘 老师"],
        "positive_kws": ["老师", "股神", "跟单", "操盘手"],
    },
    {
        "id": 7, "name": "跨平台联动推广",
        "queries": ["小红书 {name} 股票 推荐", "抖音 {name} 股票"],
        "positive_kws": ["小红书", "抖音", "快手", "B站 推荐"],
    },
    {
        "id": 8, "name": "虚假研报/伪造消息",
        "queries": ["{name} 虚假研报 谣言", "{name} 辟谣 澄清"],
        "positive_kws": ["虚假", "谣言", "澄清", "辟谣", "伪造"],
    },
]


def main(ticker_or_name: str) -> dict:
    # If ticker, resolve to name
    name = ticker_or_name
    if ticker_or_name.replace(".", "").replace("SZ", "").replace("SH", "").isdigit():
        try:
            ti = parse_ticker(ticker_or_name)
            basic = ds.fetch_basic(ti)
            name = basic.get("name") or ti.code
        except Exception:
            pass

    hit_signals = []
    all_snippets = {}
    for sig in SIGNALS:
        combined_bodies = []
        for q_template in sig["queries"][:1]:  # 1 query per signal to save search calls
            q = q_template.format(name=name)
            res = search(q, max_results=3)
            valid = [r for r in res if "error" not in r]
            combined_bodies.extend(r.get("body", "") for r in valid)
            all_snippets.setdefault(f"signal_{sig['id']}", []).extend(
                {"title": r.get("title", "")[:80], "body": r.get("body", "")[:180], "url": r.get("url", "")}
                for r in valid[:2]
            )

        combined_text = " ".join(combined_bodies)
        hits = [kw for kw in sig["positive_kws"] if kw in combined_text]
        if len(hits) >= 2:
            hit_signals.append({
                "id": sig["id"],
                "name": sig["name"],
                "evidence_kws": hits[:3],
                "severity": "high" if len(hits) >= 3 else "medium",
            })

    n_hits = len(hit_signals)
    if n_hits <= 1:
        level = "🟢 安全"
        score = 9
        recommendation = "数据正常，未发现明显推广痕迹。"
    elif n_hits <= 3:
        level = "🟡 注意"
        score = 7
        recommendation = f"发现 {n_hits} 个推广信号，建议核实信息源。"
    elif n_hits <= 5:
        level = "🟠 警惕"
        score = 4
        recommendation = f"发现 {n_hits} 个推广信号，强烈建议谨慎。"
    else:
        level = "🔴 高度可疑"
        score = 1
        recommendation = f"发现 {n_hits} 个推广信号，强烈建议回避。疑似杀猪盘特征。"

    return {
        "ticker": ticker_or_name,
        "data": {
            "trap_level": level,
            "trap_score": score,
            "signals_hit": f"{n_hits}/8",
            "signals_hit_count": n_hits,
            "signals_hit_detail": hit_signals,
            "recommendation": recommendation,
            "evidence_count": sum(len(s.get("evidence_kws", [])) for s in hit_signals),
            "high_risk_kw": ", ".join(s["name"] for s in hit_signals[:3]) if hit_signals else "未发现",
            "snippets": all_snippets,
        },
        "source": "web_search:ddgs + 8-signal keyword scan",
        "fallback": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1] if len(sys.argv) > 1 else "002273.SZ"), ensure_ascii=False, indent=2, default=str))

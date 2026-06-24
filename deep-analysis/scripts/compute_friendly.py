"""Tier 4 友好层计算器.

输入：raw_data.json + dimensions.json
输出：friendly 字段 for synthesis.json
  - scenarios: 5 情景模拟（基于历史波动率）
  - exit_triggers: 5 条自动生成的离场触发条件
  - similar_stocks: pass-through from fetch_similar_stocks

Usage:
  python compute_friendly.py {ticker}
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from lib.cache import read_task_output  # noqa: E402


def _parse_pct(s) -> float:
    try:
        return float(str(s).replace("%", "").replace("+", ""))
    except (ValueError, TypeError):
        return 0.0


def compute_scenarios(raw: dict, dimensions: dict) -> dict:
    """5 级情景（最坏/偏差/合理/乐观/极致乐观）基于历史波动率。"""
    basic = (raw.get("dimensions", {}).get("0_basic") or {}).get("data") or {}
    kline = (raw.get("dimensions", {}).get("2_kline") or {}).get("data") or {}
    research = (raw.get("dimensions", {}).get("6_research") or {}).get("data") or {}

    entry_price = basic.get("price") or 0
    stats = kline.get("kline_stats") or {}
    # 1 年化波动率
    vol_str = stats.get("volatility", "30%")
    sigma = _parse_pct(vol_str) or 30.0

    # 研报目标价隐含的预期收益
    upside_str = research.get("upside", "+15%")
    base_return = _parse_pct(upside_str) or 15.0

    return {
        "entry_price": entry_price,
        "cases": [
            {"name": "最坏情况", "probability": "5%",  "return": round(-2 * sigma, 1)},
            {"name": "偏差情况", "probability": "25%", "return": round(-1 * sigma + base_return * 0.2, 1)},
            {"name": "合理情况", "probability": "40%", "return": round(base_return, 1)},
            {"name": "乐观情况", "probability": "25%", "return": round(1 * sigma + base_return * 0.5, 1)},
            {"name": "极致乐观", "probability": "5%",  "return": round(2 * sigma + base_return, 1)},
        ],
    }


def compute_exit_triggers(raw: dict, dimensions: dict, synthesis: dict) -> list[str]:
    """自动从已有数据生成 5 条离场触发条件。"""
    triggers = []
    basic = (raw.get("dimensions", {}).get("0_basic") or {}).get("data") or {}
    kline = (raw.get("dimensions", {}).get("2_kline") or {}).get("data") or {}
    val = (raw.get("dimensions", {}).get("10_valuation") or {}).get("data") or {}
    chain = (raw.get("dimensions", {}).get("5_chain") or {}).get("data") or {}
    lhb = (raw.get("dimensions", {}).get("16_lhb") or {}).get("data") or {}
    research = (raw.get("dimensions", {}).get("6_research") or {}).get("data") or {}

    # 1. 技术止损 ~ MA60
    ma60 = (kline.get("ma60_60d") or [])
    ma60_last = next((v for v in reversed(ma60) if v), None)
    if ma60_last:
        triggers.append(f"股价跌破 ¥{ma60_last:.2f}（60 日均线支撑位）→ 无条件止损")
    else:
        price = basic.get("price") or 0
        triggers.append(f"股价跌破 ¥{price * 0.88:.2f}（当前价 -12%）→ 无条件止损")

    # 2. 基本面恶化 — 大客户
    downstream = chain.get("downstream", "")
    if downstream and downstream != "—":
        main_client = downstream.split("/")[0].strip()
        triggers.append(f"{main_client} 季度指引下修 > 10% → 产业链逻辑动摇")
    else:
        triggers.append("下季度营收同比转负 → 基本面反转信号")

    # 3. 业绩不达
    growth_str = research.get("upside", "+15%")
    g = _parse_pct(growth_str)
    if g > 0:
        min_growth = max(10, int(g - 15))
        triggers.append(f"下次业绩预告低于 +{min_growth}% → 预期管理失守")
    else:
        triggers.append("连续两期业绩不及券商预期中位数 → 逻辑失效")

    # 4. 游资撤离
    matched = lhb.get("matched_youzi", "")
    if isinstance(matched, list):
        matched_str = " / ".join(matched[:2])
    else:
        matched_str = str(matched).split("/")[0] if matched else "顶级游资"
    if matched_str and matched_str not in ("", "—"):
        triggers.append(f"{matched_str} 席位大额卖出 > 2 亿 → 顶级资金撤离信号")

    # 5. 估值泡沫
    pe_quant = val.get("pe_quantile", "")
    import re
    m = re.search(r'(\d+)', str(pe_quant))
    if m:
        cur_q = int(m.group(1))
        target = min(95, cur_q + 15)
        triggers.append(f"PE 站上 5 年 {target} 分位（≈ {val.get('pe', '—')} × {1 + (target - cur_q) / 100:.2f}）→ 泡沫区获利了结")
    else:
        triggers.append("PE 站上 5 年 90 分位 → 泡沫区获利了结")

    return triggers[:5]


def main(ticker: str) -> dict:
    raw = read_task_output(ticker, "raw_data") or {}
    dimensions = read_task_output(ticker, "dimensions") or {}
    synthesis = read_task_output(ticker, "synthesis") or {}

    scenarios = compute_scenarios(raw, dimensions)
    exit_triggers = compute_exit_triggers(raw, dimensions, synthesis)

    # Similar stocks: 从 raw_data 的 similar_stocks stub 或独立 cache
    similar = (raw.get("similar_stocks") or [])[:4]

    friendly = {
        "scenarios": scenarios,
        "exit_triggers": exit_triggers,
        "similar_stocks": similar,
    }

    return friendly


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1] if len(sys.argv) > 1 else "002273.SZ"), ensure_ascii=False, indent=2, default=str))

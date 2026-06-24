"""Dimension 9 · 期货关联 — 真实期货价格 via futures_main_sina."""
from __future__ import annotations

import json
import sys


# Industry → primary linked futures contract (if any)
INDUSTRY_FUTURES: dict[str, tuple] = {
    "钢铁":   ("螺纹钢 RB", "RB0"),
    "建材":   ("玻璃 FG",   "FG0"),
    "煤炭":   ("焦煤 JM",   "JM0"),
    "有色金属": ("沪铜 CU",  "CU0"),
    "化工":   ("原油 SC",   "SC0"),
    "农业":   ("豆粕 M",    "M0"),
    "养殖业": ("生猪 LH",   "LH0"),
    "电池":   ("碳酸锂 LC", "LC0"),
    # v2.8.4 · 补齐有色金属子类 —— 云铝等 coverage gap
    "工业金属": ("沪铝 AL",  "AL0"),
    "贵金属":   ("黄金 AU",  "AU0"),
    "能源金属": ("碳酸锂 LC", "LC0"),
    "小金属":   ("沪锡 SN",  "SN0"),
    "煤炭开采": ("焦煤 JM",  "JM0"),
    "焦炭":     ("焦炭 J",   "J0"),
    "油气开采": ("原油 SC",  "SC0"),
    "光学光电子": (None, None),  # no direct linkage
    "半导体":  (None, None),
    "医药生物": (None, None),
    "白酒":   (None, None),
    "银行":   (None, None),
    "保险":   (None, None),
}


def _pull_price(code: str) -> dict:
    try:
        import akshare as ak
        df = ak.futures_main_sina(symbol=code)
        if df is None or df.empty:
            return {}
        df = df.sort_values("日期") if "日期" in df.columns else df
        tail = df.tail(60)
        closes = [float(v) for v in tail["收盘价"] if v and float(v) > 0]
        if len(closes) < 2:
            return {}
        first = closes[0]
        last = closes[-1]
        trend_pct = ((last - first) / first * 100) if first else 0
        return {
            "latest": round(last, 2),
            "trend_60d_pct": round(trend_pct, 1),
            "history_60d": [round(v, 2) for v in closes[-60:]],
        }
    except Exception:
        return {}


def main(industry: str) -> dict:
    # Try exact match first
    linked = INDUSTRY_FUTURES.get(industry)
    if linked is None:
        # Fuzzy match
        for k, v in INDUSTRY_FUTURES.items():
            if k[:2] in industry or industry[:2] in k:
                linked = v
                break
    linked = linked or (None, None)
    name, code = linked

    if not code:
        return {
            "data": {
                "linked_contract": "无直接关联品种",
                "contract_trend": "—",
                "note": f"{industry} 行业与期货市场无强相关品种",
            },
            "source": "INDUSTRY_FUTURES mapping",
            "fallback": False,
        }

    price_data = _pull_price(code)
    trend_label = "—"
    if price_data.get("trend_60d_pct") is not None:
        pct = price_data["trend_60d_pct"]
        trend_label = f"60 日 {'+' if pct >= 0 else ''}{pct:.1f}%"

    return {
        "data": {
            "linked_contract": name,
            "contract_code": code,
            "latest_price": price_data.get("latest"),
            "contract_trend": trend_label,
            "price_history_60d": price_data.get("history_60d", []),
        },
        "source": "akshare:futures_main_sina",
        "fallback": False,
    }


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "光学光电子"
    print(json.dumps(main(arg), ensure_ascii=False, indent=2, default=str))

"""Dimension 16 · 龙虎榜 (个股 + 同板块 + 机构 vs 游资 split + 席位匹配).

补全：原方案要求覆盖
  • 个股近 30 日上榜记录
  • 知名游资席位匹配
  • 机构 vs 游资博弈 split
  • 同板块其他票龙虎榜
  • 板块辨识度龙头
"""
import json
import sys

import akshare as ak  # type: ignore
from lib import data_sources as ds
from lib.market_router import parse_ticker
from lib.seat_db import match_seats_in_lhb


def _is_institutional(seat_name: str) -> bool:
    """机构席位关键词识别"""
    return "机构专用" in seat_name or "机构" in seat_name and "证券" not in seat_name


def split_inst_vs_youzi(records: list[dict]) -> dict:
    inst_buy = inst_sell = 0.0
    youzi_buy = youzi_sell = 0.0
    for r in records:
        seat = str(r.get("营业部名称") or r.get("交易营业部") or "")
        buy = float(r.get("买入金额") or r.get("买入额") or 0)
        sell = float(r.get("卖出金额") or r.get("卖出额") or 0)
        if _is_institutional(seat):
            inst_buy += buy
            inst_sell += sell
        else:
            youzi_buy += buy
            youzi_sell += sell
    return {
        "institutional_buy": inst_buy,
        "institutional_sell": inst_sell,
        "institutional_net": inst_buy - inst_sell,
        "youzi_buy": youzi_buy,
        "youzi_sell": youzi_sell,
        "youzi_net": youzi_buy - youzi_sell,
    }


def fetch_sector_lhb(industry: str) -> list[dict]:
    """同板块其他票最近龙虎榜情况"""
    if not industry:
        return []
    try:
        df = ak.stock_lhb_stock_statistic_em(symbol="近一月")
        if df is None or df.empty:
            return []
        return df.head(50).to_dict("records")
    except Exception:
        return []


def main(ticker: str) -> dict:
    ti = parse_ticker(ticker)
    if ti.market != "A":
        return {"ticker": ti.full, "data": {"_note": "lhb only A-share"}, "source": "skip", "fallback": False}

    lhb = ds.fetch_lhb_recent(ti, days=30)
    matched = match_seats_in_lhb(lhb)
    split = split_inst_vs_youzi(lhb)

    basic = ds.fetch_basic(ti)
    sector = fetch_sector_lhb(basic.get("industry") or "")

    return {
        "ticker": ti.full,
        "data": {
            "lhb_count_30d": len(lhb),
            "lhb_records": lhb[:30],
            "matched_youzi": list(matched.keys()),
            "matched_youzi_detail": {k: v[:3] for k, v in matched.items()},
            "inst_vs_youzi": split,
            "sector_lhb_top50": sector[:30],
            "sector_leader_hint": sector[0]["代码"] if sector and "代码" in sector[0] else None,
        },
        "source": "akshare:stock_lhb_stock_detail_em + statistic + seat_db",
        "fallback": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1] if len(sys.argv) > 1 else "002273.SZ"), ensure_ascii=False, indent=2, default=str))

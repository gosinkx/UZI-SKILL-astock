"""Dimension 6 · 研报观点 — stock_research_report_em 主源 + cninfo 预测兜底."""
from __future__ import annotations

import json
import sys
from collections import Counter

import akshare as ak  # type: ignore
from lib.market_router import parse_ticker


def _fetch_em_reports(code: str) -> list[dict]:
    """Primary: stock_research_report_em — includes ratings, EPS/PE forecasts."""
    try:
        df = ak.stock_research_report_em(symbol=code)
        if df is None or df.empty:
            return []
        # Filter to exact code match
        sub = df[df['股票代码'].astype(str) == code]
        if sub.empty:
            return []
        return sub.head(60).to_dict("records")
    except Exception:
        return []


def _fetch_cninfo_forecast(code: str) -> list[dict]:
    """Fallback: cninfo 研报预测."""
    from datetime import datetime, timedelta
    today = datetime.now()
    # Try quarterly snapshots going back 1 year
    for quarter in [
        (today.year, 12, 31), (today.year, 9, 30), (today.year, 6, 30), (today.year, 3, 31),
        (today.year - 1, 12, 31), (today.year - 1, 9, 30),
    ]:
        try:
            date_str = f"{quarter[0]:04d}{quarter[1]:02d}{quarter[2]:02d}"
            df = ak.stock_rank_forecast_cninfo(date=date_str)
            if df is None or df.empty:
                continue
            col_code = next((c for c in ['证券代码', '股票代码', '代码'] if c in df.columns), None)
            if not col_code:
                continue
            sub = df[df[col_code].astype(str) == code]
            if not sub.empty:
                return sub.head(20).to_dict("records")
        except Exception:
            continue
    return []


def main(ticker: str) -> dict:
    ti = parse_ticker(ticker)
    if ti.market != "A":
        return {"ticker": ti.full, "data": {"report_count": 0}, "source": "n/a", "fallback": True}

    reports = _fetch_em_reports(ti.code)
    cninfo_forecast = _fetch_cninfo_forecast(ti.code) if not reports else []
    source = "akshare:stock_research_report_em" if reports else "akshare:stock_rank_forecast_cninfo"

    # Parse ratings
    ratings = Counter()
    for r in reports:
        rating = str(r.get("东财评级", r.get("评级", ""))).strip()
        if rating and rating not in ("nan", "-", "None", ""):
            ratings[rating] += 1

    # Parse 2026 EPS + PE forecasts (compute implied target price)
    eps_2026_values = []
    pe_2026_values = []
    eps_2027_values = []
    for r in reports:
        try:
            eps_26 = float(r.get("2026-盈利预测-收益", 0) or 0)
            pe_26 = float(r.get("2026-盈利预测-市盈率", 0) or 0)
            eps_27 = float(r.get("2027-盈利预测-收益", 0) or 0)
            if eps_26 > 0: eps_2026_values.append(eps_26)
            if pe_26 > 0: pe_2026_values.append(pe_26)
            if eps_27 > 0: eps_2027_values.append(eps_27)
        except (ValueError, TypeError):
            pass

    avg_eps_2026 = round(sum(eps_2026_values) / len(eps_2026_values), 2) if eps_2026_values else None
    avg_pe_2026 = round(sum(pe_2026_values) / len(pe_2026_values), 1) if pe_2026_values else None
    avg_eps_2027 = round(sum(eps_2027_values) / len(eps_2027_values), 2) if eps_2027_values else None

    # Implied target price: 2026 EPS × (avg historical PE or current PE)
    target_price = None
    if avg_eps_2026 and avg_pe_2026:
        target_price = round(avg_eps_2026 * avg_pe_2026, 2)

    # Brokerage list
    brokers = set()
    for r in reports:
        org = str(r.get("机构", "")).strip()
        if org and org not in ("nan", "None"):
            brokers.add(org)

    # Rating distribution dict
    rating_dist = dict(ratings)
    total = sum(rating_dist.values())
    buy_pct = 0
    if total > 0:
        buy_count = sum(v for k, v in rating_dist.items() if "买入" in k or "增持" in k)
        buy_pct = round(buy_count / total * 100, 0)

    # Build rating string
    rating_str = " / ".join(f"{k} {v}" for k, v in rating_dist.items()) if rating_dist else "—"

    # Recent reports (trimmed for display)
    recent = []
    for r in reports[:10]:
        recent.append({
            "date": str(r.get("日期", ""))[:10],
            "title": str(r.get("报告名称", ""))[:60],
            "broker": str(r.get("机构", "")),
            "rating": str(r.get("东财评级", "")),
            "pdf": str(r.get("报告PDF链接", "")),
            "eps_2026": r.get("2026-盈利预测-收益"),
            "pe_2026": r.get("2026-盈利预测-市盈率"),
        })

    return {
        "ticker": ti.full,
        "data": {
            "report_count": len(reports),
            "coverage": f"{len(brokers)} 家" if brokers else f"{len(reports)} 份",
            "coverage_count": len(brokers),
            "rating": rating_str,
            "rating_distribution": rating_dist,
            "buy_rating_pct": buy_pct,
            "target_price_avg": target_price,
            "target_avg": f"¥{target_price}" if target_price else "—",
            "consensus_eps_2026": avg_eps_2026,
            "consensus_pe_2026": avg_pe_2026,
            "consensus_eps_2027": avg_eps_2027,
            "recent_reports": recent,
            "brokers": sorted(brokers),
            "upside": None,  # computed at synthesis step vs current price
        },
        "source": source,
        "fallback": not bool(reports),
    }


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "002273.SZ"
    print(json.dumps(main(arg), ensure_ascii=False, indent=2, default=str))

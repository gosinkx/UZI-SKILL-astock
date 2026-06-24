"""Dimension 15 · 事件驱动 — 用 cninfo 公告 + 新闻兜底 (避开被代理挡的 push2/datacenter)."""
from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime, timedelta

import akshare as ak  # type: ignore
from lib.market_router import parse_ticker
from lib.web_search import search as web_search, search_trusted


def _cninfo_direct_api(code: str, page_size: int = 30, timeout: int = 15) -> list[dict]:
    """v3.6.2 · 直连 cninfo /new/hisAnnouncement/query · 仅取第 1 页 30 条.

    解决 issue #68：akshare.stock_zh_a_disclosure_report_cninfo 内部翻完全部
    854 页才返回 · 实测单股几小时. 这里绕过 akshare · 设 pageSize=30 + pageNum=1 ·
    确保单次 HTTP 调用 ≤15s · 永远不会拖垮采集.

    Returns:
        list of {date, title, url, type} dicts. Empty list on failure.
    """
    import requests
    # 推断板块：000/001/002/300 → szse · 600/601/603/605/688 → sse
    code_prefix = code[:3]
    if code_prefix in ("000", "001", "002") or code.startswith("3"):
        column = "szse"
        prefix = "9900"
        org_id = ""  # cninfo 内部用 ticker 即可
        stock_code = f"{code},{org_id}" if org_id else code
    elif code_prefix in ("600", "601", "603", "605", "688", "689"):
        column = "sse"
        stock_code = code
    else:
        # 京 北交所
        column = "bse"
        stock_code = code

    url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
        "Origin": "http://www.cninfo.com.cn",
        "Referer": "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search",
    }
    payload = {
        "pageNum": 1,
        "pageSize": page_size,
        "column": column,
        "tabName": "fulltext",
        "plate": "",
        "stock": stock_code,
        "searchkey": "",
        "secid": "",
        "category": "",
        "trade": "",
        "seDate": "",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }
    try:
        r = requests.post(url, data=payload, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return []
        data = r.json()
    except (requests.RequestException, ValueError):
        return []

    announcements = data.get("announcements") or []
    rows = []
    for a in announcements[:page_size]:
        # cninfo 时间戳是毫秒
        ts = a.get("announcementTime") or 0
        try:
            date_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d") if ts else ""
        except (TypeError, ValueError, OSError):
            date_str = ""
        ann_url = a.get("adjunctUrl") or ""
        if ann_url and not ann_url.startswith("http"):
            ann_url = f"http://static.cninfo.com.cn/{ann_url.lstrip('/')}"
        rows.append({
            "date": date_str,
            "title": str(a.get("announcementTitle", "")),
            "url": ann_url,
            "type": "cninfo 公告",
        })
    return rows


def _cninfo_disclosures(code: str, days_back: int = 180) -> list[dict]:
    """Cninfo disclosures · v3.6.2 直连 API (pageSize=30) · 永不翻全部页.

    社群 issue #68：原先调 akshare.stock_zh_a_disclosure_report_cninfo · 该函数
    内部循环翻完所有 854 页才 return · 单股能拖几小时. v3.6.2 起 · 默认直连
    cninfo /new/hisAnnouncement/query · pageSize=30 · 15s 超时 · 失败 fallback
    到 akshare（akshare 路径仍可能慢 · 用 UZI_DISABLE_AK_CNINFO=1 完全禁用）.
    """
    import os
    # 优先：直连 cninfo HTTP API · 永远不会翻页超时
    rows = _cninfo_direct_api(code, page_size=30, timeout=15)
    if rows:
        return rows

    # Fallback：akshare 慢路径 · 默认禁用（防止 854 页长尾）·
    # 仅当用户显式 export UZI_AK_CNINFO_FALLBACK=1 才尝试
    if os.environ.get("UZI_AK_CNINFO_FALLBACK") != "1":
        return []  # 直连失败就空 · 不拖慢主流程

    today = datetime.now()
    start = (today - timedelta(days=days_back)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")
    try:
        df = ak.stock_zh_a_disclosure_report_cninfo(
            symbol=code, market="沪深京", category="", start_date=start, end_date=end,
        )
        if df is None or df.empty:
            return []
        rows = []
        for _, r in df.head(30).iterrows():
            rows.append({
                "date": str(r.get("公告时间", ""))[:10],
                "title": str(r.get("公告标题", "")),
                "url": str(r.get("公告链接", "")),
                "type": "cninfo 公告",
            })
        return rows
    except Exception as e:
        return [{"error": f"cninfo fail: {e}"}]


def _try_news(code: str) -> list[dict]:
    """Best-effort news from akshare stock_news_em — may fail on SSL."""
    try:
        df = ak.stock_news_em(symbol=code)
        if df is None or df.empty:
            return []
        rows = []
        for _, r in df.head(30).iterrows():
            title = str(r.get("新闻标题", ""))
            # Filter out irrelevant board/sector/capital-flow noise
            if _is_noise_news(title):
                continue
            rows.append({
                "date": str(r.get("发布时间", ""))[:16],
                "title": title,
                "type": "新闻",
                "source": str(r.get("文章来源", "")),
            })
            if len(rows) >= 12:
                break
        return rows
    except Exception:
        return []


# Noise patterns: board-level / index / capital flow headlines that aren't company-specific
_NOISE_KWS = [
    "主力资金净流", "资金流向日报", "资金流出榜", "资金流入榜",
    "科创板主力资金", "科创板平均股价", "创业板主力", "沪深主力",
    "行业资金流", "板块资金", "个股主力资金净",
    "只股中线走稳", "站上半年线", "股价超百元",
    "融资客大手笔", "融资净买入", "融资余额",
    "北向资金", "两融", "龙虎榜汇总",
    "板块涨幅", "行业今日", "大盘分析",
    "行业4月", "行业3月", "行业2月", "行业1月",
    "股涨停", "跌停", "涨幅榜",
    "家公司的调研", "解密主力资金出逃股",
    "收盘价创历史新高股", "只股获",
]


def _is_noise_news(title: str) -> bool:
    """Return True if this headline is board-level noise, not company-specific."""
    if not title:
        return True
    return sum(1 for kw in _NOISE_KWS if kw in title) >= 1


def _web_search_events(name: str, max_results: int = 6) -> list[dict]:
    """Fallback: web search for company-specific events / catalysts / news."""
    queries = [
        f"{name} 上市公司 最新动态 合同 订单 产品",
        f"{name} 业绩 研发 突破 合作",
    ]
    results = []
    seen = set()
    # v2.7.3 · 先用 15_events 权威域（中证网/证券时报/每经/交易所）搜，
    # 缺口用普通 search 兜底。权威源返回质量远高于百科/贴吧/小红书。
    for q in queries:
        res_trusted = search_trusted(q, dim_key="15_events", max_results=max_results)
        res_generic = web_search(q, max_results=max_results) if len(res_trusted) < 3 else []
        for r in list(res_trusted) + list(res_generic):
            if "error" in r:
                continue
            title = r.get("title", "")[:80]
            if title and title not in seen and not _is_noise_news(title):
                seen.add(title)
                results.append({
                    "date": "—",
                    "title": title,
                    "type": "web_search",
                    "source": r.get("url", ""),
                })
    return results[:8]


def main(ticker: str) -> dict:
    ti = parse_ticker(ticker)
    if ti.market == "H":
        # v2.5 · HK 走 HKEXNews + 中文 web search 兜底
        try:
            from lib.hk_data_sources import fetch_hk_announcements_cached
            from lib import data_sources as _ds
            basic = _ds.fetch_basic(ti)
            company_name = basic.get("name") or basic.get("full_name") or ti.code
            anns = fetch_hk_announcements_cached(ti.code.zfill(5), limit=20)
            # web_search 中文公司名补充（多数港股有中文名）
            ws_events = _web_search_events(company_name) if len(anns) < 5 else []
            timeline = [f"{a.get('date','—')} · {a.get('title','')[:80]}" for a in anns + ws_events]
            return {
                "ticker": ti.full,
                "data": {
                    "event_timeline": timeline[:30],
                    "recent_news": [
                        {"date": a.get("date", ""), "title": a.get("title", ""),
                         "url": a.get("url", ""), "source": a.get("source", "hkexnews")}
                        for a in anns
                    ],
                    "recent_notices": [],
                    "catalysts": [],
                    "warnings": [],
                    "_note": (
                        "HK 公司公告原文走 hkexnews 法定披露源 + 中文 web search 兜底；"
                        "若需更精确事件抽取，agent 用 Playwright 打开 hkexnews titlesearch.xhtml POST"
                    ),
                },
                "source": "hkexnews + ddgs",
                "fallback": False,
            }
        except Exception as e:
            return {
                "ticker": ti.full,
                "data": {"_err": f"{type(e).__name__}: {str(e)[:120]}"},
                "source": "hkexnews",
                "fallback": True,
            }
    if ti.market != "A":
        return {"ticker": ti.full, "data": {}, "source": "n/a", "fallback": True}

    # Get company name for web search fallback
    try:
        from lib import data_sources as ds
        basic = ds.fetch_basic(ti)
        company_name = basic.get("name") or ti.code
    except Exception:
        company_name = ti.code

    disclosures = _cninfo_disclosures(ti.code)
    news = _try_news(ti.code)

    # v2.13.7 · 多源新闻聚合（金十/东财快讯/东财公告/同花顺）· 直连 HTTP · ddgs 盲区
    try:
        from lib.news_providers import get_news_multi_source
        multi = get_news_multi_source(stock_code=ti.code, stock_name=company_name, limit_per_source=10)
        for src, items in (multi.get("sources") or {}).items():
            for it in items:
                if not isinstance(it, dict) or it.get("error"):
                    continue
                title = it.get("title", "")[:80]
                if not title or _is_noise_news(title):
                    continue
                news.append({
                    "date": (it.get("publish_time") or "")[:16] or "—",
                    "title": title,
                    "type": f"news_providers:{src}",
                    "source": it.get("url", ""),
                })
    except Exception:
        pass

    # If filtered news is too sparse, supplement with web search
    if len(news) < 3:
        ws_events = _web_search_events(company_name)
        news = news + ws_events

    # Merge + dedupe + sort by date desc
    merged = {}
    for item in disclosures + news:
        if "error" in item:
            continue
        k = item.get("title", "")[:80]
        if k and k not in merged:
            merged[k] = item
    sorted_events = sorted(merged.values(), key=lambda x: x.get("date", ""), reverse=True)

    # Build a compact timeline for the viz
    timeline = []
    for ev in sorted_events[:10]:
        date = ev.get("date", "")[:10] or "—"
        title = ev.get("title", "")[:70]
        timeline.append(f"{date} · {title}")

    # Extract forward-looking catalysts (from disclosure titles)
    catalysts = []
    for item in disclosures[:20]:
        title = item.get("title", "")
        # Company-relevant catalysts: contracts, earnings, approvals, etc.
        if any(kw in title for kw in ["合同", "中标", "业绩", "研发", "获批", "专利", "投资", "合作", "股权", "分红", "回购"]):
            catalysts.append({
                "date": item.get("date", ""),
                "event": title[:80],
                "impact": "medium",
            })

    # Warnings from disclosure titles
    warning_items = []
    for item in disclosures[:20]:
        title = item.get("title", "")
        if any(kw in title for kw in ["风险", "立案", "违规", "退市", "ST", "商誉减值", "资产减值", "业绩下滑"]):
            warning_items.append(title[:80])

    return {
        "ticker": ti.full,
        "data": {
            "event_timeline": timeline,
            "recent_news": news[:10],
            "recent_notices": disclosures[:20],
            "disclosures_count": len(disclosures),
            "news_count": len(news),
            "recent_news_label": f"{len(news)} 条新闻" if news else "—",
            "catalyst": catalysts[:5],
            "warnings": warning_items if warning_items else [],
        },
        "source": "cninfo:stock_zh_a_disclosure_report + akshare:stock_news_em + news_providers(jin10/em/ths) + web_search",
        "fallback": False,
    }


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "002273.SZ"
    try:
        print(json.dumps(main(arg), ensure_ascii=False, indent=2, default=str))
    except Exception:
        traceback.print_exc()

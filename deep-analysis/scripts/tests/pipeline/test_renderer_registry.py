"""v3.0.0 Phase 3 · 8 个 section renderer 测试."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_renderer_registry_has_8_sections():
    from lib.pipeline.renderer import list_renderers
    keys = list_renderers()
    # Phase 3 目标 8 个
    assert len(keys) >= 8, f"至少 8 个 renderer · 实际 {len(keys)}"


def test_moat_renderer_four_forces():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("14_moat")
    ctx = RenderContext(
        ticker="300470.SZ", name="中密控股",
        data={
            "intangible": "技术专利 + 品牌",
            "switching": "客户认证周期长",
            "network": "—",
            "scale": "龙头份额",
            "scores": {"intangible": 7, "switching": 8, "network": 4, "scale": 6},
        },
        quality="full"
    )
    html = r.render(ctx)
    assert "无形资产" in html and "7/10" in html
    assert "转换成本" in html and "8/10" in html
    assert "moat" in html


def test_financials_renderer_percent_format():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("1_financials")
    ctx = RenderContext(
        ticker="300470.SZ", name="中密控股",
        data={"roe": "13.8%", "net_margin": "21.8%", "revenue_growth": "+12.9%"},
    )
    html = r.render(ctx)
    assert "13.8%" in html
    assert "21.8%" in html


def test_peers_renderer_gap_when_empty():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("4_peers")
    ctx = RenderContext(ticker="x", name="y", data={"peer_table": [], "peer_comparison": []})
    html = r.render(ctx)
    assert "section-gap" in html or "同行" in html


def test_industry_renderer_shows_cninfo_metrics():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("7_industry")
    ctx = RenderContext(
        ticker="x", name="y",
        data={
            "industry": "机械设备",
            "growth": "+12%",
            "cninfo_metrics": {"industry_pe_weighted": 65.33, "total_mcap_yi": 5000, "company_count": 120},
        },
    )
    html = r.render(ctx)
    assert "机械设备" in html
    assert "65.33" in html


def test_sentiment_heat_bar():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("17_sentiment")
    ctx = RenderContext(
        ticker="x", name="y",
        data={"thermometer_value": 85, "positive_pct": "67%", "sentiment_label": "乐观"},
    )
    html = r.render(ctx)
    assert "85" in html
    assert "乐观" in html


def test_events_shows_catalysts_and_warnings():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("15_events")
    ctx = RenderContext(
        ticker="x", name="y",
        data={
            "event_timeline": ["2026-04-15 · 发布分红规划"],
            "catalyst": [{"date": "2026-04-15", "event": "股东回报规划"}],
            "warnings": ["资产减值准备"],
        },
    )
    html = r.render(ctx)
    assert "分红规划" in html or "股东回报" in html
    assert "资产减值" in html


def test_basic_header_shows_price_pe():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("0_basic")
    ctx = RenderContext(
        ticker="300470.SZ", name="中密控股",
        data={
            "name": "中密控股", "price": 36.52, "market_cap": "76 亿",
            "pe_ttm": 19.8, "pb": 2.63, "industry": "机械设备",
        },
    )
    html = r.render(ctx)
    assert "中密控股" in html
    assert "36.52" in html or "¥36.52" in html
    assert "19.8" in html


def test_renderer_gap_mode_on_missing_quality():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("14_moat")
    ctx = RenderContext(ticker="x", name="y", data={}, quality="missing")
    html = r.render(ctx)
    assert "section-gap" in html
    assert "数据未抓到" in html or "数据不足" in html

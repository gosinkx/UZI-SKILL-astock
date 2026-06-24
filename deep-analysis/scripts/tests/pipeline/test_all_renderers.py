"""v3.0.0 Phase 5 · 全 21 个 renderer 完整覆盖测试."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SCRIPTS))


ALL_DIMS = [
    "0_basic", "1_financials", "2_kline", "3_macro", "4_peers",
    "5_chain", "6_fund_holders", "6_research", "7_industry", "8_materials",
    "9_futures", "10_valuation", "11_governance", "12_capital_flow",
    "13_policy", "14_moat", "15_events", "16_lhb", "17_sentiment",
    "18_trap", "19_contests",
]


def test_registry_has_all_21_renderers():
    """全部 21 个 dim 都有对应 renderer."""
    from lib.pipeline.renderer import list_renderers, RENDERER_REGISTRY
    registered = set(list_renderers())
    expected = set(ALL_DIMS)
    missing = expected - registered
    assert not missing, f"缺少 renderer: {missing}"
    assert len(RENDERER_REGISTRY) == 21, f"注册表应 21 个，实际 {len(RENDERER_REGISTRY)}"


def test_each_renderer_instantiable():
    from lib.pipeline.renderer import get_renderer
    for dim in ALL_DIMS:
        r = get_renderer(dim)
        assert r is not None, f"{dim} 无法实例化"
        assert r.section_id, f"{dim}.section_id 为空"


def test_each_renderer_produces_html_on_empty_data():
    """即使 data={} · 每个 renderer 都应返 valid HTML（gap 模式）· 不应崩溃."""
    from lib.pipeline.renderer import get_renderer, RenderContext
    for dim in ALL_DIMS:
        r = get_renderer(dim)
        ctx = RenderContext(ticker="x", name="y", data={}, quality="missing")
        html = r.render(ctx)
        assert isinstance(html, str)
        assert len(html) > 0
        assert "<section" in html or "<div" in html


def test_kline_renderer_percent_formatting():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("2_kline")
    ctx = RenderContext(ticker="x", name="y",
                        data={"price_change_1m": 5.5, "price_change_3m": -3.2, "rsi": 55})
    html = r.render(ctx)
    assert "+5.5%" in html or "5.5" in html
    assert "55" in html


def test_valuation_renderer_percentile():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("10_valuation")
    ctx = RenderContext(ticker="x", name="y",
                        data={"pe_ttm": 19.8, "pb": 2.63, "pe_percentile": "5%"})
    html = r.render(ctx)
    assert "19.8" in html
    assert "2.63" in html
    assert "5%" in html


def test_policy_renderer_sentiment_emoji():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("13_policy")
    ctx = RenderContext(ticker="x", name="y",
                        data={"policy_dir": "积极", "subsidy": "积极",
                              "monitoring": "中性", "anti_trust": "收紧"})
    html = r.render(ctx)
    assert "🟢" in html  # 积极
    assert "🟡" in html  # 中性
    assert "🔴" in html  # 收紧


def test_trap_renderer_high_risk_color():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("18_trap")
    ctx = RenderContext(ticker="x", name="y",
                        data={"risk_score": 75, "warning_flags": ["异常换手", "高位融资"]})
    html = r.render(ctx)
    assert "75" in html
    assert "高风险" in html
    assert "异常换手" in html


def test_lhb_gap_when_no_record():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("16_lhb")
    ctx = RenderContext(ticker="x", name="y",
                        data={"lhb_count_30d": 0, "lhb_records": [], "matched_youzi": []})
    html = r.render(ctx)
    assert "section-gap" in html or "未上龙虎榜" in html


def test_materials_renderer_list_detail():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("8_materials")
    ctx = RenderContext(ticker="x", name="y",
                        data={
                            "core_material": "特种石墨",
                            "price_trend": "温和上涨",
                            "materials_detail": [
                                {"name": "石墨", "price_change": "+5%"},
                                {"name": "碳化硅", "price_change": "-2%"},
                            ]
                        })
    html = r.render(ctx)
    assert "特种石墨" in html
    assert "石墨" in html
    assert "碳化硅" in html


def test_macro_renderer_multiple_factors():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("3_macro")
    ctx = RenderContext(ticker="x", name="y",
                        data={"rate_cycle": "降息周期", "fx_trend": "人民币走弱",
                              "geo_risk": "中美关系缓和", "commodity": "油价企稳"})
    html = r.render(ctx)
    assert "降息" in html
    assert "人民币" in html
    assert "中美" in html
    assert "油价" in html


def test_chain_renderer_shows_upstream_downstream():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("5_chain")
    ctx = RenderContext(ticker="x", name="y",
                        data={"upstream": ["石墨", "陶瓷"], "downstream": ["化工", "核电"]})
    html = r.render(ctx)
    assert "石墨" in html or "陶瓷" in html
    assert "化工" in html or "核电" in html


def test_research_renderer_coverage():
    from lib.pipeline.renderer import get_renderer, RenderContext
    r = get_renderer("6_research")
    ctx = RenderContext(ticker="x", name="y",
                        data={"coverage": "8 份", "buy_rating_pct": "75%",
                              "target_price_avg": "¥50.2"})
    html = r.render(ctx)
    assert "8" in html
    assert "75%" in html

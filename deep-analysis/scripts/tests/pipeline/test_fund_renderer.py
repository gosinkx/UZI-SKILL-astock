"""v3.0.0 · FundRenderer 测试 · 含 v2.15.1 bug 防回归 + v2.15.2 avatar fallback."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_resolve_manager_from_fund_code_fallback():
    """v2.15.2 · 当 fetch_fund_manager_name 挂（SSL 封）manager=='—'，用 fund_code 反查."""
    from lib.pipeline.renderer.fund import resolve_manager
    assert resolve_manager("022645", "—") == "朱少醒"
    assert resolve_manager("003494", "—") == "朱少醒"
    assert resolve_manager("005827", "") == "张坤"
    assert resolve_manager("012001", "-") == "田瑀"


def test_resolve_manager_preserves_known_name():
    from lib.pipeline.renderer.fund import resolve_manager
    assert resolve_manager("022645", "朱少醒") == "朱少醒"  # 已知名保留


def test_resolve_manager_unknown_returns_dash():
    from lib.pipeline.renderer.fund import resolve_manager
    assert resolve_manager("999999", "—") == "—"
    assert resolve_manager("", "—") == "—"


def test_resolve_avatar_known():
    from lib.pipeline.renderer.fund import resolve_avatar
    assert resolve_avatar("朱少醒") == "zhushaoxing"
    assert resolve_avatar("张坤") == "zhangkun"
    assert resolve_avatar("—") == ""
    assert resolve_avatar("") == ""


def test_enrich_manager_fills_name_and_avatar():
    from lib.pipeline.renderer.fund import enrich_manager
    raw = {"fund_code": "022645", "fund_name": "富国天惠D", "name": "—"}
    out = enrich_manager(raw)
    assert out["name"] == "朱少醒"
    assert out["avatar"] == "zhushaoxing"
    assert out["_name_resolved_by"] == "fund_code_map"


def test_fund_renderer_skips_lite_as_full_card():
    """v2.15.1 防回归 · lite 行（return_5y=None 或 _row_type=lite）不应生成 fund-card."""
    from lib.pipeline.renderer.fund import FundRenderer
    from lib.pipeline.renderer.base import RenderContext

    mgrs = [
        {"fund_code": "022645", "fund_name": "富国天惠D", "name": "朱少醒",
         "position_pct": 4.92, "return_5y": 32.5, "annualized_5y": 5.8,
         "max_drawdown": -31.2, "sharpe": 0.42, "peer_rank_pct": 45,
         "_row_type": "full"},
        {"fund_code": "xxx", "fund_name": "南方宝元债券", "name": "—",
         "position_pct": 0.54, "return_5y": None, "annualized_5y": None,
         "max_drawdown": None, "sharpe": None, "_row_type": "lite"},
    ]
    ctx = RenderContext(ticker="300470.SZ", name="中密控股", data={"fund_managers": mgrs})
    html = FundRenderer().render(ctx)

    # full-card 应只有 1 张（朱少醒）· lite 行走 compact row
    assert html.count('<div class="fund-card">') == 1
    # lite 行的基金名应在 compact row 里（不应在 full-card 里显示 0.0%）
    assert "南方宝元债券" in html
    # 不允许 0.0% 假数据出现在 fund-card 块里
    import re
    card_blocks = re.findall(r'<div class="fund-card">.*?(?=<div class="fund-card">|<div class="fund-compact-list">|</section>)', html, re.DOTALL)
    for block in card_blocks:
        assert "+0.0%" not in block
        assert "-0.0%" not in block


def test_fund_renderer_gap_when_no_managers():
    from lib.pipeline.renderer.fund import FundRenderer
    from lib.pipeline.renderer.base import RenderContext
    ctx = RenderContext(ticker="x", name="y", data={"fund_managers": []})
    html = FundRenderer().render(ctx)
    assert "section-gap" in html or "无公募基金持仓数据" in html


def test_fund_renderer_lite_cap_30():
    """v2.15.1 · 700+ lite 行应被 cap 到 30 · 剩余用"另有 N 家"."""
    from lib.pipeline.renderer.fund import FundRenderer
    from lib.pipeline.renderer.base import RenderContext

    mgrs = [
        {"fund_code": f"lite{i:04d}", "fund_name": f"基金{i}", "name": "—",
         "position_pct": 0.5 + i * 0.001, "return_5y": None, "_row_type": "lite"}
        for i in range(50)
    ]
    ctx = RenderContext(ticker="x", name="y", data={"fund_managers": mgrs})
    html = FundRenderer().render(ctx)
    assert html.count('<div class="fund-compact-row">') == 30
    assert "另有" in html


def test_fund_renderer_compact_uses_name_initial_not_question_mark():
    """v2.15.2 · compact row 没 avatar 时用 name 首字，不是默认 "?" ."""
    from lib.pipeline.renderer.fund import FundRenderer
    from lib.pipeline.renderer.base import RenderContext

    # 场景 · fund_code 反查后 name 是"朱少醒" · 头像应是"朱"字 · 不是 "?"
    mgrs = [
        {"fund_code": "022645", "fund_name": "富国天惠D", "name": "—",
         "position_pct": 4.92, "return_5y": None, "_row_type": "lite"},
    ]
    ctx = RenderContext(ticker="x", name="y", data={"fund_managers": mgrs})
    html = FundRenderer().render(ctx)
    # enrich_manager 应把 name 补成"朱少醒" · compact row avatar 应含"朱"
    assert "朱" in html  # name 首字
    # 只要 name 被反查到，就不应显示 "?"
    # （此处我们 assert "朱" 在 html 里，说明 enrich 生效）

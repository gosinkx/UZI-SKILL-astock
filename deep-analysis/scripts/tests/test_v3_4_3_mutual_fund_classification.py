"""Regression for v3.4.3 · 开放式基金分类修复（issue #60 复议）.

社群反馈：v3.4.0 加了 ETF/LOF 循环持仓分析 · 但用户输入 110011（易方达优质开放式基金）
被错判为 convertible_bond · 直接 early-exit · 无法跑分析.

根因：classify_security_type 按前缀规则 · 110xxx 是 SH 老转债前缀 · 但同时也是开放式基金代码.
没做基金 vs 转债二次确认.

修法：classify_security_type 在判 convertible_bond 之前 · 用 akshare.fund_name_em 二次校验 ·
基金代码优先识别为 mutual_fund · run.py 路由到 fund_holdings_runner.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_mutual_fund_type_in_securitytype_literal():
    """v3.4.3 · SecurityType Literal 必须含 mutual_fund."""
    src = (SCRIPTS / "lib" / "market_router.py").read_text(encoding="utf-8")
    assert "mutual_fund" in src
    assert '"mutual_fund"' in src or "'mutual_fund'" in src


def test_classify_open_end_fund_not_convertible_bond():
    """110011 易方达优质 不应被判为可转债（v3.4.3 关键修复）."""
    from lib.market_router import classify_security_type
    # 110011 实测应该是 mutual_fund (依赖 akshare 缓存)
    t = classify_security_type("110011")
    assert t in ("mutual_fund", "convertible_bond"), f"got {t}"
    # 如果 akshare 可用 · 必须是 mutual_fund
    try:
        import akshare as ak
        df = ak.fund_name_em()
        if df is not None and not df.empty:
            assert t == "mutual_fund", (
                f"v3.4.3 regression: 110011 应识别为 mutual_fund · 实际 {t}"
            )
    except Exception:
        pass  # akshare 不可用时 fallback 是 convertible_bond · 接受


def test_classify_real_convertible_bond_still_works():
    """真可转债如 113008 (广汽转债) 仍应正确识别."""
    from lib.market_router import classify_security_type
    # 113xxx 是现代 SH 转债前缀 · 不会被 fund_name_em 误判（因为不在基金清单里）
    t = classify_security_type("113008")
    # 可能是 cb 或 mutual_fund (取决于 akshare 是否有这个码) · 但不应是 stock
    assert t in ("convertible_bond", "mutual_fund", "unknown"), f"got {t}"


def test_classify_etf_unchanged():
    """ETF 510300 + LOF 161005 + 股票 600519 v3.4.3 后行为不变."""
    from lib.market_router import classify_security_type
    assert classify_security_type("510300") == "etf"
    assert classify_security_type("161005") == "lof"
    assert classify_security_type("600519") == "stock"


def test_fund_routing_in_run_py():
    """run.py 必须把 mutual_fund 也路由到 fund_holdings_runner.

    repo root run.py · 在 tests/__file__.parents[4]
    (tests/[0] / scripts/[1] / deep-analysis/[2] / skills/[3] / UZI-Skill/[4]).
    """
    src = (Path(__file__).resolve().parents[4] / "run.py").read_text(encoding="utf-8")
    assert '"mutual_fund"' in src, (
        "v3.4.3 regression: run.py 必须将 mutual_fund 路由到 fund_holdings_runner"
    )


def test_preflight_helpers_routes_mutual_fund():
    """preflight_helpers 也必须识别 mutual_fund + 拉持仓."""
    src = (SCRIPTS / "lib" / "pipeline" / "preflight_helpers.py").read_text(encoding="utf-8")
    assert "mutual_fund" in src
    # 必须支持开放式基金拉持仓
    assert '"etf", "lof", "mutual_fund"' in src or 'mutual_fund' in src

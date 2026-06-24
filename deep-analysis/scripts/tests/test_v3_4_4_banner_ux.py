"""Regression for v3.4.4 · data_gap_banner UX 优化.

社群反馈：
1. ETF 17% 覆盖率 banner 让人误以为"数据不可信"· 实际是基金类型本身没个股字段
2. 橙底橙字（#f59e0b / #fbbf24）看不清 · 对比度差

修法：
1. _render_data_gap_banner 新增 raw 参数 · 检测 ETF/LOF/mutual_fund · 切换 fund-type banner
2. fund-type banner 文案明确"基金类型预期缺字段·不影响可信度"
3. CSS 加深字色 (#f59e0b → #92400e/#7c2d12) + 加粗 + 基金类型用蓝色调
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


def _make_gaps(cov: int = 17, n: int = 15) -> dict:
    return {
        "tasks": [
            {"label": f"字段{i}", "dim": "1_financials" if i % 2 else "0_basic",
             "severity": "critical", "status": "unresolved"}
            for i in range(n)
        ],
        "coverage_pct": cov,
        "unresolved": n,
    }


def test_stock_uses_classic_banner():
    """普通 stock · 仍走老 banner · 文案不变."""
    from lib.report.institutional import _render_data_gap_banner
    raw = {"ticker": "600519.SH",
           "dimensions": {"0_basic": {"data": {"security_type": "stock"}}}}
    html = _render_data_gap_banner(_make_gaps(89), raw=raw)
    assert "data-gap-banner" in html
    assert "fund-type" not in html, "stock 不应走 fund-type banner"
    assert "DATA QUALITY" in html


def test_etf_uses_fund_type_banner_with_friendly_copy():
    """ETF · 走 fund-type banner · 文案明确"不影响可信度"."""
    from lib.report.institutional import _render_data_gap_banner
    raw = {"ticker": "510300.SH",
           "dimensions": {"0_basic": {"data": {"security_type": "etf"}}}}
    html = _render_data_gap_banner(_make_gaps(17), raw=raw)
    assert "data-gap-banner fund-type" in html
    assert "FUND-TYPE NOTE" in html
    assert "不影响分析可信度" in html or "不影响" in html
    # 必须引导用户去看持仓股
    assert "持仓" in html


def test_mutual_fund_uses_fund_type_banner():
    """开放式基金（mutual_fund · v3.4.3 新类型）也用 fund-type banner."""
    from lib.report.institutional import _render_data_gap_banner
    raw = {"ticker": "110011.SH",
           "dimensions": {"0_basic": {"data": {"security_type": "mutual_fund"}}}}
    html = _render_data_gap_banner(_make_gaps(20), raw=raw)
    assert "fund-type" in html
    assert "开放式基金" in html


def test_lof_uses_fund_type_banner():
    """LOF 也是 fund 类型."""
    from lib.report.institutional import _render_data_gap_banner
    raw = {"ticker": "161005.SZ",
           "dimensions": {"0_basic": {"data": {"security_type": "lof"}}}}
    html = _render_data_gap_banner(_make_gaps(20), raw=raw)
    assert "fund-type" in html
    assert "LOF" in html


def test_ticker_only_infers_type():
    """raw 里没显式 security_type 时 · 通过 ticker 反推（510300 应识别为 ETF）."""
    from lib.report.institutional import _render_data_gap_banner
    raw = {"ticker": "510300.SH"}  # 无 dimensions.0_basic
    html = _render_data_gap_banner(_make_gaps(17), raw=raw)
    assert "fund-type" in html, "ticker 反推应识别 ETF 走 fund-type"


def test_no_raw_back_compat():
    """不传 raw 时不崩 · 走老 banner（向后兼容）."""
    from lib.report.institutional import _render_data_gap_banner
    html = _render_data_gap_banner(_make_gaps(89))
    assert "data-gap-banner" in html
    assert "fund-type" not in html


def test_empty_gaps_returns_empty_string():
    """无 data_gaps 时返空（向后兼容）."""
    from lib.report.institutional import _render_data_gap_banner
    assert _render_data_gap_banner(None) == ""
    assert _render_data_gap_banner({}) == ""
    assert _render_data_gap_banner({"tasks": []}) == ""


# ─── CSS 对比度回归 ────────────────────────────────────────────

def test_css_subtitle_strong_uses_high_contrast():
    """CSS · subtitle strong 必须用深棕色 (#7c2d12) · 不能再用浅橙 #f59e0b."""
    tpl = (SCRIPTS.parent / "assets" / "report-template.html").read_text(encoding="utf-8")
    # 找 .data-gap-banner .subtitle strong 规则
    idx = tpl.find(".data-gap-banner .subtitle strong")
    assert idx > 0
    rule = tpl[idx:idx + 200]
    assert "#7c2d12" in rule or "#92400e" in rule or "#b45309" in rule, (
        f"v3.4.4 regression: subtitle strong 应用深棕色提高对比度 · 当前: {rule[:150]}"
    )


def test_css_title_uses_high_contrast():
    """CSS · banner title 必须用深棕 (#92400e) · 不能再用浅橙 #f59e0b."""
    tpl = (SCRIPTS.parent / "assets" / "report-template.html").read_text(encoding="utf-8")
    idx = tpl.find(".data-gap-banner .title")
    assert idx > 0
    rule = tpl[idx:idx + 250]
    assert "#92400e" in rule or "#7c2d12" in rule, (
        f"v3.4.4 regression: banner title 应深棕色 · 当前: {rule[:200]}"
    )


def test_css_chip_high_contrast():
    """CSS · chip 文字深棕色 + 加粗 · 替代之前的浅橙 #fbbf24."""
    tpl = (SCRIPTS.parent / "assets" / "report-template.html").read_text(encoding="utf-8")
    idx = tpl.find(".data-gap-banner .chip {")
    assert idx > 0
    rule = tpl[idx:idx + 400]
    assert "#7c2d12" in rule or "#92400e" in rule, (
        f"v3.4.4 regression: chip 文字应深棕 · 当前: {rule[:300]}"
    )
    # font-weight 不能是默认 normal
    assert "font-weight: 600" in rule or "font-weight: 700" in rule or "font-weight: 800" in rule, (
        f"chip 应加粗提高对比 · 当前: {rule[:300]}"
    )


def test_fund_type_banner_uses_blue_color():
    """fund-type banner 用蓝色调 · 区别于"问题"橙色调 · 暗示这是信息提示而非警告."""
    tpl = (SCRIPTS.parent / "assets" / "report-template.html").read_text(encoding="utf-8")
    idx = tpl.find(".data-gap-banner.fund-type {")
    assert idx > 0, "v3.4.4 应有 fund-type 专用 CSS"
    rule = tpl[idx:idx + 500]
    # 蓝色 sky / cyan
    assert "#0369a1" in rule or "#0c4a6e" in rule or "rgba(14, 165, 233" in rule, (
        f"fund-type banner 应蓝色调 · 当前: {rule[:300]}"
    )

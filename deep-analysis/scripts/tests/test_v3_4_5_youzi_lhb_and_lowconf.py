"""Regression for v3.4.5 · 两点社群反馈修复.

用户反馈 (京东方 000725 实测)：
1. **F 派 23 人全 skip · 但 LHB 实际有 3-5 个游资席位参与涨停** → 规则与数据脱节
2. **fund_score 37.6 但 agent 重评 65/100** · 报告强调 "0 看多 / 24 看空" 误导

修法：
- v3.4.5 fix #1: lib.investor_evaluator._is_youzi_out_of_range · 若 LHB 30 天该席位实际参与 · 即使股票市值超出射程也强制评分（matched_youzi 反查覆盖）
- v3.4.5 fix #2: _render_data_gap_banner · stock 类型 + fund_score<50 + cov<60% → 渲染 low-confidence 红色 banner · 引导用户看 agent 重评 · 不要盲信 0/24 票数
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


# ─── #1 · 游资 LHB 反查 ───────────────────────────────────

def test_youzi_skipped_when_no_lhb_match_and_oversize():
    """大市值 (2000 亿) + LHB 无该游资 → 仍 skip（保留 v2.13.3 行为）."""
    from lib.investor_evaluator import _is_youzi_out_of_range
    features = {"market_cap_yi": 2000, "matched_youzi": []}
    out, reason = _is_youzi_out_of_range("zhao_lg", features)
    assert out is True
    assert "不在" in reason and "射程" in reason


def test_youzi_active_when_lhb_shows_participation():
    """v3.4.5 · 大市值 + LHB 显示该游资真实参与 → 不 skip · 强制评分."""
    from lib.investor_evaluator import _is_youzi_out_of_range
    features = {"market_cap_yi": 2000, "matched_youzi": ["赵老哥", "孙哥"]}
    out, reason = _is_youzi_out_of_range("zhao_lg", features)
    assert out is False, "LHB 反查应覆盖射程限制 · 让评委参与评分"


def test_youzi_normal_range_unchanged():
    """中小盘股 · 在射程内 · 行为不变."""
    from lib.investor_evaluator import _is_youzi_out_of_range
    features = {"market_cap_yi": 100, "matched_youzi": []}  # 100 亿在射程内
    out, _ = _is_youzi_out_of_range("zhao_lg", features)
    assert out is False


def test_non_f_school_not_affected():
    """非 F 派评委 (如巴菲特 buffett) · 不受 LHB 反查逻辑影响."""
    from lib.investor_evaluator import _is_youzi_out_of_range
    features = {"market_cap_yi": 2000, "matched_youzi": ["buffett"]}
    out, _ = _is_youzi_out_of_range("buffett", features)
    assert out is False  # 非 F 派 · 永远返 False


# ─── #2 · low-confidence banner ──────────────────────────

def _gaps(cov: int = 30, n: int = 15) -> dict:
    return {
        "tasks": [
            {"label": f"字段{i}", "dim": "0_basic" if i % 2 else "1_financials",
             "severity": "critical", "status": "unresolved"}
            for i in range(n)
        ],
        "coverage_pct": cov,
        "unresolved": n,
    }


def test_low_confidence_triggers_when_fund_score_and_cov_low():
    """v3.4.5 · stock + fund_score 37 + cov 30% → 渲染 low-confidence banner."""
    from lib.report.institutional import _render_data_gap_banner
    raw = {"ticker": "000725.SZ", "dimensions": {"0_basic": {"data": {"security_type": "stock"}}}}
    syn = {"fundamental_score": 37.6}
    html = _render_data_gap_banner(_gaps(30), raw=raw, syn=syn)
    assert "low-confidence" in html
    assert "LOW CONFIDENCE" in html
    assert "🚨" in html
    # 必须引导用户看 agent 重评
    assert "agent 重评" in html or "agent 重评估" in html


def test_low_confidence_not_triggered_for_etf():
    """ETF 走 fund-type banner（v3.4.4）· 不应触发 low-confidence."""
    from lib.report.institutional import _render_data_gap_banner
    raw = {"ticker": "510300.SH", "dimensions": {"0_basic": {"data": {"security_type": "etf"}}}}
    syn = {"fundamental_score": 30}  # 即使 fund_score 低
    html = _render_data_gap_banner(_gaps(17), raw=raw, syn=syn)
    assert "fund-type" in html
    assert "low-confidence" not in html, "ETF 应走 fund-type · 不能也是 low-confidence"


def test_low_confidence_not_triggered_when_fund_score_ok():
    """fund_score 60 + cov 30 · fund_score 没问题 · 不触发 low-confidence."""
    from lib.report.institutional import _render_data_gap_banner
    raw = {"ticker": "000725.SZ", "dimensions": {"0_basic": {"data": {"security_type": "stock"}}}}
    syn = {"fundamental_score": 60}
    html = _render_data_gap_banner(_gaps(30), raw=raw, syn=syn)
    assert "low-confidence" not in html


def test_low_confidence_not_triggered_when_coverage_ok():
    """fund_score 37 + cov 80 · 数据齐 · 不触发 low-confidence."""
    from lib.report.institutional import _render_data_gap_banner
    raw = {"ticker": "000725.SZ", "dimensions": {"0_basic": {"data": {"security_type": "stock"}}}}
    syn = {"fundamental_score": 37}
    html = _render_data_gap_banner(_gaps(80), raw=raw, syn=syn)
    assert "low-confidence" not in html


def test_low_confidence_no_syn_back_compat():
    """不传 syn 时 · 走老 banner · 不崩."""
    from lib.report.institutional import _render_data_gap_banner
    raw = {"ticker": "000725.SZ"}
    html = _render_data_gap_banner(_gaps(30), raw=raw)  # 无 syn
    assert "data-gap-banner" in html
    assert "low-confidence" not in html


def test_css_low_confidence_high_contrast():
    """CSS · low-confidence 必须用深红 #7f1d1d 高对比 · 不能用浅红淡黄."""
    tpl = (SCRIPTS.parent / "assets" / "report-template.html").read_text(encoding="utf-8")
    idx = tpl.find(".data-gap-banner.low-confidence")
    assert idx > 0, "v3.4.5 应有 low-confidence CSS"
    rule = tpl[idx:idx + 800]
    assert "#7f1d1d" in rule or "#b91c1c" in rule, (
        f"low-confidence 应用深红 #7f1d1d/#b91c1c · 当前: {rule[:200]}"
    )

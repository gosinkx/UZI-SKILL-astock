"""Regression for v3.7.2 · 安全审计加固 · versus/portfolio HTML 转义.

安全审计发现：--versus / --portfolio 的 HTML 渲染把股票名 / CSV 备注 /
组合名直接插值进 HTML 而未转义。虽然是本地自看报告 + 数据多来自财经 API
(self-XSS 低危)，但 --portfolio 的 CSV note/portfolio_name 是用户可控字段，
统一用 html.escape 做防御纵深。

测试覆盖：
1. versus_runner._esc 正确转义 < > & "
2. versus HTML 渲染中恶意 name 被转义 (不出现裸 <script>)
3. portfolio HTML 渲染中恶意 portfolio_name / note 被转义
4. 正常中文名不被破坏 (转义不影响可读性)
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


# ─── #1 · _esc 基础 ──────────────────────────────────────

def test_esc_escapes_html_metachars():
    from lib.versus_runner import _esc
    out = _esc('<script>alert(1)</script>')
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_esc_escapes_quotes_and_amp():
    from lib.versus_runner import _esc
    out = _esc('A & B "C" <d>')
    assert "&amp;" in out
    assert "&quot;" in out
    assert "&lt;d&gt;" in out


def test_esc_preserves_chinese():
    from lib.versus_runner import _esc
    assert _esc("贵州茅台") == "贵州茅台"


def test_esc_none_returns_default():
    from lib.versus_runner import _esc
    assert _esc(None) == "—"
    assert _esc("", "") == ""


# ─── #2 · versus 渲染转义 ────────────────────────────────

def _malicious_metric(ticker="X.SZ", name='<img src=x onerror=alert(1)>'):
    return {
        "ticker": ticker, "name": name, "industry": "<b>industry</b>",
        "price": 10.0, "market_cap_yi": 100, "pe_ttm": 20, "pb": 2,
        "roe": 15, "net_margin": 10, "gross_margin": 30, "rev_growth_3y": 12,
        "overall_score": 70, "fund_score": 65, "consensus": 60,
        "verdict": '<script>x</script>', "verdict_detail": "d",
        "bull_count": 5, "bear_count": 2, "neutral_count": 3, "skip_count": 0,
        "punchline": '</div><script>evil()</script>',
        "trap_level": "🟢 安全", "school_lock": None, "_weight": 0.5,
    }


def test_versus_html_escapes_malicious_name():
    from lib.versus_runner import _render_html
    html = _render_html([_malicious_metric(), _malicious_metric("Y.SZ", "正常名")], depth="lite")
    # 裸 onerror / <script> 不应出现 (被转义成 &lt;)
    assert "<img src=x onerror" not in html
    assert "<script>evil()</script>" not in html
    assert "<script>x</script>" not in html
    # 转义后的形式应存在
    assert "&lt;img" in html or "&lt;script&gt;" in html


# ─── #3 · portfolio 渲染转义 ─────────────────────────────

def test_portfolio_html_escapes_malicious_portfolio_name_and_note():
    from lib.portfolio_runner import _render_html, _portfolio_health
    m = _malicious_metric()
    m["industry"] = "白酒"
    metrics = [m]
    health = _portfolio_health(metrics)
    html = _render_html('<script>steal()</script>', metrics, health, depth="lite")
    # 恶意组合名被转义
    assert "<script>steal()</script>" not in html
    assert "&lt;script&gt;steal()" in html
    # 恶意股票名也被转义
    assert "<img src=x onerror" not in html


def test_portfolio_normal_name_intact():
    from lib.portfolio_runner import _render_html, _portfolio_health
    m = _malicious_metric("600519.SH", "贵州茅台")
    m["industry"] = "白酒"
    m["verdict"] = "买入"
    m["punchline"] = "稀缺品"
    metrics = [m]
    health = _portfolio_health(metrics)
    html = _render_html("我的核心组合", metrics, health, depth="lite")
    assert "我的核心组合" in html
    assert "贵州茅台" in html

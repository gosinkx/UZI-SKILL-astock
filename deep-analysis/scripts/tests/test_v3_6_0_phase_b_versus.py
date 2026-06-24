"""Regression for v3.6.0 Phase B · 多股横向对比 (--versus).

测试覆盖：
1. versus_runner._extract_metrics 正确从 syn/raw/panel 抽取核心字段
2. _winner 高低对比逻辑正确
3. _render_comparison_grid 渲染 12 行指标 · 高亮 winner
4. _render_html 单 HTML 自包含（含 main 模板 style + dark-toggle）
5. run_versus 输入校验 (< 2 / > 4 报错)
6. CLI --versus argparse 完整
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


# ─── #1 · _winner 高低对比 ────────────────────────────────

def test_winner_higher_is_better():
    from lib.versus_runner import _winner
    # ROE 越高越好 · index 0 (42) 赢
    assert _winner([42.0, 8.5, 13.2], higher_is_better=True) == 0


def test_winner_lower_is_better():
    from lib.versus_runner import _winner
    # PE 越低越好 · index 1 (15) 赢
    assert _winner([45.0, 15.0, 28.0], higher_is_better=False) == 1


def test_winner_all_none_returns_minus_one():
    from lib.versus_runner import _winner
    assert _winner([None, None], higher_is_better=True) == -1


def test_winner_skips_zero():
    """0 通常是数据缺失 · 不应当作 winner."""
    from lib.versus_runner import _winner
    assert _winner([0.0, 12.5, 0.0], higher_is_better=True) == 1


# ─── #2 · _extract_metrics ────────────────────────────────

def _fake_bundle(ticker="600519.SH", roe=42.0, pe=28.0, score=85.0, name="贵州茅台"):
    return {
        "ticker": ticker,
        "syn": {
            "name": name,
            "overall_score": score,
            "fundamental_score": score - 5,
            "panel_consensus": 78.0,
            "verdict_label": "买入",
            "verdict_detail": "基本面 +2 · 共识 +3",
            "debate": {"punchline": "ROE 42% 配 PE 28x 是合理的稀缺品"},
            "school_lock": None,
        },
        "raw": {
            "dimensions": {
                "0_basic": {"data": {"name": name, "industry": "白酒", "price": 1850.0,
                                     "market_cap_yi": 23000, "pe_ttm": pe, "pb": 8.5}},
                "1_financials": {"data": {"roe": roe, "net_margin": 52.6, "gross_margin": 91.5,
                                          "rev_growth_3y": 12.3}},
                "10_valuation": {"data": {}},
                "18_trap": {"data": {"trap_level": "🟢 安全"}},
            }
        },
        "panel": {
            "signal_distribution": {"bullish": 28, "bearish": 4, "neutral": 15, "skip": 4},
            "panel_consensus": 78.0,
        },
    }


def test_extract_metrics_full_fields():
    from lib.versus_runner import _extract_metrics
    m = _extract_metrics(_fake_bundle())
    assert m["ticker"] == "600519.SH"
    assert m["name"] == "贵州茅台"
    assert m["industry"] == "白酒"
    assert m["roe"] == 42.0
    assert m["pe_ttm"] == 28.0
    assert m["overall_score"] == 85.0
    assert m["bull_count"] == 28
    assert m["bear_count"] == 4
    assert "ROE 42%" in m["punchline"]


def test_extract_metrics_missing_dims_returns_none():
    from lib.versus_runner import _extract_metrics
    sparse = {"ticker": "X", "syn": {}, "raw": {"dimensions": {}}, "panel": {}}
    m = _extract_metrics(sparse)
    assert m["ticker"] == "X"
    assert m["roe"] is None
    assert m["pe_ttm"] is None
    # 不崩 · 全 None ok
    assert m["overall_score"] is None


# ─── #3 · 渲染 ────────────────────────────────────────────

def test_render_comparison_grid_highlights_winner():
    from lib.versus_runner import _extract_metrics, _render_comparison_grid
    m1 = _extract_metrics(_fake_bundle("600519.SH", roe=42, pe=28, score=85, name="茅台"))
    m2 = _extract_metrics(_fake_bundle("000858.SZ", roe=24, pe=22, score=72, name="五粮液"))
    grid = _render_comparison_grid([m1, m2])
    assert "ROE %" in grid
    assert "PE TTM" in grid
    assert "茅台" in grid
    assert "五粮液" in grid
    # winner badge 必须出现
    assert "★ WIN" in grid


def test_render_html_self_contained_with_main_styles():
    from lib.versus_runner import _extract_metrics, _render_html
    m1 = _extract_metrics(_fake_bundle("600519.SH", name="茅台"))
    m2 = _extract_metrics(_fake_bundle("000858.SZ", roe=24, pe=22, score=72, name="五粮液"))
    html = _render_html([m1, m2], depth="lite")
    # 自包含 · main 模板的 :root 必须在
    assert ":root" in html
    assert "[data-theme=\"dark\"]" in html
    # versus 自己的 hero block
    assert "茅台 VS 五粮液" in html
    # toggle 必须在
    assert "theme-toggle" in html
    # 单文件不依赖外部 CSS（除模板内嵌的）
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_render_html_two_three_four_stocks():
    """支持 2/3/4 只 · 表格列宽自动适配."""
    from lib.versus_runner import _extract_metrics, _render_html
    metrics = [
        _extract_metrics(_fake_bundle(f"00{i}001.SZ", name=f"票{i}", score=70 + i * 3))
        for i in range(4)
    ]
    for n in (2, 3, 4):
        html = _render_html(metrics[:n], depth="lite")
        assert html.count("票0") >= 1 if n >= 1 else True
        # 列宽 col_pct 应是 100/(n+1)
        col_pct = f"{100 / (n + 1):.2f}%"
        assert col_pct in html


# ─── #4 · run_versus 输入校验 ─────────────────────────────

def test_run_versus_rejects_too_few():
    from lib.versus_runner import run_versus
    result = run_versus(["600519.SH"], depth="lite", auto_open=False)
    assert result["status"] == "invalid_input"
    assert "2-4" in result["message"]


def test_run_versus_rejects_too_many():
    from lib.versus_runner import run_versus
    result = run_versus(["A", "B", "C", "D", "E"], depth="lite", auto_open=False)
    assert result["status"] == "invalid_input"


# ─── #5 · CLI argparse ────────────────────────────────────

def test_run_py_has_versus_argument():
    run_py = (Path(__file__).resolve().parents[4] / "run.py").read_text(encoding="utf-8")
    assert '"--versus"' in run_py
    assert 'nargs="+"' in run_py
    # 必须 import versus_runner
    assert "from lib.versus_runner import run_versus" in run_py

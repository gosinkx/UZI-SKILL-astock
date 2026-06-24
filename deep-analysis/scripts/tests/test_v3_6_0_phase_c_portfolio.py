"""Regression for v3.6.0 Phase C · 组合批量分析 (--portfolio).

测试覆盖：
1. CSV parser 容错：header / no-header / 中英文列名 / 0-1 vs 0-100 权重
2. weight 归一化：缺失 → 平均 · 部分缺 → 剩余均分 · 全有 → 归一化
3. _portfolio_health 加权评分 + 健康度判定
4. _render_html 自包含 + dark mode + KPI 网格
5. CSV 不存在报错
6. CLI --portfolio argparse 完整
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


# ─── #1 · CSV parser ──────────────────────────────────────

def _write_csv(content: str) -> Path:
    tmp = Path(tempfile.mktemp(suffix=".csv"))
    tmp.write_text(content, encoding="utf-8")
    return tmp


def test_parse_csv_with_header():
    from lib.portfolio_runner import _parse_csv
    csv_path = _write_csv(
        "ticker,weight,note\n"
        "600519.SH,0.30,白酒龙头\n"
        "000858.SZ,0.15,白酒第二\n"
    )
    rows = _parse_csv(csv_path)
    assert len(rows) == 2
    assert rows[0]["ticker"] == "600519.SH"
    assert rows[0]["weight"] == 0.30
    assert rows[0]["note"] == "白酒龙头"


def test_parse_csv_chinese_headers():
    from lib.portfolio_runner import _parse_csv
    csv_path = _write_csv(
        "代码,权重,备注\n"
        "贵州茅台,30,白酒\n"
        "五粮液,20,白酒\n"
    )
    rows = _parse_csv(csv_path)
    assert len(rows) == 2
    # 30 应自动判为 30% → 0.30
    assert rows[0]["weight"] == 0.30
    assert rows[0]["note"] == "白酒"


def test_parse_csv_no_header_single_column():
    from lib.portfolio_runner import _parse_csv
    csv_path = _write_csv("600519.SH\n000858.SZ\n002594.SZ\n")
    rows = _parse_csv(csv_path)
    assert len(rows) == 3
    assert all(r["weight"] is None for r in rows)


def test_parse_csv_raises_for_missing_file():
    from lib.portfolio_runner import _parse_csv
    try:
        _parse_csv(Path("/tmp/__does_not_exist_v360.csv"))
        raise AssertionError("应该抛 FileNotFoundError")
    except FileNotFoundError:
        pass


# ─── #2 · weight 归一化 ───────────────────────────────────

def test_normalize_all_weights_present():
    from lib.portfolio_runner import _normalize_weights
    rows = [
        {"ticker": "A", "weight": 0.5},
        {"ticker": "B", "weight": 0.3},
        {"ticker": "C", "weight": 0.2},
    ]
    out = _normalize_weights(rows)
    assert abs(sum(r["weight"] for r in out) - 1.0) < 1e-6


def test_normalize_partial_weights():
    """50% A + B/C 缺 · 剩 50% 均分给 B/C 各 25%."""
    from lib.portfolio_runner import _normalize_weights
    rows = [
        {"ticker": "A", "weight": 0.5},
        {"ticker": "B", "weight": None},
        {"ticker": "C", "weight": None},
    ]
    out = _normalize_weights(rows)
    assert abs(sum(r["weight"] for r in out) - 1.0) < 1e-6
    # A 应仍是约 0.5 · B/C 各约 0.25
    assert 0.45 < out[0]["weight"] < 0.55


def test_normalize_all_missing_average():
    from lib.portfolio_runner import _normalize_weights
    rows = [{"ticker": f"T{i}", "weight": None} for i in range(4)]
    out = _normalize_weights(rows)
    assert all(abs(r["weight"] - 0.25) < 1e-6 for r in out)


def test_normalize_oversum_renormalized():
    """sum > 1 也归一化 · 不报错."""
    from lib.portfolio_runner import _normalize_weights
    rows = [{"ticker": "A", "weight": 0.8}, {"ticker": "B", "weight": 0.6}]
    out = _normalize_weights(rows)
    assert abs(sum(r["weight"] for r in out) - 1.0) < 1e-6


# ─── #3 · portfolio_health ────────────────────────────────

def _fake_metric(ticker, score, industry="白酒", weight=0.25):
    return {
        "ticker": ticker, "name": ticker, "industry": industry,
        "overall_score": score, "verdict": "买入",
        "bull_count": 20, "bear_count": 5, "neutral_count": 10, "skip_count": 16,
        "_weight": weight,
    }


def test_health_green_with_high_score_low_concentration():
    from lib.portfolio_runner import _portfolio_health
    metrics = [
        _fake_metric("A", 85, "白酒", 0.25),
        _fake_metric("B", 75, "电动车", 0.25),
        _fake_metric("C", 80, "半导体", 0.25),
        _fake_metric("D", 70, "光通信", 0.25),
    ]
    h = _portfolio_health(metrics)
    assert h["weighted_score"] == 77.5
    assert h["n_industries"] == 4
    assert "🟢" in h["verdict"]


def test_health_red_when_concentrated():
    from lib.portfolio_runner import _portfolio_health
    metrics = [
        _fake_metric("A", 45, "白酒", 0.60),  # 60% 集中度
        _fake_metric("B", 50, "白酒", 0.40),  # 同行业
    ]
    h = _portfolio_health(metrics)
    assert h["weighted_score"] == 47.0
    assert h["n_industries"] == 1
    assert "🔴" in h["verdict"]


def test_health_handles_all_invalid():
    from lib.portfolio_runner import _portfolio_health
    h = _portfolio_health([{"overall_score": None, "_weight": 1.0}])
    assert h["weighted_score"] == 0
    assert "数据不足" in h["verdict"]


# ─── #4 · 渲染 ────────────────────────────────────────────

def test_render_html_self_contained():
    from lib.portfolio_runner import _render_html, _portfolio_health
    metrics = [
        _fake_metric("600519.SH", 85, "白酒", 0.50),
        _fake_metric("002594.SZ", 70, "电动车", 0.50),
    ]
    for m in metrics:
        m["name"] = "茅台" if "600519" in m["ticker"] else "比亚迪"
    h = _portfolio_health(metrics)
    html = _render_html("我的核心组合", metrics, h, depth="lite")
    assert ":root" in html  # 主模板 CSS
    assert "[data-theme=\"dark\"]" in html
    assert "我的核心组合" in html
    assert "加权评分" in html
    assert "比亚迪" in html
    assert "theme-toggle" in html
    assert html.startswith("<!DOCTYPE html>")


# ─── #5 · CLI argparse ────────────────────────────────────

def test_run_py_has_portfolio_argument():
    run_py = (Path(__file__).resolve().parents[4] / "run.py").read_text(encoding="utf-8")
    assert '"--portfolio"' in run_py
    assert "from lib.portfolio_runner import run_portfolio" in run_py

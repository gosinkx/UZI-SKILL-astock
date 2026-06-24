"""Regression for v3.4.0 · ETF/LOF 持仓循环分析 + 二次确认.

设计来自用户反馈：
"基金和 etf 很简单 · 你就搜索这个基金的持仓分析就行了 ·
但是在使用前要提醒用户因为要搜索十个股票 · 可能时间和消耗会变大 · 需要他二次确认"
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


def _fake_holdings(n: int = 10) -> list[dict]:
    """构造 fake top holdings."""
    return [
        {"rank": i, "code": f"6005{19+i:02d}", "name": f"股票{i}",
         "weight_pct": round(10 - i * 0.5, 2)}
        for i in range(1, n + 1)
    ]


def test_runner_estimate_runtime():
    from lib.fund_holdings_runner import _estimate_runtime
    # lite 60s/股 × 10 = 600s = 10 分钟
    assert "10 分钟" in _estimate_runtime(10, "lite")
    # medium 240s × 5 = 1200s = 20 分钟
    assert "20 分钟" in _estimate_runtime(5, "medium")
    # deep 900s × 3 = 2700s = 45 分钟
    assert "45 分钟" in _estimate_runtime(3, "deep")


def test_runner_no_holdings_returns_status():
    from lib.fund_holdings_runner import confirm_and_run_holdings
    r = confirm_and_run_holdings("510300.SH", "ETF", [], auto_yes=True)
    assert r["status"] == "no_holdings"


def test_runner_non_interactive_default_cancels():
    """非交互 + auto_yes=False → 应取消（agent 必须显式传 auto_yes）."""
    from lib.fund_holdings_runner import confirm_and_run_holdings
    r = confirm_and_run_holdings(
        "510300.SH", "ETF", _fake_holdings(3),
        auto_yes=False, interactive=False,
    )
    assert r["status"] == "cancelled"


def test_runner_auto_yes_runs_all(monkeypatch, tmp_path, capsys):
    """auto_yes=True 应跳过 prompt 跑全部持仓."""
    from lib.fund_holdings_runner import confirm_and_run_holdings

    fake_run = MagicMock(return_value=str(tmp_path / "fake-report.html"))
    (tmp_path / "fake-report.html").write_text("<html></html>", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    with patch("lib.pipeline.run.run_pipeline", fake_run):
        r = confirm_and_run_holdings(
            "510300.SH", "ETF", _fake_holdings(3),
            depth="lite", auto_yes=True,
        )

    assert r["status"] == "completed"
    assert len(r["analyzed"]) == 3
    assert fake_run.call_count == 3
    # 验证 summary HTML 生成
    summary_p = Path(r["summary_html"])
    assert summary_p.exists()
    html = summary_p.read_text(encoding="utf-8")
    assert "ETF" in html and "510300.SH" in html
    assert "股票1" in html  # 持仓清单


def test_runner_partial_failure_still_completes(monkeypatch, tmp_path):
    """某个持仓分析失败时不应中断 · 其他继续 + summary 标失败."""
    from lib.fund_holdings_runner import confirm_and_run_holdings

    call_count = {"n": 0}

    def fake_run(code, resume=True):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise RuntimeError("simulated network error")
        report = tmp_path / f"{code}-report.html"
        report.write_text("<html></html>", encoding="utf-8")
        return str(report)

    monkeypatch.chdir(tmp_path)
    with patch("lib.pipeline.run.run_pipeline", side_effect=fake_run):
        r = confirm_and_run_holdings(
            "510300.SH", "ETF", _fake_holdings(3),
            depth="lite", auto_yes=True,
        )

    assert r["status"] == "completed"
    assert len(r["analyzed"]) == 2
    assert len(r["failed"]) == 1
    assert call_count["n"] == 3  # 全跑了 · 失败那个也调过


def test_summary_html_contains_links(monkeypatch, tmp_path):
    """生成的 summary HTML 必须含到子报告的 <a href> 链接."""
    from lib.fund_holdings_runner import confirm_and_run_holdings

    monkeypatch.chdir(tmp_path)
    fake_path = tmp_path / "subdir" / "stock-report.html"
    fake_path.parent.mkdir(parents=True)
    fake_path.write_text("<html></html>", encoding="utf-8")

    with patch("lib.pipeline.run.run_pipeline", return_value=str(fake_path)):
        r = confirm_and_run_holdings(
            "510300.SH", "ETF", _fake_holdings(2),
            depth="lite", auto_yes=True,
        )

    html = Path(r["summary_html"]).read_text(encoding="utf-8")
    assert 'href=' in html
    assert 'target="_blank"' in html


def test_runner_default_path_handled():
    """preflight_helpers.prepare_target ETF 路径应返 security_type='etf' + top_holdings."""
    src = (SCRIPTS / "lib" / "pipeline" / "preflight_helpers.py").read_text(encoding="utf-8")
    # ETF 路径必须返 status=non_stock_security · security_type=etf · top_holdings
    assert '"status": "non_stock_security"' in src
    assert '"security_type": sec_type' in src
    assert "top_holdings" in src

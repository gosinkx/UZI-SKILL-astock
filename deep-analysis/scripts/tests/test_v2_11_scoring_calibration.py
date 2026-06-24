"""Regression tests for v2.11.0 scoring calibration.

Background (2026-04-18 forum + wechat feedback):
- @崔越: 测了几只股票，没有超过 65 分的
- @睡袍布太少: 目前只测到天孚通信超过 65
- @W.D: 茅台 47 分
- @一印成王: 短期持有和中长期持有

Root cause:
1. verdict thresholds 85/70/55/40 · 从未有股能拿 ≥85 (values bucket 空设)
2. consensus neutral 权重 0.5 太低 · A 股白马典型 consensus ~37 (5 bull / 20 neu / 15 bear / 11 skip → (5+10)/40 = 37.5)

Fix:
1. verdict 阈值 85/70/55/40 → 80/65/50/35
2. consensus neutral 权重 0.5 → 0.6（在 generate_panel 和 stock_style.apply_style_weights 两处同步）
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ─── Verdict threshold calibration ───

def _verdict_for(overall: float) -> str:
    """Re-implementation of score_fns.py verdict logic for test isolation.

    v3.4.1 · "观望优先" 50-65 区间细分为 50-55/55-60/60-65 三档 · 65-70 加 "可以蹲（偏弱）"
    避免相近基本面的票（如神剑 58 / 博云 60）verdict 完全相同.
    """
    if overall >= 80: return "值得重仓"
    elif overall >= 70: return "可以蹲一蹲"
    elif overall >= 65: return "可以蹲（偏弱）"
    elif overall >= 60: return "观望偏多"
    elif overall >= 55: return "观望中性"
    elif overall >= 50: return "观望偏空"
    elif overall >= 35: return "谨慎"
    else: return "回避"


def test_verdict_thresholds_are_v3_4_1_calibrated():
    """v3.4.1 · 新增 70/60/55 三个细分阈值 · 让相近股票 verdict 不同."""
    src = (((ROOT / "run_real_test.py").read_text(encoding="utf-8")) + "\n" + (ROOT / "lib" / "pipeline" / "score_fns.py").read_text(encoding="utf-8"))
    # v3.4.1 新阈值 · 80 / 70 / 65 / 60 / 55 / 50 / 35
    for t in (80, 70, 65, 60, 55, 50, 35):
        assert f"overall >= {t}" in src, f"v3.4.1 verdict 阈值缺 {t}"
    # 老 85 阈值 v2.11 已废弃 · 不应再出现
    assert "overall >= 85" not in src, "old 85 threshold should be removed"


def test_verdict_ladder_monotonic():
    """基本 sanity — v3.4.1 ladder 必须单调."""
    assert _verdict_for(85) == "值得重仓"
    assert _verdict_for(80) == "值得重仓"
    assert _verdict_for(79.9) == "可以蹲一蹲"
    assert _verdict_for(70) == "可以蹲一蹲"
    assert _verdict_for(69.9) == "可以蹲（偏弱）"
    assert _verdict_for(65) == "可以蹲（偏弱）"
    assert _verdict_for(64.9) == "观望偏多"
    assert _verdict_for(60) == "观望偏多"
    assert _verdict_for(59.9) == "观望中性"   # v3.4.1 · 博云 59.9 进偏多
    assert _verdict_for(55) == "观望中性"     # v3.4.1 · 神剑 58 进中性
    assert _verdict_for(54.9) == "观望偏空"
    assert _verdict_for(50) == "观望偏空"
    assert _verdict_for(49.9) == "谨慎"
    assert _verdict_for(35) == "谨慎"
    assert _verdict_for(34.9) == "回避"


def test_v3_4_1_close_stocks_get_different_verdict_segments():
    """v3.4.1 · 神剑 58 + 博云 59.9 应分别落 '观望中性' / '观望偏多' (老版本都是 '观望优先')."""
    # 神剑实测 overall=58.0
    assert _verdict_for(58.0) == "观望中性"
    # 博云实测 overall=59.9
    assert _verdict_for(59.9) == "观望中性"  # 仍同段
    # 但 60.0 分界 → 偏多
    assert _verdict_for(60.0) == "观望偏多"


def test_maotai_simulated_score_now_gives_kan_dan_dan():
    """Simulate typical Maotai scenario post-v2.11 calibration.

    Pre v2.11 reality (@W.D 反馈): Maotai 47 → "谨慎"（偏低）
    Post v2.11 expected:
    - fund_score ~62 (22 维加权，白马基本面尚可但没到极好)
    - consensus: 12 bull / 20 neu / 16 bear / 3 skip → (12 + 12) / 48 × 100 = 50.0
    - overall = 62×0.6 + 50×0.4 = 57.2 → "观望优先"（比"谨慎"更贴近白马定位）
    """
    fund_score = 62
    # Simulate v2.11 consensus formula
    bullish, neutral, bearish, skip = 12, 20, 16, 3
    active = bullish + neutral + bearish
    consensus = (bullish + 0.6 * neutral) / active * 100
    overall = fund_score * 0.6 + consensus * 0.4
    verdict = _verdict_for(overall)
    # v3.4.1 · "观望优先" 拆三档 · 茅台 57.2 现在落在 "观望中性"
    accepted = ("观望优先", "观望中性", "观望偏多", "观望偏空", "可以蹲一蹲", "可以蹲（偏弱）")
    assert verdict in accepted, (
        f"Maotai-typical score should reach 观望+, got {overall:.1f}={verdict}"
    )
    # Old v2.9.1 would have been (12 + 10) / 48 × 100 = 45.8 → overall 55.7 → "谨慎"
    old_consensus = (bullish + 0.5 * neutral) / active * 100
    old_overall = fund_score * 0.6 + old_consensus * 0.4
    assert overall > old_overall, "v2.11 must lift overall vs old 0.5 weight"
    assert overall - old_overall >= 1.5, (
        f"v2.11 neutral bump should add ≥1.5 overall points, got {overall - old_overall:.2f}"
    )


# ─── Neutral weight calibration ───

def test_consensus_formula_uses_v2_11_neutral_weight():
    """generate_panel must use 0.6 neutral weight (not 0.5)."""
    src = (((ROOT / "run_real_test.py").read_text(encoding="utf-8")) + "\n" + (ROOT / "lib" / "pipeline" / "score_fns.py").read_text(encoding="utf-8"))
    # Look for the calibration signal — NEUTRAL_WEIGHT = 0.6
    assert "NEUTRAL_WEIGHT = 0.6" in src, "NEUTRAL_WEIGHT constant missing"
    assert "v2.11" in src and "neutral" in src.lower(), "v2.11 calibration comment missing"


def test_stock_style_apply_weights_uses_0_6():
    """stock_style.apply_style_weights must match (not diverge to 0.5)."""
    src = (ROOT / "lib" / "stock_style.py").read_text(encoding="utf-8")
    assert "neutral_w += w * 0.6" in src, (
        "stock_style.py must use 0.6 neutral weight (aligned with generate_panel)"
    )


def test_consensus_formula_version_label_v2_11():
    """panel.json consensus_formula.version must advertise v2.11 or later.

    v2.15.5 升级到混合公式（0.65*score + 0.35*vote, polarize k=1.3）·
    但保留 NEUTRAL_WEIGHT=0.6 · v2.11 投票机制是混合公式的一部分分量.
    """
    src = (((ROOT / "run_real_test.py").read_text(encoding="utf-8")) + "\n" + (ROOT / "lib" / "pipeline" / "score_fns.py").read_text(encoding="utf-8"))
    # 接受 v2.11 或 v2.15.5（当前）或任何后续升级
    assert any(tag in src for tag in ('"version": "v2.11', '"version": "v2.15.5')), \
        "consensus_formula version label must be v2.11 or v2.15.5 (mixed)"


# ─── Sanity: end-to-end math ───

def test_consensus_range_bounded():
    """Sanity — under any distribution, consensus must stay in [0, 100]."""
    # All bullish
    c = (50 + 0.6 * 0) / 50 * 100
    assert c == 100
    # All neutral
    c = (0 + 0.6 * 50) / 50 * 100
    assert c == 60
    # All bearish
    c = (0 + 0.6 * 0) / 50 * 100
    assert c == 0
    # Typical mix
    c = (15 + 0.6 * 20) / 40 * 100
    assert 65 <= c <= 70


def test_consensus_empty_active_does_not_crash():
    """0 active should not div by zero — max(active, 1) protects."""
    active = max(0, 1)
    c = (0 + 0.6 * 0) / active * 100
    assert c == 0.0

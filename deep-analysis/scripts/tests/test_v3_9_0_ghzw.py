"""Regression for v3.9.0 · 股海贼王 (ghzw) · 淘股吧十年实盘蒸馏评委.

数据源 (docs/ghzw-dossier.md)：
  8951 笔交割单 (2016-02 → 2026-06 · 33 万 → 3131 万) + 5069 条发言。
  持仓中位 1 天 · 同时持仓 3-5 只 · 第一重仓中位 51% · 2010 只票题材轮动。

测试覆盖：
1. 注册完整（v3.8.1 体检 checklist 全项：db/rules/scope/personas/profile/avatar）
2. 行为复刻：妖股(主线+涨停基因+低位) bullish · 白马 bearish · 美股 skip
3. 台词渲染 · 三 signal 各有台词
4. dossier 文档存在且含核心统计
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
REPO = SCRIPTS.parents[2]
sys.path.insert(0, str(SCRIPTS))


# ─── #1 · 注册完整性（按 v3.8.1 加评委 checklist）─────────

def test_ghzw_in_db_f_group_flagship():
    from lib.investor_db import by_id, INVESTORS
    inv = by_id("ghzw")
    assert inv is not None, "investor_db 缺 ghzw"
    assert inv["group"] == "F"
    assert inv["tier"] == "flagship"  # 有完整真实数据 · flagship 级
    assert len(INVESTORS) == 66


def test_ghzw_rules_registered_data_driven():
    from lib.investor_criteria import INVESTOR_RULES
    rules = INVESTOR_RULES.get("ghzw", [])
    assert len(rules) >= 5, f"ghzw 仅 {len(rules)} 条规则"
    names = [r.name for r in rules]
    # 核心打法必须覆盖：主线 / 涨停基因 / 盘口 / 格局票
    assert any("主线" in n for n in names)
    assert any("涨停" in n or "龙虎" in n for n in names)
    assert any("盘口" in n or "Stage" in n for n in names)
    assert any("情绪载体" in n or "格局" in n for n in names)


def test_ghzw_scope_a_only():
    from lib.investor_knowledge import MARKET_SCOPE
    assert MARKET_SCOPE.get("ghzw") == "A", "接力/打板只在 A 股 T+1 生态有效"


def test_ghzw_personas_and_profile():
    from lib.investor_personas import PERSONAS, get_comment
    from lib.investor_profile import get_profile
    assert "ghzw" in PERSONAS
    for sig in ("bullish", "bearish", "neutral"):
        assert PERSONAS["ghzw"].get(sig), f"ghzw 缺 {sig} 台词"
    line = get_comment("ghzw", "bullish", {"name": "鸿博股份", "industry": "AI 算力"})
    assert line and "{name}" not in line
    p = get_profile("ghzw", "F")
    assert "超短接力" in p["time_horizon"]  # 数据：持仓中位 1 天
    assert "—" not in p["time_horizon"]


def test_ghzw_avatar_exists():
    assert (SCRIPTS.parent / "assets" / "avatars" / "ghzw.svg").is_file()


# ─── #2 · 行为复刻（来自其真实交易模式）──────────────────

def _hot_theme_stock():
    """鸿博股份式妖股 (他 2023 年真做过 22 次)：主线 AI + 涨停基因 + 低位 + Stage2."""
    return {"market": "A", "ticker": "002229.SZ", "name": "鸿博股份",
            "industry": "AI 算力租赁", "market_cap_yi": 120,
            "has_positive_catalyst": True, "sentiment_heat": 85,
            "lhb_30d_count": 4, "stage_num": 2,
            "pct_from_year_high": -35, "vol_amplified": True}


def test_ghzw_bullish_on_mainline_limit_up_stock():
    from lib.investor_evaluator import evaluate
    r = evaluate("ghzw", _hot_theme_stock())
    assert r["signal"] == "bullish", f"主线妖股应 bullish · 实际 {r['signal']}"
    assert r["score"] >= 80


def test_ghzw_bearish_on_white_horse():
    """茅台式白马：无涨停基因/不在题材主线 → 他不碰（'逆主线=送钱'）."""
    from lib.investor_evaluator import evaluate
    f = {"market": "A", "ticker": "600519.SH", "name": "贵州茅台", "industry": "白酒",
         "market_cap_yi": 23000, "has_positive_catalyst": False, "sentiment_heat": 45,
         "lhb_30d_count": 0, "stage_num": 1, "pct_from_year_high": -10}
    r = evaluate("ghzw", f)
    assert r["signal"] == "bearish", f"白马应 bearish · 实际 {r['signal']}"


def test_ghzw_skips_us_market():
    from lib.investor_evaluator import evaluate
    r = evaluate("ghzw", {"market": "US", "ticker": "NVDA", "name": "NVIDIA",
                          "industry": "AI"})
    assert r["signal"] == "skip"


def test_ghzw_no_seat_range_false_skip():
    """ghzw 是网名非龙虎榜席位 · 不在 SEATS · 不应被射程检查误 skip
    (大众交通百亿大票他真做过 46 次 · 格局票模式)."""
    from lib.investor_evaluator import _is_youzi_out_of_range
    out, _ = _is_youzi_out_of_range("ghzw", {"market_cap_yi": 500})
    assert out is False, "不在 SEATS 的 F 组评委不应被射程 skip"


# ─── #3 · dossier 文档 ───────────────────────────────────

def test_ghzw_dossier_exists_with_core_stats():
    doc = (REPO / "docs" / "ghzw-dossier.md").read_text(encoding="utf-8")
    # 核心统计必须在档案里 (数据可溯源)
    for key in ("8951", "5069", "中位 1 天", "2010 只", "复盘三问", "不要跟票"):
        assert key in doc, f"dossier 缺核心内容: {key}"

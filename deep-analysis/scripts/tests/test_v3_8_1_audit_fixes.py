"""Regression for v3.8.1 · skills 全面体检修复.

体检发现 v3.6.3/v3.7.0 加 H/I 两组 14 位评委时 · 多处配套层漏更新：
1. 14 评委缺头像 SVG → 报告评委席/群聊破图
2. special_cards.render_school_scores order 缺 H/I → 两派分数永远不渲染
3. panel_cards/special_cards GROUP_LABELS 缺 H/I → 显示裸字母
4. investor_profile.GROUP_DEFAULT 缺 H/I → profile 落 GENERIC_FALLBACK 全 "—"
5. stock_style.STYLE_GROUP_WEIGHTS 缺 H/I → 风格加权失效 (默认 1.0)
6. 13 新评委缺 MARKET_SCOPE 显式登记 + PERSONAS 台词
7. SKILL.md/commands ~31 处 51/52 评委过时引用

本文件守护以上全部修复。
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
REPO = SCRIPTS.parents[2]
sys.path.insert(0, str(SCRIPTS))

NEW_IDS = ["andreessen", "gurley", "naval", "gerstner", "chamath",
           "burry", "chanos", "zhang_lei", "asness",
           "jensen_huang", "musk", "altman", "saylor"]


# ─── #1 · 全员头像 ───────────────────────────────────────

def test_all_65_investors_have_avatars():
    from lib.investor_db import INVESTORS
    avatars = SCRIPTS.parent / "assets" / "avatars"
    missing = [i["id"] for i in INVESTORS if not (avatars / f"{i['id']}.svg").is_file()]
    assert not missing, f"缺头像 → 报告破图: {missing}"


# ─── #2 · school_scores 渲染含 H/I ───────────────────────

def test_render_school_scores_includes_h_and_i():
    from lib.report.special_cards import render_school_scores
    school = {g: {"label": f"{g}派", "consensus": 60, "avg_score": 60, "verdict": "关注",
                  "n_members": 3, "n_active": 3, "bullish": 1, "neutral": 1, "bearish": 1,
                  "skip": 0, "desc": "x", "dominant_signal": "neutral"}
              for g in "ABCDEFGHI"}
    html = render_school_scores({"school_scores": school}, {})
    assert "H派" in html, "H 组 (科技领袖派) 没渲染 · order 漏 H"
    assert "I派" in html, "I 组 (Serenity) 没渲染 · order 漏 I"


# ─── #3 · GROUP_LABELS 含 H/I ────────────────────────────

def test_panel_cards_group_labels_have_h_i():
    from lib.report.panel_cards import GROUP_LABELS
    assert "H" in GROUP_LABELS and "I" in GROUP_LABELS, "panel_cards 缺 H/I 标签 → 显示裸字母"


# ─── #4 · GROUP_DEFAULT profile 含 H/I ───────────────────

def test_group_default_profile_has_h_i():
    from lib.investor_profile import GROUP_DEFAULT, get_profile
    assert "H" in GROUP_DEFAULT and "I" in GROUP_DEFAULT
    # H 组无个人档案的评委不再落 "—"
    p = get_profile("jensen_huang", "H")
    assert p["time_horizon"] != "—", "H 组 profile 落到 GENERIC_FALLBACK"


# ─── #5 · 风格加权矩阵含 H/I ─────────────────────────────

def test_style_group_weights_have_h_i():
    from lib.stock_style import STYLE_GROUP_WEIGHTS
    for style, weights in STYLE_GROUP_WEIGHTS.items():
        assert "H" in weights and "I" in weights, f"风格 {style} 缺 H/I 权重"
    # 语义抽查：Serenity (I) 在红利防御股上应被大幅降权 · 在科技成长股上拉满
    from lib.stock_style import DIVIDEND_DEFENSE, GROWTH_TECH
    assert STYLE_GROUP_WEIGHTS[DIVIDEND_DEFENSE]["I"] < 0.5
    assert STYLE_GROUP_WEIGHTS[GROWTH_TECH]["I"] >= 1.3


# ─── #6 · MARKET_SCOPE + PERSONAS 全覆盖 ─────────────────

def test_all_new_investors_in_market_scope():
    from lib.investor_knowledge import MARKET_SCOPE
    missing = [i for i in NEW_IDS if i not in MARKET_SCOPE]
    assert not missing, f"MARKET_SCOPE 缺: {missing}"


def test_all_new_investors_have_persona_lines():
    from lib.investor_personas import PERSONAS
    missing = [i for i in NEW_IDS if i not in PERSONAS]
    assert not missing, f"PERSONAS 台词缺: {missing} (群聊会落 generic fallback)"
    # 每人三种 signal 至少各 1 条
    for i in NEW_IDS:
        for sig in ("bullish", "bearish", "neutral"):
            assert PERSONAS[i].get(sig), f"{i} 缺 {sig} 台词"


def test_persona_lines_render_with_placeholders():
    """台词模板含 {name}/{industry} · get_comment 渲染不崩."""
    from lib.investor_personas import get_comment
    for i in NEW_IDS:
        line = get_comment(i, "bullish", {"name": "测试股", "industry": "光模块"})
        assert line and "{name}" not in line, f"{i} 台词渲染失败: {line[:50]}"


# ─── #7 · 文档计数同步 ───────────────────────────────────

def test_skill_md_no_stale_counts():
    """SKILL.md / commands 不再有 51/52 评委这类过时计数."""
    import re
    for rel in ("skills/deep-analysis/SKILL.md", "skills/investor-panel/SKILL.md",
                "commands/analyze-stock.md", "commands/panel-only.md"):
        t = (REPO / rel).read_text(encoding="utf-8")
        # 注：'51 位投资者' 是合法表述（persona YAML 确实是 51 个）· 不算 stale
        stale = re.findall(r"5[012] 评委|5[02] 位投资|5[012] 位大佬|5[02] 人评", t)
        assert not stale, f"{rel} 仍有过时计数: {stale}"


def test_evaluate_all_covers_65():
    """evaluate_all 批量评估覆盖全部 65 人 (INVESTOR_RULES 全注册)."""
    from lib.investor_criteria import INVESTOR_RULES
    from lib.investor_db import INVESTORS
    assert len(INVESTOR_RULES) == len(INVESTORS) == 66  # v3.9.0 +ghzw

"""Regression for v3.3.3 · PR #54 + #59 hotfixes (社区贡献).

#54 · @DragonQuix · institutional.py 缺 svg_radar import
     根因：v3.2 拆分时 _render_competitive_analysis 的 Porter radar 用 svg_radar 但漏 import
     修法：lib/report/institutional.py 加 svg_radar 到 import block

#59 · @Charlson852 · special_cards.py Python 3.11 嵌套 f-string SyntaxError
     根因：f"{f'...\\\"...\\\"...' if skip else ''}" 在 Python 3.11 会报 SyntaxError
            (f-string expression part cannot include a backslash)
     修法：把 skip 部分提取为独立变量 skip_display · 再插入主 f-string
     注意：PR #59 原版还把 items.append 错误移出 for-loop · 我们只 cherry-pick 修复部分.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


# ─── #54 · svg_radar import in institutional.py ────────────────────

def test_institutional_imports_svg_radar():
    """institutional.py 必须 import svg_radar · 否则 _render_competitive_analysis NameError."""
    src = (SCRIPTS / "lib" / "report" / "institutional.py").read_text(encoding="utf-8")
    import_block_end = src.find("from lib.report.dim_viz import")
    assert import_block_end > 0
    import_block = src[:import_block_end]
    assert "svg_radar" in import_block, (
        "v3.3.3 regression: institutional.py 必须 import svg_radar"
        " · _render_competitive_analysis 的 Porter radar 调用 (PR #54)"
    )


def test_render_competitive_analysis_does_not_raise_nameerror():
    """实际跑 _render_competitive_analysis · Porter radar 路径不能 NameError."""
    from lib.report.institutional import _render_competitive_analysis
    dim22 = {
        "competitive_analysis": {
            "porter_five_forces": {
                "supplier_power": {"score": 3},
                "buyer_power": {"score": 2},
                "new_entrants_threat": {"score": 4},
                "substitutes_threat": {"score": 2},
                "rivalry_intensity": {"score": 3},
            },
            "bcg_position": {"category": "Star (明星)", "market_growth_pct": 25, "market_share_pct": 5},
            "industry_attractiveness_pct": 70,
        }
    }
    html = _render_competitive_analysis(dim22)
    assert "<svg" in html, "Porter radar 调用失败 · svg_radar 可能没 import"


# ─── #59 · Python 3.11 nested f-string fix ─────────────────────────

def test_school_scores_uses_skip_display_variable():
    """render_school_scores 应用 skip_display 变量提取 · 避免 f-string 嵌套反斜杠."""
    src = (SCRIPTS / "lib" / "report" / "special_cards.py").read_text(encoding="utf-8")
    idx = src.find("def render_school_scores(")
    assert idx > 0
    end = src.find("\ndef ", idx + 1)
    fn_src = src[idx:end if end > 0 else len(src)]
    assert "skip_display" in fn_src, "缺 skip_display 变量提取 (PR #59 Python 3.11 兼容修复)"


def test_render_school_scores_renders_all_seven_groups():
    """关键回归：items.append 必须在 for-loop 内 · 否则 7 流派只渲染 1 个 (PR #59 原版 bug)."""
    from lib.report.special_cards import render_school_scores
    fake = {"school_scores": {g: {
        "group": g, "label": f"流派{g}", "desc": f"desc-{g}",
        "consensus": 50.0, "avg_score": 50.0, "score_mean": 50.0,
        "vote_consensus": 50.0, "verdict": "关注",
        "n_members": 3, "n_active": 3,
        "bullish": 1, "neutral": 1, "bearish": 1, "skip": 0,
        "dominant_signal": "neutral",
    } for g in "ABCDEFG"}}
    html = render_school_scores(fake, {})
    for g in "ABCDEFG":
        assert f"流派{g}" in html, f"缺流派 {g} · items.append 可能被错移到 for-loop 外"


def test_render_school_scores_handles_skip_count():
    """skip > 0 时显示 —{skip} · skip == 0 时不显示."""
    from lib.report.special_cards import render_school_scores
    base = {
        "group": "F", "label": "游资", "desc": "...",
        "consensus": 40.0, "avg_score": 40.0, "score_mean": 40.0,
        "vote_consensus": 40.0, "verdict": "谨慎",
        "n_members": 23, "n_active": 20,
        "bullish": 5, "neutral": 10, "bearish": 5,
        "dominant_signal": "neutral",
    }
    html_with = render_school_scores({"school_scores": {"F": {**base, "skip": 3}}}, {})
    assert "—3" in html_with

    html_without = render_school_scores({"school_scores": {"F": {**base, "skip": 0}}}, {})
    assert "—0" not in html_without

"""Regression for v3.5.0 · 单一流派视角锁定.

用户需求：CLI 加 --school A/B/C/D/E/F/G 锁定单一流派评委 · 其他派自动 skip ·
报告顶部渲染 SCHOOL LOCK banner · agent role-play 也只覆盖该派.

测试覆盖：
1. evaluator.get_locked_school 正确解析 UZI_SCHOOL env
2. evaluator.evaluate 对非锁定派评委返 skip
3. evaluator.evaluate 对锁定派评委正常评分
4. _render_school_lock_banner 渲染 7 派各自配色
5. 未锁定时 banner 不渲染（不污染默认报告）
6. 流派标签映射完整 (7 派)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


# ─── #1 · get_locked_school 解析 env ─────────────────────

def test_locked_school_unset_returns_empty():
    from lib.investor_evaluator import get_locked_school
    os.environ.pop("UZI_SCHOOL", None)
    assert get_locked_school() == ""


def test_locked_school_lowercase_normalized():
    from lib.investor_evaluator import get_locked_school
    os.environ["UZI_SCHOOL"] = "f"
    try:
        assert get_locked_school() == "F"
    finally:
        os.environ.pop("UZI_SCHOOL", None)


def test_locked_school_invalid_ignored():
    """乱填的字母 · 不在 A-G 范围 · 当作未锁定."""
    from lib.investor_evaluator import get_locked_school
    os.environ["UZI_SCHOOL"] = "Z"
    try:
        assert get_locked_school() == ""
    finally:
        os.environ.pop("UZI_SCHOOL", None)


def test_school_labels_cover_seven_groups():
    from lib.investor_evaluator import SCHOOL_LABELS
    # v3.6.3 · I 组「AI 卡位/瓶颈猎手」(重磅角色 Serenity, 独立成组) · H 组为 v3.7.0 科技领袖派
    assert set(SCHOOL_LABELS.keys()) == {"A", "B", "C", "D", "E", "F", "G", "H", "I"}
    # 标签都是非空中文
    for k, v in SCHOOL_LABELS.items():
        assert v and isinstance(v, str), f"{k} 标签缺失"


# ─── #2 · evaluator skip 非锁定派 ────────────────────────

def test_evaluate_skips_non_locked_school():
    """锁定 F 派 · buffett (A 派) 应该 skip · 不进规则引擎."""
    from lib.investor_evaluator import evaluate
    os.environ["UZI_SCHOOL"] = "F"
    try:
        features = {"market": "A", "ticker": "300394.SZ", "name": "天孚通信",
                    "industry": "光器件", "market_cap_yi": 1500}
        result = evaluate("buffett", features)
        assert result["signal"] == "skip", "A 派评委在 F 锁定下应 skip"
        assert "锁定" in result.get("skip_reason", ""), "skip 理由必须说明是用户锁定"
        assert "F" in result.get("skip_reason", "") or "游资" in result.get("skip_reason", "")
    finally:
        os.environ.pop("UZI_SCHOOL", None)


def test_evaluate_no_lock_does_not_skip():
    """未锁定 · 评委照常评分 (不被 v3.5.0 误伤)."""
    from lib.investor_evaluator import evaluate
    os.environ.pop("UZI_SCHOOL", None)
    features = {"market": "A", "ticker": "300394.SZ", "name": "天孚通信",
                "industry": "光器件", "market_cap_yi": 1500, "roe": 42, "pe_ttm": 154}
    result = evaluate("buffett", features)
    # 不应因 school_lock 而 skip · 可能因其他原因 skip 但理由不能是"锁定"
    if result["signal"] == "skip":
        assert "锁定" not in result.get("skip_reason", "")


# ─── #3 · banner 渲染 ──────────────────────────────────────

def test_school_lock_banner_renders_when_locked():
    from lib.report.institutional import _render_school_lock_banner
    syn = {"school_lock": {"group": "F", "label": "A 股游资"}}
    html = _render_school_lock_banner(syn)
    assert "SCHOOL LOCK" in html
    assert "F · A 股游资" in html
    assert "赵老哥" in html  # F 派代表评委提示


def test_school_lock_banner_empty_when_no_lock():
    from lib.report.institutional import _render_school_lock_banner
    assert _render_school_lock_banner({}) == ""
    assert _render_school_lock_banner({"school_lock": None}) == ""
    assert _render_school_lock_banner(None) == ""


def test_school_lock_banner_each_school_has_theme():
    """7 派各自的 banner 必须有配色 + 代表评委提示 · 不能用默认灰."""
    from lib.report.institutional import _render_school_lock_banner
    for g, label in [("A", "价值派"), ("B", "成长派"), ("C", "宏观派"),
                     ("D", "技术派"), ("E", "中国价投"), ("F", "A 股游资"), ("G", "量化")]:
        html = _render_school_lock_banner({"school_lock": {"group": g, "label": label}})
        assert "SCHOOL LOCK" in html
        assert g in html and label in html
        assert "rgba(107,114,128" not in html, f"{g} 派用了默认灰 · 应单独配色"


def test_school_lock_banner_unknown_group_falls_back():
    """非 A-G 的 group · 应优雅降级 · 不崩."""
    from lib.report.institutional import _render_school_lock_banner
    html = _render_school_lock_banner({"school_lock": {"group": "X", "label": "实验派"}})
    assert "SCHOOL LOCK" in html
    assert "X" in html or "实验派" in html


# ─── #4 · run.py argparse ────────────────────────────────

def test_run_py_has_school_argument():
    """v3.5.0 · run.py argparse 必须含 --school choices=[A-G]."""
    run_py = (Path(__file__).resolve().parents[4] / "run.py").read_text(encoding="utf-8")
    assert '"--school"' in run_py
    # v3.7.0 起 choices 扩到 A-I (新增 H 科技领袖派 + I Serenity 卡位猎手)
    assert 'choices=["A", "B", "C", "D", "E", "F", "G", "H", "I"]' in run_py
    # 应设置 UZI_SCHOOL env · 让 evaluator 读取
    assert 'UZI_SCHOOL' in run_py

"""Regression for v3.9.1 · issue #79 · TOC 导航栏折叠/展开.

GitHub issue #79（QKioi）：HTML 报告左侧 sticky 导航栏会略微遮挡正文，
希望加一个按钮，点一下折叠起来，再点一下展开。

测试覆盖：
1. 折叠按钮 markup 存在（在 toc-rail 内 · 有 aria 标注）
2. 折叠态 CSS（.toc-rail.collapsed 隐藏 toc-item）
3. 折叠 JS 用 localStorage 持久化（key uzi-toc-collapsed）
4. 安全 · 折叠 JS 段不引入 innerHTML 赋值
"""
from __future__ import annotations

from pathlib import Path

TEMPLATE = (
    Path(__file__).resolve().parents[2] / "assets" / "report-template.html"
).read_text(encoding="utf-8")


# ─── #1 · 折叠按钮 markup ──────────────────────────────────
def test_toc_toggle_button_inside_rail():
    assert 'id="toc-toggle"' in TEMPLATE, "缺折叠按钮"
    assert 'class="toc-toggle"' in TEMPLATE
    # 按钮必须落在 toc-rail 内部
    rail_idx = TEMPLATE.find('id="toc-rail"')
    nav_end = TEMPLATE.find("</nav>", rail_idx)
    assert rail_idx != -1 and nav_end != -1
    assert 'id="toc-toggle"' in TEMPLATE[rail_idx:nav_end], "折叠按钮不在 toc-rail 内"


def test_toc_toggle_has_aria_and_title():
    idx = TEMPLATE.find('id="toc-toggle"')
    btn = TEMPLATE[idx - 80:idx + 200]
    assert "aria-expanded" in btn
    assert "aria-label" in btn
    assert "折叠" in btn or "展开" in btn


# ─── #2 · 折叠态 CSS ──────────────────────────────────────
def test_collapsed_css_hides_items():
    assert ".toc-rail.collapsed" in TEMPLATE, "缺 collapsed 态样式"
    idx = TEMPLATE.find(".toc-rail.collapsed .toc-item")
    assert idx != -1
    assert "display: none" in TEMPLATE[idx:idx + 60]


def test_toc_toggle_css_present():
    assert ".toc-rail .toc-toggle" in TEMPLATE
    assert "cursor: pointer" in TEMPLATE[TEMPLATE.find(".toc-rail .toc-toggle"):
                                         TEMPLATE.find(".toc-rail .toc-toggle") + 400]


# ─── #3 · 折叠状态持久化 ──────────────────────────────────
def test_toc_collapse_persists_localstorage():
    assert "uzi-toc-collapsed" in TEMPLATE, "缺 localStorage key"
    # 同时读取 + 写入
    assert "localStorage.getItem(TOC_KEY)" in TEMPLATE
    assert "localStorage.setItem(TOC_KEY" in TEMPLATE


def test_toc_toggle_click_toggles_collapsed_class():
    idx = TEMPLATE.find("uzi-toc-collapsed")
    block = TEMPLATE[idx:idx + 900]
    assert "addEventListener('click'" in block
    assert "classList.toggle('collapsed'" in block
    # 同步 aria-expanded
    assert "aria-expanded" in block


# ─── #4 · 安全 · 折叠逻辑不引入 innerHTML ─────────────────
def test_toc_collapse_block_no_innerhtml():
    idx = TEMPLATE.find("uzi-toc-collapsed")
    block = TEMPLATE[idx:idx + 900]
    assert ".innerHTML" not in block, "折叠逻辑禁止使用 innerHTML"

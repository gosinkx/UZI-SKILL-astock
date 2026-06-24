"""Regression for v3.6.0 Phase A · 视觉/交互升级.

测试覆盖：
1. Dark mode 主题 toggle 完整（CSS [data-theme] + button + JS toggle）
2. Sticky TOC rail 含 8 个章节 · 锚点 ID 全部存在
3. Count-up 动画 hint class 注入
4. Jargon tooltip · TERMS 字典 + 安全 DOM 构造（无 innerHTML 注入）
5. Share-QR canvas + URL 占位渲染
6. 安全 · script 段无 .innerHTML = 赋值（XSS 加固）
"""
from __future__ import annotations

from pathlib import Path

TEMPLATE = (
    Path(__file__).resolve().parents[2] / "assets" / "report-template.html"
).read_text(encoding="utf-8")


# ─── #1 · Dark mode ──────────────────────────────────────

def test_dark_theme_css_block_present():
    """[data-theme=\"dark\"] 必须重定义至少 10 个 CSS 变量."""
    assert '[data-theme="dark"]' in TEMPLATE
    dark_idx = TEMPLATE.find('[data-theme="dark"]')
    block = TEMPLATE[dark_idx:dark_idx + 2000]
    # 关键变量都得有
    for var in ["--bg-deep", "--bg-card", "--text-bright", "--text-main",
                "--bull-green", "--bear-red", "--neon-cyan", "--border"]:
        assert var in block, f"dark theme 缺 {var}"


def test_theme_toggle_button_in_topbar():
    assert 'id="theme-toggle"' in TEMPLATE
    assert "切换暗色" in TEMPLATE or "暗色" in TEMPLATE


def test_theme_toggle_js_persists_localstorage():
    """JS 必须把 theme 存到 localStorage · 跨刷新保留."""
    assert "uzi-theme" in TEMPLATE
    assert "localStorage.setItem" in TEMPLATE
    assert "prefers-color-scheme" in TEMPLATE


# ─── #2 · Sticky TOC ─────────────────────────────────────

def test_toc_rail_has_eight_sections():
    assert 'class="toc-rail"' in TEMPLATE
    sections = ["section-core", "section-clash", "section-jury", "section-chat",
                "section-scan", "section-modeling", "section-risks", "section-zones"]
    for sec in sections:
        assert f'href="#{sec}"' in TEMPLATE, f"TOC 缺 {sec} 链接"
        assert f'id="{sec}"' in TEMPLATE, f"模板缺 {sec} 锚点 ID"


def test_toc_scroll_spy_uses_intersection_observer():
    """IntersectionObserver · 高度兼容 · 不污染滚动性能."""
    assert "IntersectionObserver" in TEMPLATE
    assert ".toc-item" in TEMPLATE


def test_toc_responsive_hidden_below_1280():
    """TOC 在窄屏隐藏 · 不挡主内容."""
    assert "@media (max-width: 1280px)" in TEMPLATE
    # TOC display:none 在窄屏
    idx = TEMPLATE.find("@media (max-width: 1280px)")
    assert "toc-rail" in TEMPLATE[idx:idx + 200]


# ─── #3 · Count-up 动画 ───────────────────────────────────

def test_count_up_animation_present():
    assert ".count-up" in TEMPLATE
    assert "easeOut" in TEMPLATE or "ease-out" in TEMPLATE.lower()
    assert "requestAnimationFrame" in TEMPLATE


def test_count_up_targets_big_score_elements():
    """count-up 自动作用于大分数 · 不需要手工标记."""
    assert ".score-giant" in TEMPLATE or ".sc-score-giant" in TEMPLATE
    # selector 至少包含两类大数字
    assert "querySelectorAll" in TEMPLATE


# ─── #4 · Jargon tooltip + 安全 DOM ────────────────────

def test_jargon_terms_dict_covers_key_finance_jargon():
    """术语词典必须含 PE / PB / ROE / DCF 等核心金融术语."""
    for term in ["PE", "PB", "ROE", "DCF", "IRR", "WACC", "PEG"]:
        assert f"'{term}'" in TEMPLATE, f"TERMS dict 缺 {term}"


def test_jargon_css_styles_present():
    assert ".jargon" in TEMPLATE
    assert "data-tip" in TEMPLATE
    assert "cursor: help" in TEMPLATE or "cursor:help" in TEMPLATE


def test_tooltipify_uses_safe_dom_no_innerhtml():
    """v3.6.0 安全加固 · tooltipify 不能用 .innerHTML（XSS 风险）."""
    # 找 tooltipify 函数体
    idx = TEMPLATE.find("function tooltipify")
    assert idx > 0
    # 找下一个 function ( 或 } 收尾（取 ~3500 字节足够）
    body = TEMPLATE[idx:idx + 3500]
    assert ".innerHTML" not in body, "tooltipify 用了 innerHTML · XSS 风险 · 必须用 DOM API"
    # 必须有 createElement / textContent 安全构造
    assert "createElement" in body
    assert "textContent" in body
    assert "setAttribute" in body


# ─── #5 · Share-QR card ───────────────────────────────────

def test_share_qr_card_present():
    assert "share-qr-card" in TEMPLATE
    assert 'id="report-qr-canvas"' in TEMPLATE
    assert 'id="report-qr-url"' in TEMPLATE


def test_share_qr_handles_file_protocol():
    """file:// 本地路径下 · QR 不渲染外网二维码 · 提示 --remote."""
    idx = TEMPLATE.find("'file:'") if "'file:'" in TEMPLATE else TEMPLATE.find("file://")
    assert idx > 0 or "file://" in TEMPLATE
    # 提示文案
    assert "--remote" in TEMPLATE


def test_share_qr_uses_canvas_2d_no_innerhtml():
    """QR 渲染段也不能用 innerHTML."""
    idx = TEMPLATE.find("function drawQR")
    if idx < 0:
        # alternative name
        idx = TEMPLATE.find("qrCanvas")
    assert idx > 0
    body = TEMPLATE[idx:idx + 1500]
    # canvas 2D context 是安全的（图片绘制 / 文字绘制都不解析 HTML）
    assert "getContext" in body
    assert ".innerHTML" not in body, "QR 段不能 innerHTML"

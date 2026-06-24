"""Regression for v3.3.2 · GitHub issue #50 + #51 hotfixes.

#50 · institutional.py 调用 svg_sparkline 但未 import → NameError 卡死 stage2
     根因：v3.2 拆分 assemble_report → lib/report/* 时漏 import
     修法：lib/report/institutional.py 加 svg_sparkline 到 import block

#51 · xueqiu cubes_search.json 完全下线 → 登录 verify 永远失败
     社区反馈 (@Kylin824)：改用 query/v1/search/cube/stock.json
     修法：lib/xueqiu_browser.py + fetch_contests.py 同步换 endpoint
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


# ─── #50 · svg_sparkline import in institutional.py ───────────────────

def test_institutional_imports_svg_sparkline():
    """institutional.py 必须 import svg_sparkline · 否则 _render_lbo_block NameError."""
    src = (SCRIPTS / "lib" / "report" / "institutional.py").read_text(encoding="utf-8")
    # import 块必须含 svg_sparkline
    import_block_end = src.find("from lib.report.dim_viz import")
    assert import_block_end > 0
    import_block = src[:import_block_end]
    assert "svg_sparkline" in import_block, (
        "v3.3.2 regression: institutional.py 必须 import svg_sparkline"
        " · 否则 _render_lbo_block 触发 NameError 卡死 stage2 (issue #50)"
    )


def test_render_lbo_block_does_not_raise_nameerror():
    """实际跑 _render_lbo_block · 含 ebitda_path/debt_schedule 时不能 NameError."""
    from lib.report.institutional import _render_lbo_block
    dim20 = {
        "lbo": {
            "irr_pct": 22.5,
            "verdict": "Yes",
            "ebitda_path": [100, 110, 120, 130, 145],
            "debt_schedule": [500, 480, 450, 410, 360],
        }
    }
    html = _render_lbo_block(dim20)  # 之前会 NameError: svg_sparkline
    assert "<svg" in html, "svg_sparkline 调用失败"
    assert html.count("<svg") >= 2, "应生成 ebitda + debt 两个 sparkline"


# ─── #51 · xueqiu cubes endpoint migration ────────────────────────────

def test_xueqiu_login_url_uses_new_endpoint():
    """LOGIN_TEST_URL 必须用 query/v1/search/cube/stock.json (老 cubes_search.json 已下线)."""
    from lib.xueqiu_browser import LOGIN_TEST_URL
    assert "query/v1/search/cube/stock.json" in LOGIN_TEST_URL, (
        f"v3.3.2 regression: LOGIN_TEST_URL 仍用老 endpoint {LOGIN_TEST_URL}"
        " · 应该是 query/v1/search/cube/stock.json (issue #51)"
    )
    assert "cubes/cubes_search.json" not in LOGIN_TEST_URL, "老 endpoint 残留"


def test_xueqiu_browser_fetch_uses_new_endpoint():
    """fetch_cubes_via_browser 必须用新 endpoint."""
    import inspect
    from lib.xueqiu_browser import fetch_cubes_via_browser
    src = inspect.getsource(fetch_cubes_via_browser)
    assert "query/v1/search/cube/stock.json" in src, (
        "v3.3.2 regression: fetch_cubes_via_browser 仍用老 endpoint"
    )


def test_fetch_contests_uses_new_endpoint():
    """fetch_contests.fetch_xueqiu_cubes 必须用新 endpoint."""
    import inspect
    import fetch_contests
    src = inspect.getsource(fetch_contests.fetch_xueqiu_cubes)
    assert "query/v1/search/cube/stock.json" in src, (
        "v3.3.2 regression: fetch_contests 仍用老 endpoint"
    )

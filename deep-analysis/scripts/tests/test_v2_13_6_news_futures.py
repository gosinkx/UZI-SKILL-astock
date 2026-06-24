"""Regression tests for v2.13.6 · 新增 6 个经 curl 验证的期货/新闻源.

背景：用户 2026-04-19 第二波 Grok 清单（期货 + 财经新闻 · 10+ 源）批量 curl 验证：
- 有效 6 个：jin10 / em_kuaixun / em_stock_ann / 99qh / cfachina / ths_news_today
- 无效 7 个：sina 期货（403）· 金十 flash-api（502）· 新浪/央视/网易 RSS（404）· 雪球 batch（400）
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_registry_has_6_new_sources_v2_13_6():
    """70 = v2.13.5 64 + 新 6."""
    from lib.data_source_registry import SOURCES
    assert len(SOURCES) >= 70, f"registry 应 >= 70 · got {len(SOURCES)}"


def test_jin10_registered_as_cailianpress_alternative():
    """金十快讯 · 财联社替代品 · 必须覆盖 15_events + 17_sentiment."""
    from lib.data_source_registry import SOURCES
    s = next((x for x in SOURCES if x.id == "jin10_flash"), None)
    assert s is not None
    assert "15_events" in s.dims
    assert "17_sentiment" in s.dims
    assert s.health == "known_good"
    # 3 市场全覆盖（金十含国内+国际宏观）
    assert s.markets == ("A", "H", "U")


def test_em_kuaixun_for_news():
    from lib.data_source_registry import SOURCES
    s = next((x for x in SOURCES if x.id == "em_kuaixun"), None)
    assert s is not None
    assert "15_events" in s.dims


def test_em_stock_ann_for_a_share():
    """东财公告只覆盖 A 股（港美股用 hkexnews 等）."""
    from lib.data_source_registry import SOURCES
    s = next((x for x in SOURCES if x.id == "em_stock_ann"), None)
    assert s is not None
    assert s.markets == ("A",)
    assert "15_events" in s.dims


def test_futures_sources_cover_9_futures():
    """新增期货源 99qh + cfachina 必须覆盖 9_futures."""
    from lib.data_source_registry import SOURCES
    sids = {s.id: s for s in SOURCES}
    assert "9_futures" in sids["qh99_inventory"].dims
    assert "9_futures" in sids["cfachina"].dims


def test_qh99_covers_8_materials():
    """99 期货网含库存/现货 · 也辅助 8_materials 原材料价."""
    from lib.data_source_registry import SOURCES
    s = next((x for x in SOURCES if x.id == "qh99_inventory"), None)
    assert s is not None
    assert "8_materials" in s.dims


def test_ths_news_for_news_dim():
    from lib.data_source_registry import SOURCES
    s = next((x for x in SOURCES if x.id == "ths_news_today"), None)
    assert s is not None
    assert "15_events" in s.dims
    assert "17_sentiment" in s.dims


def test_registry_no_duplicates():
    from lib.data_source_registry import assert_registry_sane
    assert_registry_sane()


def test_http_sources_for_15_events_a_includes_new():
    """A 股 15_events 应含 jin10 / em_kuaixun / em_stock_ann / ths_news."""
    from lib.data_source_registry import http_sources_for
    ids = {s.id for s in http_sources_for("15_events", "A")}
    assert "jin10_flash" in ids
    assert "em_kuaixun" in ids
    assert "em_stock_ann" in ids
    assert "ths_news_today" in ids


def test_http_sources_for_9_futures_a_includes_new():
    """A 股 9_futures 应含 qh99 + cfachina."""
    from lib.data_source_registry import http_sources_for
    ids = {s.id for s in http_sources_for("9_futures", "A")}
    assert "qh99_inventory" in ids
    assert "cfachina" in ids

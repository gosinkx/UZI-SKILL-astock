"""Regression tests for v2.13.4 · 新增 10 个经 curl 验证的无 Key 公开数据源.

背景：用户 2026-04-19 提供 Grok 清单（20+ 个端点）· 批量 curl 验证：
- 9 个加密源（CoinGecko/OKX/KuCoin/Kraken/Gemini/CoinLore/GeckoTerminal）
- 1 个 Yahoo Chart v8（替代 401 的 v7 quote）
- 1 个 Tencent HK quote（腾讯港股 qt.gtimg.cn）

以下源验证为无效不加入：
- Sina sh/list（403 Forbidden，国内反爬）
- Netease chddata（502 Bad Gateway）
- Yahoo v7 quote（401 Unauthorized · 已被 Yahoo 关闭）
- Binance spot/24hr/futures（451 Restricted Location · 国内 IP 封）
- CoinCap / CoinDesk v1（连接不通）
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_registry_has_10_new_sources():
    """v2.13.4 新增 10 个源 · 总数应 >= 64."""
    from lib.data_source_registry import SOURCES
    assert len(SOURCES) >= 64, f"registry 应 >= 64 · got {len(SOURCES)}"


def test_new_sources_registered_by_id():
    """新增的 10 个源都应可按 id 查到."""
    from lib.data_source_registry import SOURCES
    ids = {s.id for s in SOURCES}
    expected = {
        "yahoo_chart_v8",
        "tencent_hk_quote",
        "coingecko_simple_price",
        "coingecko_markets",
        "okx_spot_tickers",
        "kucoin_stats",
        "kraken_trades",
        "gemini_ticker",
        "coinlore_tickers",
        "geckoterminal_networks",
    }
    missing = expected - ids
    assert not missing, f"新源缺失: {missing}"


def test_crypto_sources_attached_to_macro_dim():
    """加密源应标注到 3_macro 维度（作为全球流动性参考）."""
    from lib.data_source_registry import SOURCES
    crypto_ids = {"coingecko_simple_price", "coingecko_markets", "okx_spot_tickers",
                  "kucoin_stats", "kraken_trades", "gemini_ticker", "coinlore_tickers",
                  "geckoterminal_networks"}
    for s in SOURCES:
        if s.id in crypto_ids:
            assert "3_macro" in s.dims, f"{s.id} 应覆盖 3_macro · got dims={s.dims}"


def test_yahoo_chart_v8_for_us_hk():
    """Yahoo Chart v8 应覆盖 U + H · 标注 2_kline."""
    from lib.data_source_registry import SOURCES
    s = next((x for x in SOURCES if x.id == "yahoo_chart_v8"), None)
    assert s is not None
    assert "U" in s.markets and "H" in s.markets
    assert "2_kline" in s.dims
    assert s.tier == 1
    assert s.health == "known_good"


def test_tencent_hk_quote_for_0_basic():
    """腾讯港股 quote 应标 H 市场 + 0_basic."""
    from lib.data_source_registry import SOURCES
    s = next((x for x in SOURCES if x.id == "tencent_hk_quote"), None)
    assert s is not None
    assert s.markets == ("H",)
    assert "0_basic" in s.dims


def test_registry_sane_no_duplicates():
    """防御 · assert_registry_sane 不 raise（无重复 ID）."""
    from lib.data_source_registry import assert_registry_sane
    assert_registry_sane()  # raises on duplicate


def test_http_sources_for_hk_basic_includes_new():
    """http_sources_for('0_basic', 'H') 应包含新加的 tencent_hk_quote."""
    from lib.data_source_registry import http_sources_for
    sources = http_sources_for("0_basic", "H")
    ids = [s.id for s in sources]
    assert "tencent_hk_quote" in ids, f"tencent_hk_quote 应在 HK 0_basic 列表, got {ids}"


def test_http_sources_for_us_kline_includes_yahoo_v8():
    """http_sources_for('2_kline', 'U') 应包含 yahoo_chart_v8."""
    from lib.data_source_registry import http_sources_for
    sources = http_sources_for("2_kline", "U")
    ids = [s.id for s in sources]
    assert "yahoo_chart_v8" in ids, f"yahoo_chart_v8 应在 US kline 列表, got {ids}"

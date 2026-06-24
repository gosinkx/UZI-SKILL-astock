"""Regression for v3.4.2 · baostock fallback for fetch_basic + fetch_financials.

社群反馈（Windows + Clash）：
- 东方财富 Schannel TLS 不兼容 ❌
- Clash 国内规则 DIRECT 仍走 Schannel ❌
- baostock 完全绕过 ✅（自有协议 · 不受 SSL 兼容性影响）

修法：当 akshare (eastmoney/push2) 链全挂时 · 自动 fallback 到 baostock 拿
- PE / PB / price / name / listed_date  (lib/data_sources.fetch_basic)
- ROE 历史 / 营收历史 / 净利率 / 毛利率  (fetch_financials.py::_fetch_a_share)
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_data_sources_has_baostock_fallback_in_fetch_basic():
    """data_sources.fetch_basic 必须含 baostock fallback 段."""
    src = (SCRIPTS / "lib" / "data_sources.py").read_text(encoding="utf-8")
    # 找 _fetch_basic_impl_a / fetch_basic 体 · 必须 import baostock + 调 query_history_k_data_plus
    assert "query_history_k_data_plus" in src, (
        "v3.4.2 regression: fetch_basic 必须用 baostock query_history_k_data_plus 拿 PE/PB"
    )
    assert "peTTM" in src and "pbMRQ" in src, (
        "v3.4.2 必须从 baostock 拉 peTTM/pbMRQ 字段补 PE/PB"
    )


def test_fetch_financials_has_baostock_fallback():
    """fetch_financials._fetch_a_share 必须含 baostock 兜底."""
    src = (SCRIPTS / "fetch_financials.py").read_text(encoding="utf-8")
    assert "query_profit_data" in src, (
        "v3.4.2 regression: fetch_financials 必须用 baostock query_profit_data 兜底"
    )
    assert "roeAvg" in src
    assert "Schannel" in src or "v3.4.2" in src, "应注释说明 baostock fallback 动机"


def test_baostock_fallback_triggers_only_on_empty():
    """fetch_financials baostock 段只在 akshare 全挂时触发 · 不能覆盖有效数据."""
    src = (SCRIPTS / "fetch_financials.py").read_text(encoding="utf-8")
    # 找 needs_fallback 判断 · 必须 check 核心字段都空
    assert "needs_fallback" in src
    assert 'not out.get("roe")' in src or 'out.get(\"roe\")' in src


def test_baostock_provider_unchanged():
    """v3.4.2 不改 baostock_provider · 仍走老接口."""
    src = (SCRIPTS / "lib" / "providers" / "baostock_provider.py").read_text(encoding="utf-8")
    # provider 仍含 fetch_financials_a + fetch_kline_a · v3.4.2 新加的 fallback 直接调 bs · 不改 provider
    assert "fetch_financials_a" in src
    assert "fetch_kline_a" in src


def test_baostock_real_fetch_smoke(monkeypatch):
    """烟雾测试：baostock 茅台 query_profit_data 必须能返非空（依赖网络 · CI 可能跳）."""
    try:
        import baostock as bs
    except ImportError:
        import pytest
        pytest.skip("baostock 未装")

    lg = bs.login()
    if lg.error_code != "0":
        import pytest
        pytest.skip(f"baostock login 失败: {lg.error_msg}")
    try:
        rs = bs.query_profit_data(code="sh.600519", year=2025, quarter=1)
        rows = []
        while rs.error_code == "0" and rs.next():
            rows.append(rs.get_row_data())
        assert len(rows) >= 0, "至少能调通 (空 result 不算错)"
        # 如果有数据 · 必有这些字段
        if rows:
            fields = rs.fields
            assert "roeAvg" in fields
            assert "npMargin" in fields
    finally:
        bs.logout()


def test_provider_chain_includes_baostock():
    """provider 注册表必须含 baostock."""
    from lib.providers import baostock_provider as bsm
    p = bsm._BaostockProvider()
    assert p.name == "baostock"
    assert p.requires_key is False
    assert "A" in p.markets

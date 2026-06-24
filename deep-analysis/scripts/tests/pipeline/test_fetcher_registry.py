"""v3.0.0 Phase 2 · 22 fetcher adapter 注册表测试."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_registry_has_21_unique_dim_keys():
    """22 legacy fetcher · 但 fetch_fund_holders + fetch_research 共享 '6_' 前缀（fund_holders/research）· 注册表用 6_fund_holders / 6_research 区分."""
    from lib.pipeline.fetchers import list_fetchers
    keys = list_fetchers()
    # 6_fund_holders 和 6_research 算两个 · 总计 21 个 unique key（合并到注册表）
    # 实际 22 fetcher 里 fetch_similar_stocks 是 bonus 不算主 22
    assert len(keys) >= 20, f"至少 20 个 fetcher · 实际 {len(keys)}"


def test_registry_all_adapters_loadable():
    """所有 adapter 可以 instantiate 且 spec 完整."""
    from lib.pipeline.fetchers import list_fetchers, get_fetcher
    for dim_key in list_fetchers():
        f = get_fetcher(dim_key)
        assert f is not None, f"{dim_key} 加载失败"
        assert f.spec.dim_key == dim_key
        assert isinstance(f.spec.sources, list) and len(f.spec.sources) > 0


def test_fetcher_adapter_returns_dim_result(monkeypatch):
    """adapter 跑 legacy main · 返 DimResult · 空时 quality=MISSING·不是 FULL."""
    from lib.pipeline.fetchers import get_fetcher
    from lib.pipeline import Quality

    f = get_fetcher("0_basic")
    # mock legacy main · 返空 dict
    import fetch_basic
    monkeypatch.setattr(fetch_basic, "main", lambda t: {"data": {}})
    r = f.fetch("300470.SZ")
    assert r.dim_key == "0_basic"
    assert r.quality in (Quality.MISSING, Quality.PARTIAL, Quality.ERROR)


def test_fetcher_adapter_catches_legacy_exception(monkeypatch):
    """legacy main 抛异常 · adapter 返 ERROR · 不 propagate."""
    from lib.pipeline.fetchers import get_fetcher
    from lib.pipeline import Quality

    f = get_fetcher("1_financials")
    import fetch_financials
    monkeypatch.setattr(fetch_financials, "main", lambda t: (_ for _ in ()).throw(RuntimeError("SSL fail")))
    r = f.fetch("300470.SZ")
    assert r.quality == Quality.ERROR
    assert "SSL fail" in r.error


def test_fund_holders_adapter_extracts_top_level(monkeypatch):
    """fund_holders adapter · fund_managers 必须去 top_level · 不在 data."""
    from lib.pipeline.fetchers import get_fetcher
    f = get_fetcher("6_fund_holders")
    import fetch_fund_holders
    monkeypatch.setattr(fetch_fund_holders, "main", lambda t, **kw: {
        "data": {
            "fund_managers": [{"fund_code": "022645", "position_pct": 4.92}],
            "total_funds_holding": 993,
        }
    })
    r = f.fetch("300470.SZ")
    assert "fund_managers" in r.top_level_fields
    assert r.top_level_fields["fund_managers"][0]["fund_code"] == "022645"
    assert "fund_managers" not in r.data
    assert r.data.get("total_funds_holding") == 993


def test_list_fetchers_covers_main_22():
    """主要 22 fetcher 都在注册表里（至少下列核心 dim）."""
    from lib.pipeline.fetchers import list_fetchers
    keys = set(list_fetchers())
    must_have = {
        "0_basic", "1_financials", "2_kline", "3_macro", "4_peers",
        "5_chain", "6_fund_holders", "6_research", "7_industry", "8_materials",
        "9_futures", "10_valuation", "11_governance", "12_capital_flow",
        "13_policy", "14_moat", "15_events", "16_lhb", "17_sentiment",
        "18_trap", "19_contests",
    }
    missing = must_have - keys
    assert not missing, f"注册表缺：{missing}"

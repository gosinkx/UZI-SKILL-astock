"""v3.0.0 · BaseFetcher 测试."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_base_fetcher_requires_spec():
    """子类不声明 spec 必须 TypeError."""
    from lib.pipeline import BaseFetcher
    import pytest
    with pytest.raises(TypeError):
        class BadFetcher(BaseFetcher):
            def _fetch_raw(self, ticker): return {}


def test_base_fetcher_catches_exception():
    from lib.pipeline import BaseFetcher, Quality
    from lib.pipeline.schema import FetcherSpec

    class BuggyFetcher(BaseFetcher):
        spec = FetcherSpec(dim_key="0_basic", required_fields=["name"])
        def _fetch_raw(self, ticker):
            raise RuntimeError("network down")

    f = BuggyFetcher()
    r = f.fetch("300470.SZ")
    assert r.quality == Quality.ERROR
    assert "network down" in r.error


def test_base_fetcher_normalizes_empty_sentinels():
    from lib.pipeline import BaseFetcher, Quality
    from lib.pipeline.schema import FetcherSpec

    class TestFetcher(BaseFetcher):
        spec = FetcherSpec(
            dim_key="0_basic",
            required_fields=["name"],
            optional_fields=["pe_ttm"],
            sources=["akshare:test"],
        )
        def _fetch_raw(self, ticker):
            return {"name": "中密", "pe_ttm": "—", "extra_field": ""}

    r = TestFetcher().fetch("300470.SZ")
    assert r.data["name"] == "中密"
    assert r.data["pe_ttm"] is None  # normalized from "—"
    assert r.data["extra_field"] is None  # normalized from ""
    assert r.quality == Quality.PARTIAL
    assert "pe_ttm" in r.data_gaps


def test_base_fetcher_extracts_top_level():
    """fund_managers 类字段应去 top_level_fields."""
    from lib.pipeline import BaseFetcher
    from lib.pipeline.schema import FetcherSpec

    class FundLike(BaseFetcher):
        spec = FetcherSpec(
            dim_key="6_fund_holders",
            required_fields=["total_funds_holding"],
            top_level_fields=["fund_managers"],
            sources=["akshare"],
        )
        def _fetch_raw(self, ticker):
            return {
                "total_funds_holding": 993,
                "fund_managers": [{"fund_code": "022645", "position_pct": 4.92}],
            }

    r = FundLike().fetch("300470.SZ")
    assert "fund_managers" in r.top_level_fields
    assert "fund_managers" not in r.data  # 已移到 top_level
    assert r.data["total_funds_holding"] == 993


def test_base_fetcher_keep_zero_fields():
    """子类声明 keep_zero_fields · 0 不应被规约 None."""
    from lib.pipeline import BaseFetcher
    from lib.pipeline.schema import FetcherSpec

    class WithZero(BaseFetcher):
        spec = FetcherSpec(dim_key="x", required_fields=["count"], sources=["test"])
        keep_zero_fields = {"count"}
        def _fetch_raw(self, ticker):
            return {"count": 0}

    r = WithZero().fetch("x")
    assert r.data["count"] == 0
    from lib.pipeline import Quality
    assert r.quality == Quality.FULL  # count=0 是有效值 · 未缺失

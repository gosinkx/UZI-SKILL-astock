"""v3.0.0 · pipeline.schema 测试."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_quality_enum():
    from lib.pipeline import Quality
    assert Quality.FULL.value == "full"
    assert Quality.PARTIAL.value == "partial"
    assert Quality.MISSING.value == "missing"
    assert Quality.ERROR.value == "error"


def test_dim_result_empty():
    from lib.pipeline import DimResult, Quality
    r = DimResult.empty("0_basic")
    assert r.dim_key == "0_basic"
    assert r.quality == Quality.MISSING
    assert r.data == {}
    assert r.data_gaps == []


def test_dim_result_error():
    from lib.pipeline import DimResult, Quality
    r = DimResult.error_result("6_fund_holders", "SSL failed", source="akshare")
    assert r.quality == Quality.ERROR
    assert "SSL failed" in r.error


def test_dim_result_to_from_dict_roundtrip():
    """v3.0.0 业务零区别 · to_dict 顶层必须是 legacy 格式 · quality 等挪到 _pipeline."""
    from lib.pipeline import DimResult, Quality
    r = DimResult(
        dim_key="1_financials",
        data={"roe": 15.5},
        source="akshare",
        quality=Quality.PARTIAL,
        data_gaps=["net_margin"],
    )
    d = r.to_dict()
    # 顶层 legacy 格式
    assert d["data"]["roe"] == 15.5
    assert d["source"] == "akshare"
    assert d["fallback"] is False  # partial 不算 fallback
    # pipeline-extra 在 _pipeline 命名空间
    assert d["_pipeline"]["quality"] == "partial"
    assert d["_pipeline"]["data_gaps"] == ["net_margin"]
    assert d["_pipeline"]["dim_key"] == "1_financials"
    # roundtrip 恢复
    r2 = DimResult.from_dict(d)
    assert r2.dim_key == r.dim_key
    assert r2.quality == Quality.PARTIAL
    assert r2.data["roe"] == 15.5


def test_dim_result_to_dict_legacy_compat():
    """v3.0.0 · 输出必须跟 legacy fetcher 格式一致 · 零业务区别."""
    from lib.pipeline import DimResult, Quality
    r = DimResult(
        dim_key="0_basic", data={"name": "x"}, source="akshare:test",
        quality=Quality.FULL,
    )
    d = r.to_dict()
    # 必有的 legacy 顶层字段
    for field in ("data", "source", "fallback"):
        assert field in d, f"legacy 必要字段 {field} 缺失"
    # fallback 必须是 bool
    assert isinstance(d["fallback"], bool)


def test_dim_result_error_fallback_true():
    """error quality → fallback=True · legacy 约定."""
    from lib.pipeline import DimResult
    r = DimResult.error_result("x", "fail")
    d = r.to_dict()
    assert d["fallback"] is True  # quality=error → fallback=true


def test_fetcher_spec_required_dim_key():
    from lib.pipeline.schema import FetcherSpec
    import pytest
    with pytest.raises(ValueError):
        FetcherSpec(dim_key="")

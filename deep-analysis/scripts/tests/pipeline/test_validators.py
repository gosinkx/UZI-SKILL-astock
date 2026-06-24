"""v3.0.0 · pipeline.validators 测试 · 核心防 v2.15.1 回归."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_is_empty_value_none_string_sentinels():
    from lib.pipeline import is_empty_value
    assert is_empty_value(None) is True
    assert is_empty_value("") is True
    assert is_empty_value("—") is True
    assert is_empty_value("-") is True
    assert is_empty_value("n/a") is True
    assert is_empty_value("  ") is True
    assert is_empty_value("无数据") is True


def test_is_empty_value_empty_containers():
    from lib.pipeline import is_empty_value
    assert is_empty_value([]) is True
    assert is_empty_value({}) is True
    assert is_empty_value(()) is True


def test_is_empty_value_preserves_zero():
    """v2.15.1 的核心教训：数值 0 不应被视为"空值"."""
    from lib.pipeline import is_empty_value
    assert is_empty_value(0) is False   # 0 是有效值
    assert is_empty_value(0.0) is False
    assert is_empty_value(False) is False


def test_is_empty_value_preserves_valid_data():
    from lib.pipeline import is_empty_value
    assert is_empty_value(15.5) is False
    assert is_empty_value("中密控股") is False
    assert is_empty_value({"key": "value"}) is False
    assert is_empty_value([1, 2, 3]) is False


def test_is_data_gap_missing_key():
    from lib.pipeline import is_data_gap
    assert is_data_gap({}, "price") is True
    assert is_data_gap({"price": None}, "price") is True
    assert is_data_gap({"price": "—"}, "price") is True
    assert is_data_gap({"price": 100.5}, "price") is False


def test_normalize_empty_converts_sentinel_to_none():
    from lib.pipeline.validators import normalize_empty
    assert normalize_empty("") is None
    assert normalize_empty("—") is None
    assert normalize_empty("n/a") is None
    assert normalize_empty(None) is None
    # 保留有效值
    assert normalize_empty(15.5) == 15.5
    assert normalize_empty(0) == 0


def test_normalize_data_default_preserves_zero():
    """如果字段语义是 "0 也是数据"（如 holding_quarters=0），不应被规约."""
    from lib.pipeline.validators import normalize_data
    data = {"price": "—", "holding_quarters": 0, "name": "中密"}
    out = normalize_data(data, keep_zero_fields={"holding_quarters"})
    assert out["price"] is None
    assert out["holding_quarters"] == 0
    assert out["name"] == "中密"


def test_validate_result_sets_quality_full_when_all_filled():
    from lib.pipeline import DimResult, Quality
    from lib.pipeline.schema import FetcherSpec
    from lib.pipeline.validators import validate_result

    spec = FetcherSpec(
        dim_key="0_basic",
        required_fields=["name", "price"],
        optional_fields=["pe_ttm"],
    )
    r = DimResult(
        dim_key="0_basic",
        data={"name": "中密", "price": 36.52, "pe_ttm": 19.8},
    )
    r = validate_result(r, spec)
    assert r.quality == Quality.FULL
    assert r.data_gaps == []


def test_validate_result_sets_quality_partial_when_optional_missing():
    from lib.pipeline import DimResult, Quality
    from lib.pipeline.schema import FetcherSpec
    from lib.pipeline.validators import validate_result

    spec = FetcherSpec(
        dim_key="0_basic",
        required_fields=["name", "price"],
        optional_fields=["pe_ttm", "industry"],
    )
    r = DimResult(
        dim_key="0_basic",
        data={"name": "中密", "price": 36.52, "pe_ttm": None, "industry": "—"},
    )
    r = validate_result(r, spec)
    assert r.quality == Quality.PARTIAL
    assert "pe_ttm" in r.data_gaps
    assert "industry" in r.data_gaps


def test_validate_result_sets_quality_missing_when_all_required_empty():
    from lib.pipeline import DimResult, Quality
    from lib.pipeline.schema import FetcherSpec
    from lib.pipeline.validators import validate_result

    spec = FetcherSpec(
        dim_key="0_basic",
        required_fields=["name", "price"],
    )
    r = DimResult(dim_key="0_basic", data={"name": None, "price": "—"})
    r = validate_result(r, spec)
    assert r.quality == Quality.MISSING


def test_validate_preserves_error_quality():
    """Quality.ERROR 不应被 validate 改写."""
    from lib.pipeline import DimResult, Quality
    from lib.pipeline.schema import FetcherSpec
    from lib.pipeline.validators import validate_result

    spec = FetcherSpec(dim_key="0_basic", required_fields=["name"])
    r = DimResult.error_result("0_basic", "fetcher crashed")
    assert r.quality == Quality.ERROR
    r = validate_result(r, spec)
    assert r.quality == Quality.ERROR, "error 状态 validate 不应改写"


def test_quality_score_ratio():
    from lib.pipeline import DimResult
    from lib.pipeline.schema import FetcherSpec
    from lib.pipeline.validators import quality_score

    spec = FetcherSpec(
        dim_key="x",
        required_fields=["a", "b"],
        optional_fields=["c", "d"],
    )
    r = DimResult(dim_key="x", data={"a": 1, "b": 2, "c": None, "d": None})
    assert quality_score(r, spec) == 0.5

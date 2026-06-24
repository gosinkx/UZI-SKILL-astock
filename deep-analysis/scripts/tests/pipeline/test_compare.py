"""v3.0.0 Phase 6b · pipeline.compare 测试."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_values_match_identical():
    from lib.pipeline.compare import _values_match
    assert _values_match(15.5, 15.5) is True
    assert _values_match("中密控股", "中密控股") is True


def test_values_match_empty_equivalents():
    """None / "" / "—" / "n/a" 互相等价."""
    from lib.pipeline.compare import _values_match
    assert _values_match(None, "") is True
    assert _values_match("", "—") is True
    assert _values_match("n/a", None) is True
    assert _values_match([], None) is True


def test_values_match_numeric_tolerance():
    """数值宽松比较（0.01 tolerance）· 兼容 legacy 19.8 vs pipeline 19.80 str."""
    from lib.pipeline.compare import _values_match
    assert _values_match(19.8, "19.8") is True
    assert _values_match("19.8%", 19.8) is True
    assert _values_match(15.5, 15.51) is True   # within 0.01
    assert _values_match(15.5, 15.6) is False   # outside tolerance


def test_compare_raw_data_no_diffs_for_empty():
    from lib.pipeline.compare import compare_raw_data
    r = compare_raw_data({}, {})
    assert r["diff_count"] == 0


def test_compare_raw_data_finds_diff():
    from lib.pipeline.compare import compare_raw_data
    legacy = {
        "dimensions": {
            "0_basic": {"data": {"name": "中密控股", "price": 36.52, "pe_ttm": 19.8}}
        }
    }
    pipeline = {
        "dimensions": {
            "0_basic": {"data": {"name": "中密控股", "price": 36.52, "pe_ttm": 25.0}}  # diff here
        }
    }
    r = compare_raw_data(legacy, pipeline)
    assert r["diff_count"] == 1
    assert any(d["field"] == "pe_ttm" for d in r["diffs"])


def test_compare_raw_data_top_level_fund_managers():
    """顶层 fund_managers count 差异要被 detect."""
    from lib.pipeline.compare import compare_raw_data
    legacy = {"dimensions": {}, "fund_managers": [{"x": 1}, {"x": 2}]}
    pipeline = {"dimensions": {}, "fund_managers": [{"x": 1}]}
    r = compare_raw_data(legacy, pipeline)
    assert r["diff_count"] >= 1
    assert any(d["field"] == "fund_managers" for d in r["diffs"])


def test_compare_ignores_pipeline_only_fields():
    """quality / data_gaps / latency_ms 等是 pipeline-only · 不应触发 diff."""
    from lib.pipeline.compare import compare_raw_data
    legacy = {
        "dimensions": {
            "0_basic": {"data": {"name": "中密", "price": 36.52}, "source": "akshare", "fallback": False}
        }
    }
    pipeline = {
        "dimensions": {
            "0_basic": {
                "dim_key": "0_basic",
                "data": {"name": "中密", "price": 36.52},
                "source": "akshare",
                "quality": "full",
                "data_gaps": [],
                "latency_ms": 123,
            }
        }
    }
    r = compare_raw_data(legacy, pipeline)
    assert r["diff_count"] == 0, "pipeline-only 字段不应触发 diff"

"""v3.0.0 Phase 4 · pipeline.collect 测试."""
from __future__ import annotations

import os
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_is_pipeline_enabled_env_flag():
    from lib.pipeline import is_pipeline_enabled
    os.environ.pop("UZI_PIPELINE", None)
    assert is_pipeline_enabled() is False
    os.environ["UZI_PIPELINE"] = "1"
    try:
        assert is_pipeline_enabled() is True
    finally:
        os.environ.pop("UZI_PIPELINE", None)


def test_is_resume_valid_rejects_error_quality():
    from lib.pipeline.collect import _is_resume_valid
    assert _is_resume_valid({"data": {"x": 1}, "quality": "full"}) is True
    assert _is_resume_valid({"data": {}, "quality": "error"}) is False
    assert _is_resume_valid({"data": None, "quality": "missing"}) is False
    assert _is_resume_valid(None) is False
    assert _is_resume_valid({"data": {"x": 1}}) is True  # 老格式兼容


def test_dependent_dims_set():
    from lib.pipeline.collect import DEPENDENT_DIMS
    assert "3_macro" in DEPENDENT_DIMS
    assert "7_industry" in DEPENDENT_DIMS
    assert "9_futures" in DEPENDENT_DIMS
    assert "13_policy" in DEPENDENT_DIMS
    # 0_basic 不应该在
    assert "0_basic" not in DEPENDENT_DIMS

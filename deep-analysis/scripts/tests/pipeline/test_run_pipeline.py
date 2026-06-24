"""v3.0.0 Phase 6a · pipeline.run_pipeline · delegate wrapper smoke test."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SCRIPTS))


def test_run_pipeline_exported():
    """run_pipeline 可从 lib.pipeline 顶层 import."""
    from lib.pipeline import run_pipeline
    assert callable(run_pipeline)


def test_score_from_cache_exists():
    from lib.pipeline.score import score_from_cache
    assert callable(score_from_cache)


def test_synthesize_and_render_exists():
    from lib.pipeline.synthesize import synthesize_and_render
    assert callable(synthesize_and_render)


def test_pipeline_run_has_load_and_write_cache():
    """run.py 内部 helper 存在 · 用于 resume + 落地 raw_data.json."""
    from lib.pipeline.run import _load_cache, _write_cache
    assert callable(_load_cache)
    assert callable(_write_cache)


def test_run_pipeline_signature():
    """run_pipeline(ticker, resume=True) · 签名稳定."""
    import inspect
    from lib.pipeline.run import run_pipeline
    sig = inspect.signature(run_pipeline)
    params = list(sig.parameters.keys())
    assert "ticker" in params
    assert "resume" in params

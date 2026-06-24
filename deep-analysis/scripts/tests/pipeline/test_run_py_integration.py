"""v3.0.0 Phase 7 · run.py UZI_PIPELINE=1 opt-in 集成测试."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SCRIPTS))

ROOT = SCRIPTS.parent.parent.parent


def test_run_py_has_uzi_pipeline_check():
    """run.py 含 UZI_PIPELINE=1 检测 · Phase 7 的核心."""
    run_py = ROOT / "run.py"
    txt = run_py.read_text(encoding="utf-8")
    assert "UZI_PIPELINE" in txt, "run.py 必须检测 UZI_PIPELINE env"
    assert "run_pipeline" in txt, "run.py 必须调 pipeline.run_pipeline"


def test_run_py_has_fallback_on_exception():
    """pipeline 异常时必须回退 legacy · 保护业务流程."""
    run_py = ROOT / "run.py"
    txt = run_py.read_text(encoding="utf-8")
    assert "_pipeline_succeeded" in txt
    assert "回退 legacy" in txt or "fallback" in txt.lower()


def test_run_py_default_still_legacy():
    """UZI_PIPELINE 未设时必须保持 legacy 路径 · 向后兼容."""
    run_py = ROOT / "run.py"
    txt = run_py.read_text(encoding="utf-8")
    # 默认路径（非 pipeline）必须仍调 _stage1/_stage2 或 run_analysis
    assert "_stage1(args.ticker)" in txt or "run_analysis(args.ticker)" in txt


def test_pipeline_imports_work():
    """UZI_PIPELINE=1 入口 · import 链路完整 · 不会因为循环 import 挂."""
    from lib.pipeline import run_pipeline
    assert callable(run_pipeline)
    from lib.pipeline.run import _load_cache, _write_cache
    assert callable(_load_cache)

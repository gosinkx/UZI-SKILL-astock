"""Regression for v3.3.4 · GitHub issue #61 mini_racer V8 crash escape hatch.

#61 · @dragonforai · macOS Py 3.12/3.13 + mini_racer 在多线程下即使串行化仍可能
     V8 isolate 双重初始化 SIGTRAP（"address_pool_manager.cc Check failed"）·
     用户报 `python run.py SEHK.03690 --depth deep` 崩溃.

修法（多重）:
1. `UZI_DISABLE_MINI_RACER=1` env var · 显式跳过 3 个 fetcher · graceful 降级
2. Sentinel 文件 (~/.uzi-skill/_minirackercrash.sentinel) · 调用前 arm · 成功后 disarm
   下次启动若 sentinel 还在 = 上次崩了 · 自动 disable
3. `UZI_FORCE_MINI_RACER=1` 强制启用（让用户能手动测试 / 强制忽略 sentinel）
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


def _clean_state(monkeypatch, tmp_path):
    """每个测试隔离 env + sentinel."""
    for k in ("UZI_DISABLE_MINI_RACER", "UZI_FORCE_MINI_RACER"):
        monkeypatch.delenv(k, raising=False)
    sentinel = tmp_path / ".uzi-skill" / "_minirackercrash.sentinel"
    return sentinel


def test_disable_env_var_skips_fetcher(monkeypatch, tmp_path):
    """UZI_DISABLE_MINI_RACER=1 时 · 跑 fetch_industry 应直接跳过返 fallback."""
    import run_real_test as rrt

    monkeypatch.setenv("UZI_DISABLE_MINI_RACER", "1")
    monkeypatch.setattr(rrt, "_MINI_RACER_SENTINEL", tmp_path / "sentinel")

    result = rrt.run_fetcher("fetch_industry", ("综合",))
    assert result.get("fallback") is True
    assert "skipped" in result.get("source", "") or "skipped" in str(result.get("data", {}))
    assert "mini_racer" in (result.get("error") or "").lower()


def test_force_overrides_sentinel(monkeypatch, tmp_path):
    """UZI_FORCE_MINI_RACER=1 时 · 即使 sentinel 存在也应启用 mini_racer."""
    import run_real_test as rrt

    sentinel = tmp_path / "sentinel"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text("dummy", encoding="utf-8")
    monkeypatch.setattr(rrt, "_MINI_RACER_SENTINEL", sentinel)

    monkeypatch.delenv("UZI_DISABLE_MINI_RACER", raising=False)
    monkeypatch.setenv("UZI_FORCE_MINI_RACER", "1")

    # 重置 _warned · 避免之前测试污染
    if hasattr(rrt._mini_racer_disabled, "_warned"):
        del rrt._mini_racer_disabled._warned

    assert rrt._mini_racer_disabled() is False, "UZI_FORCE_MINI_RACER=1 应覆盖 sentinel"


def test_sentinel_auto_disable(monkeypatch, tmp_path):
    """Sentinel 存在时 · _mini_racer_disabled 应返 True (auto-recovery)."""
    import run_real_test as rrt

    sentinel = tmp_path / "_minirackercrash.sentinel"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text("12345.0|fetch_industry\n", encoding="utf-8")
    monkeypatch.setattr(rrt, "_MINI_RACER_SENTINEL", sentinel)

    monkeypatch.delenv("UZI_DISABLE_MINI_RACER", raising=False)
    monkeypatch.delenv("UZI_FORCE_MINI_RACER", raising=False)

    if hasattr(rrt._mini_racer_disabled, "_warned"):
        del rrt._mini_racer_disabled._warned

    assert rrt._mini_racer_disabled() is True, "sentinel 存在时应 auto-disable"


def test_sentinel_arm_and_disarm_lifecycle(monkeypatch, tmp_path):
    """成功调 mini_racer fetcher 后 · sentinel 应被删除."""
    import run_real_test as rrt

    sentinel = tmp_path / "_minirackercrash.sentinel"
    monkeypatch.setattr(rrt, "_MINI_RACER_SENTINEL", sentinel)

    rrt._arm_mini_racer_sentinel("fetch_industry")
    assert sentinel.exists(), "arm 后 sentinel 应存在"

    rrt._disarm_mini_racer_sentinel()
    assert not sentinel.exists(), "disarm 后 sentinel 应删除"


def test_normal_python_exception_does_not_leave_sentinel(monkeypatch, tmp_path):
    """普通 Python 异常时 sentinel 应被清掉 · 区别于 V8 SIGTRAP（进程级崩 · sentinel 留）."""
    import run_real_test as rrt

    sentinel = tmp_path / "_minirackercrash.sentinel"
    monkeypatch.setattr(rrt, "_MINI_RACER_SENTINEL", sentinel)
    monkeypatch.delenv("UZI_DISABLE_MINI_RACER", raising=False)
    monkeypatch.delenv("UZI_FORCE_MINI_RACER", raising=False)
    if hasattr(rrt._mini_racer_disabled, "_warned"):
        del rrt._mini_racer_disabled._warned

    # mock 一个会抛 ValueError 的 fetcher (非 SIGTRAP)
    fake_mod = MagicMock()
    fake_mod.main = MagicMock(side_effect=ValueError("simulated logic error"))

    real_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

    def fake_import(name, *args, **kwargs):
        if name == "fetch_industry":
            return fake_mod
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    result = rrt.run_fetcher("fetch_industry", ("综合",))

    assert result.get("fallback") is True, "异常时应返 fallback dict"
    assert "ValueError" in (result.get("error") or "")
    # sentinel 应已被 disarm (普通异常不留 · 否则下次启动会误判 V8 crash)
    assert not sentinel.exists(), "普通 Python 异常后 sentinel 应被清掉"


def test_non_minirackerfetcher_unaffected(monkeypatch):
    """非 mini_racer fetcher 应不受 disable env 影响."""
    import run_real_test as rrt

    monkeypatch.setenv("UZI_DISABLE_MINI_RACER", "1")

    fake_mod = MagicMock()
    fake_mod.main = MagicMock(return_value={"data": {"name": "test"}, "source": "test"})

    real_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

    def fake_import(name, *args, **kwargs):
        if name == "fetch_basic":
            return fake_mod
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    result = rrt.run_fetcher("fetch_basic", ("002217.SZ",))
    assert result.get("data", {}).get("name") == "test"
    fake_mod.main.assert_called_once()


def test_pipeline_collect_respects_disable(monkeypatch):
    """pipeline.collect 也应识别 UZI_DISABLE_MINI_RACER · 不调 fetcher."""
    src = (SCRIPTS / "lib" / "pipeline" / "collect.py").read_text(encoding="utf-8")
    assert "UZI_DISABLE_MINI_RACER" in src, (
        "pipeline.collect 必须支持 UZI_DISABLE_MINI_RACER · 否则 pipeline 路径仍会崩 (issue #61)"
    )

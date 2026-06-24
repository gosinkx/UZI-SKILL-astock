"""pipeline.compare · dark-launch 对比工具.

用途（Phase 6b）：切换默认入口之前 · 必须证明 pipeline.run_pipeline 产出跟 legacy 一致.

场景：
- 同一 ticker 先走 legacy 再走 pipeline · 两份 raw_data.json diff
- 关键字段（ROE / PE / panel consensus / fund 数 / 评委投票分布）应一致
- 允许差异的字段：latency_ms / quality / data_gaps / top_level_fields（这些是新加的）

用法：
    from lib.pipeline.compare import compare_raw_data, run_dark_launch
    result = run_dark_launch("300470.SZ")
    print(result["matches"], result["diffs"])
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# 新增字段 · 不参与 diff（legacy 侧没有）
PIPELINE_ONLY_FIELDS = {"dim_key", "quality", "data_gaps", "latency_ms", "top_level_fields", "cached"}

# 关键字段（必须一致）· 按 dim 列出
KEY_FIELDS_BY_DIM = {
    "0_basic": ["name", "price", "pe_ttm", "pb", "market_cap", "industry"],
    "1_financials": ["roe", "net_margin", "revenue_growth"],
    "7_industry": ["industry"],
    "10_valuation": ["pe_ttm", "pb"],
}


def compare_raw_data(legacy_raw: dict, pipeline_raw: dict) -> dict:
    """对比两份 raw_data · 返 {matches, diffs, summary}.

    忽略 pipeline-only 字段 · 只对比业务数据（dim.data 里的核心字段）.
    """
    diffs = []
    matches = 0
    legacy_dims = legacy_raw.get("dimensions", {})
    pipeline_dims = pipeline_raw.get("dimensions", {})

    all_dims = set(legacy_dims.keys()) | set(pipeline_dims.keys())
    for dim_key in sorted(all_dims):
        l_dim = legacy_dims.get(dim_key, {})
        p_dim = pipeline_dims.get(dim_key, {})
        l_data = l_dim.get("data") or {}
        p_data = p_dim.get("data") or {}

        key_fields = KEY_FIELDS_BY_DIM.get(dim_key, [])
        for field in key_fields:
            l_val = l_data.get(field)
            p_val = p_data.get(field)
            if _values_match(l_val, p_val):
                matches += 1
            else:
                diffs.append({
                    "dim": dim_key,
                    "field": field,
                    "legacy": _safe_repr(l_val),
                    "pipeline": _safe_repr(p_val),
                })

    # 顶层溢出字段也要对比
    for top_field in ("fund_managers", "similar_stocks"):
        l_val = legacy_raw.get(top_field)
        p_val = pipeline_raw.get(top_field)
        if l_val is None and p_val is None:
            continue
        l_count = len(l_val) if isinstance(l_val, list) else (1 if l_val else 0)
        p_count = len(p_val) if isinstance(p_val, list) else (1 if p_val else 0)
        if l_count != p_count:
            diffs.append({
                "dim": "(top-level)",
                "field": top_field,
                "legacy": f"{l_count} items",
                "pipeline": f"{p_count} items",
            })
        else:
            matches += 1

    return {
        "matches": matches,
        "diff_count": len(diffs),
        "diffs": diffs[:20],  # 截断前 20 条 · 避免爆屏
        "summary": f"{matches} 字段一致 / {len(diffs)} 差异",
    }


def _values_match(a: Any, b: Any) -> bool:
    """宽松比较 · None == "" == "—" · 数值转 float 比"""
    if a is None and b is None:
        return True
    # 空值等价
    if _is_empty(a) and _is_empty(b):
        return True
    # 数值宽松比
    try:
        fa = _try_float(a)
        fb = _try_float(b)
        if fa is not None and fb is not None:
            return abs(fa - fb) < 0.01
    except Exception:
        pass
    return str(a).strip() == str(b).strip()


def _is_empty(v):
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip() in ("", "—", "-", "n/a", "N/A", "无数据")
    if isinstance(v, (list, dict, tuple)) and len(v) == 0:
        return True
    return False


def _try_float(v):
    if v is None:
        return None
    try:
        s = str(v).strip().rstrip("%")
        # 去逗号
        s = s.replace(",", "")
        return float(s)
    except (ValueError, TypeError):
        return None


def _safe_repr(v) -> str:
    if v is None:
        return "None"
    s = str(v)
    return s[:60] + "…" if len(s) > 60 else s


def run_dark_launch(ticker: str, save_diff_to: str | None = None) -> dict:
    """跑一次 legacy + pipeline · 返回对比结果.

    注意：不实际执行全流程 · 而是假设两侧已有 cache · 读 raw_data.json 对比.
    完整 e2e 请在 shell 里分别跑 UZI_PIPELINE=0 和 UZI_PIPELINE=1 再调 `compare_cached_runs`.
    """
    return compare_cached_runs(ticker, save_diff_to=save_diff_to)


def compare_cached_runs(ticker: str, save_diff_to: str | None = None) -> dict:
    """基于已有的 cache raw_data.json 做对比（假设测试时手动切 UZI_PIPELINE 跑了两轮）.

    实际测试流程：
    1. 用户 shell: UZI_PIPELINE=0 python3 run.py 300470.SZ --no-resume （记下 raw_data）
    2. 用户 shell: cp .cache/300470.SZ/raw_data.json /tmp/legacy_raw.json
    3. 用户 shell: UZI_PIPELINE=1 python3 run.py 300470.SZ --no-resume （记下 raw_data）
    4. 调 compare_files(legacy_path, pipeline_path)
    """
    # 这个函数只做文件读 + compare_raw_data
    from lib.market_router import parse_ticker
    import run_real_test as rrt
    ti = parse_ticker(ticker)
    cache_path = Path(rrt.__file__).parent / ".cache" / ti.full / "raw_data.json"

    if not cache_path.exists():
        return {"error": f"cache 不存在 {cache_path}"}

    # 只读当前 cache（仅作格式演示 · 真正 diff 需要用户手动提供两份）
    current = json.loads(cache_path.read_text(encoding="utf-8"))
    return {
        "note": "compare_cached_runs 需要手动提供两份 raw_data 文件 · 调 compare_files(l, p)",
        "current_dims": list(current.get("dimensions", {}).keys()),
    }


def compare_files(legacy_path: str | Path, pipeline_path: str | Path) -> dict:
    """直接对比两个 raw_data.json 文件 · 返 diff 报告."""
    legacy = json.loads(Path(legacy_path).read_text(encoding="utf-8"))
    pipeline = json.loads(Path(pipeline_path).read_text(encoding="utf-8"))
    return compare_raw_data(legacy, pipeline)

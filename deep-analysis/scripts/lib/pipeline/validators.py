"""统一空值约定 · 根绝 v2.15.1 "0 vs None vs '—'" 类 bug.

**历史教训**：fetch_fund_holders 在 stats 空时用 `stats.get("return_5y", 0)` 写 0 · render 端
`m.get("return_5y") or 0` 把 None 当 0 ·导致报告里 15+ 张 fund-card 显示 "5Y +0.0%" 假数据。

**本模块约定**：
- 缺失值一律用 `None` · 禁止用 `0` / `"—"` / `""` 表示"没抓到"
- fetcher 内部可以用任意值，但 **落盘到 DimResult.data 前必须过一遍 `normalize_empty`**
- render 端用 `is_empty_value()` 判断 · 不要自己 `or 0` fallback
"""
from __future__ import annotations

from typing import Any

from .schema import DimResult, FetcherSpec, Quality


# 明确的"空"语义值 · fetcher 返这些都当缺失
EMPTY_SENTINELS = (None, "", "—", "-", "n/a", "N/A", "无数据", "暂无", "null", "NaN")
EMPTY_COLLECTIONS = ((), [], {}, set())


def is_empty_value(v: Any) -> bool:
    """标准空值判定 · 所有 render / validator 都用这个.

    包括：None / "" / "—" / "-" / "n/a" / "暂无" / 空容器 / 只含 whitespace 的字符串
    **不包括**：数值 0（0 是有效值 · 除非字段语义明确"0 = 缺失"，由 fetcher 决定转 None）
    """
    if v is None:
        return True
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return True
        return s in EMPTY_SENTINELS
    if isinstance(v, (list, tuple, set, dict)) and len(v) == 0:
        return True
    return False


def is_data_gap(data: dict, field_name: str) -> bool:
    """字段在 data 里缺失（不存在 or 值为空）."""
    if field_name not in data:
        return True
    return is_empty_value(data[field_name])


def normalize_empty(value: Any) -> Any:
    """把任何 empty sentinel 规约为 None · fetcher 落盘前过这一遍."""
    if is_empty_value(value):
        return None
    return value


def normalize_data(data: dict, keep_zero_fields: set[str] = None) -> dict:
    """规约整个 data dict · 所有 empty sentinel → None.

    `keep_zero_fields`: 某些字段语义上 0 也要保留（如 `default_days`、`holding_quarters`）
    """
    keep_zero_fields = keep_zero_fields or set()
    out = {}
    for k, v in data.items():
        if k in keep_zero_fields:
            out[k] = v
            continue
        out[k] = normalize_empty(v)
    return out


def validate_result(result: DimResult, spec: FetcherSpec) -> DimResult:
    """根据 spec 校验 result · 自动填 data_gaps · 推断 Quality.

    逻辑：
    - 所有 required 都有实测值 + optional 全有 = FULL
    - required 齐但 optional 部分缺 = PARTIAL
    - required 部分或全部缺 = MISSING / PARTIAL（看 optional 情况）
    - 已标记 ERROR 不变
    """
    if result.quality == Quality.ERROR:
        return result  # 错误状态不动

    data = result.data
    missing_required = [f for f in spec.required_fields if is_data_gap(data, f)]
    missing_optional = [f for f in spec.optional_fields if is_data_gap(data, f)]

    result.data_gaps = missing_required + missing_optional

    if not missing_required and not missing_optional:
        result.quality = Quality.FULL
    elif not missing_required:
        result.quality = Quality.PARTIAL
    elif missing_required and (len(missing_required) == len(spec.required_fields)):
        result.quality = Quality.MISSING
    else:
        result.quality = Quality.PARTIAL

    return result


def quality_score(result: DimResult, spec: FetcherSpec) -> float:
    """数据完整度百分比 · 0.0-1.0."""
    all_fields = spec.required_fields + spec.optional_fields
    if not all_fields:
        return 1.0 if result.quality == Quality.FULL else 0.0
    filled = sum(1 for f in all_fields if not is_data_gap(result.data, f))
    return filled / len(all_fields)

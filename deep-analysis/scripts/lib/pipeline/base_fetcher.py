"""抽象 BaseFetcher · 所有新 fetcher 继承 · 逐步迁移 22 个老 fetcher.

设计原则（对应 v2.15.1 教训）：
1. fetcher.fetch() 永远返 DimResult · 不是裸 dict
2. fetcher.spec 声明 required / optional / top_level 字段 · validator 自动判 quality
3. 异常一律 catch · 返 DimResult.error_result() · 永不 raise 出去
4. 支持 cache 装饰器 · 默认 1h TTL · 可按 spec 配置
5. 子类只实现 `_fetch_raw()` → dict · 框架包揽 normalize + validate + error handling
"""
from __future__ import annotations

import time
import traceback
from abc import ABC, abstractmethod
from typing import Any

from .schema import DimResult, FetcherSpec, Quality
from .validators import normalize_data, validate_result


class BaseFetcher(ABC):
    """Fetcher 基类 · 子类必填 spec + _fetch_raw()."""

    spec: FetcherSpec  # 子类必须声明

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "spec"):
            raise TypeError(f"{cls.__name__} 必须声明 `spec: FetcherSpec`")
        if not isinstance(cls.spec, FetcherSpec):
            raise TypeError(f"{cls.__name__}.spec 必须是 FetcherSpec 实例")

    @abstractmethod
    def _fetch_raw(self, ticker: Any) -> dict:
        """子类实现真正的抓取逻辑 · 返裸 dict · 允许任意空值（None/""/"—"）.

        框架会自动：
        - normalize 所有空值 → None
        - 按 spec 校验 data_gaps / quality
        - catch 异常 → DimResult.error_result
        """
        raise NotImplementedError

    # 子类可覆盖：哪些字段语义上"0 也算有效值"不应规约为 None
    keep_zero_fields: set[str] = set()

    # 子类可覆盖：要写到 raw_data.json 顶层的字段（如 fund_managers）
    # 注意：也要在 self.spec.top_level_fields 声明
    def extract_top_level(self, data: dict) -> dict:
        """子类覆盖以挑出要放 raw 顶层的字段."""
        return {k: data.get(k) for k in self.spec.top_level_fields if k in data}

    # ─── 主入口 ─────────────────────────────────────────────

    def fetch(self, ticker: Any) -> DimResult:
        """顶层入口 · 子类不覆盖 · 框架包揽所有 boilerplate."""
        t0 = time.time()
        try:
            raw_data = self._fetch_raw(ticker)
        except Exception as e:
            tb = traceback.format_exc()[:300]
            return DimResult.error_result(
                dim_key=self.spec.dim_key,
                error=f"{type(e).__name__}: {str(e)[:100]}",
                source=_first_source(self.spec),
            )

        if not isinstance(raw_data, dict):
            return DimResult.error_result(
                dim_key=self.spec.dim_key,
                error=f"fetch returned {type(raw_data).__name__}, expected dict",
                source=_first_source(self.spec),
            )

        # Normalize · 空值 → None
        normalized = normalize_data(raw_data, keep_zero_fields=self.keep_zero_fields)

        # 构造 result
        top_level = self.extract_top_level(normalized)
        result = DimResult(
            dim_key=self.spec.dim_key,
            data={k: v for k, v in normalized.items() if k not in top_level},
            source=_first_source(self.spec),
            quality=Quality.MISSING,  # validator 会改
            top_level_fields=top_level,
            latency_ms=int((time.time() - t0) * 1000),
        )

        # 根据 spec 校验 · 自动填 data_gaps + quality
        return validate_result(result, self.spec)


def _first_source(spec: FetcherSpec) -> str:
    """取 spec.sources 第一个作为 source · 为空返 'unknown'."""
    return spec.sources[0] if spec.sources else "unknown"

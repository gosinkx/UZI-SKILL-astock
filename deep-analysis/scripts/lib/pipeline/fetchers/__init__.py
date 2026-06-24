"""Fetcher adapters · 22 个 legacy fetcher 的 BaseFetcher 包装.

Phase 2 策略：**adapter pattern · 不动老代码**
- 每个 adapter 内部调 `fetch_X.main(...)` · 把老 dict 结果包成 DimResult
- FetcherSpec 声明 required/optional/top_level 字段 · validator 自动判 quality
- 这让 22 fetcher 统一了接口 · 不用一次性重写 fetch 逻辑（高风险）
- 稳定后未来 session 可按 MIGRATION.md 把每个老 fetcher 的内部逻辑挪进 _fetch_raw

用法：
    from lib.pipeline.fetchers import get_fetcher
    f = get_fetcher("0_basic")
    result = f.fetch(ticker_info)  # → DimResult
"""
from .registry import get_fetcher, list_fetchers, FETCHER_REGISTRY

__all__ = ["get_fetcher", "list_fetchers", "FETCHER_REGISTRY"]

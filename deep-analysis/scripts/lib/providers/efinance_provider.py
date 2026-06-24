"""Efinance provider · 0 key · akshare 的并行冗余.

Efinance (https://github.com/Micro-sheep/efinance) 内部从东财、同花顺、新浪
等多源爬虫聚合，国内直连稳定。提供 A/港/美 股 + ETF + 基金 + 可转债 全覆盖。

安装：pip install efinance
零 API key 要求。
"""
from __future__ import annotations

from . import Provider, register, ProviderError

try:
    import efinance as ef  # type: ignore
    _EF_OK = True
except ImportError:
    ef = None
    _EF_OK = False


class _EfinanceProvider:
    name = "efinance"
    requires_key = False
    markets = ("A", "H", "U")

    def is_available(self) -> bool:
        return _EF_OK

    def fetch_basic_a(self, code: str) -> dict:
        """A 股基本信息 + 最新行情（走东财爬虫）."""
        if not _EF_OK:
            raise ProviderError("efinance 未安装")
        try:
            # efinance.stock.get_base_info 返回 DataFrame（code/name/行业/市盈率等）
            df = ef.stock.get_base_info(code)
            if df is None or (hasattr(df, 'empty') and df.empty):
                raise ProviderError("empty response")
            if hasattr(df, 'to_dict'):
                rec = df.to_dict("records")[0] if not df.empty else {}
            else:
                rec = dict(df)
            return {"ok": True, "raw": rec}
        except Exception as e:
            raise ProviderError(f"efinance.get_base_info: {e}")

    def fetch_kline(self, code: str, market: str = "A", days: int = 500) -> list[dict]:
        """K 线 · efinance 支持 A/港/美/ETF/基金 一致接口."""
        if not _EF_OK:
            raise ProviderError("efinance 未安装")
        try:
            df = ef.stock.get_quote_history(code)
            if df is None or df.empty:
                raise ProviderError("empty kline")
            return df.tail(days).to_dict("records")
        except Exception as e:
            raise ProviderError(f"efinance.get_quote_history: {e}")

    def fetch_realtime_quote(self, code: str) -> dict:
        """实时行情快照."""
        if not _EF_OK:
            raise ProviderError("efinance 未安装")
        try:
            df = ef.stock.get_realtime_quotes(fs=code) if hasattr(ef.stock, "get_realtime_quotes") else None
            if df is None or df.empty:
                raise ProviderError("empty realtime")
            return df.to_dict("records")[0]
        except Exception as e:
            raise ProviderError(f"efinance realtime: {e}")

    def fetch_fund_holders(self, code: str) -> list[dict]:
        """基金持仓（哪些基金持有本股）· 作为 akshare 的冗余."""
        if not _EF_OK:
            raise ProviderError("efinance 未安装")
        try:
            # efinance 有 fund.get_inverst_position，是 基金 → 持仓
            # 反查 "持有本股的基金" 需要反向用东财 API（efinance 不直接提供）
            # 这里只作 akshare stock_fund_stock_holder 失败时的 fallback 点位
            raise ProviderError("efinance 不直接提供股票→基金反查，跳过")
        except Exception as e:
            raise ProviderError(str(e))


register(_EfinanceProvider())

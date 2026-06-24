"""AkShare provider · 现有默认主源的正式封装."""
from __future__ import annotations

from . import Provider, register, ProviderError

try:
    import akshare as ak
    _AK_OK = True
except ImportError:
    ak = None
    _AK_OK = False


class _AkshareProvider:
    name = "akshare"
    requires_key = False
    markets = ("A", "H", "U")

    def is_available(self) -> bool:
        return _AK_OK

    # === 不同维度的统一接口 ===
    # fetch_basic / fetch_financials 等 wave1-2 fetcher 可直接调

    def fetch_financials_a(self, code: str) -> dict:
        if not _AK_OK:
            raise ProviderError("akshare 未安装")
        try:
            df = ak.stock_financial_abstract(symbol=code)
            return {"ok": True, "raw": df.to_dict("records") if df is not None else []}
        except Exception as e:
            raise ProviderError(f"akshare.stock_financial_abstract: {e}")

    def fetch_kline_a(self, code: str, period: str = "daily", start: str = "20200101") -> list[dict]:
        if not _AK_OK:
            raise ProviderError("akshare 未安装")
        try:
            df = ak.stock_zh_a_hist(symbol=code, period=period, start_date=start, adjust="qfq")
            return df.to_dict("records") if df is not None else []
        except Exception as e:
            raise ProviderError(f"akshare.stock_zh_a_hist: {e}")


register(_AkshareProvider())

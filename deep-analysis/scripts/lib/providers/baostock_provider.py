"""BaoStock provider · 官方开源 · 0 key · A 股为主.

目前已在 data_sources._kline_a_share_chain 里作 fallback 用。本 provider
把它正式化，让 financials / 指标 也能通过 chain 调到。

BaoStock (http://baostock.com) 完全免费，需要 login()/logout()。
"""
from __future__ import annotations

from . import Provider, register, ProviderError

try:
    import baostock as bs  # type: ignore
    _BS_OK = True
except ImportError:
    bs = None
    _BS_OK = False


class _BaostockProvider:
    name = "baostock"
    requires_key = False
    markets = ("A",)

    _logged_in = False

    def is_available(self) -> bool:
        return _BS_OK

    def _ensure_login(self) -> None:
        if self._logged_in or not _BS_OK:
            return
        lg = bs.login()
        if lg.error_code != "0":
            raise ProviderError(f"baostock login: {lg.error_code} {lg.error_msg}")
        self._logged_in = True

    def _bs_code(self, code: str) -> str:
        """600519 → sh.600519 / 000001 → sz.000001."""
        code6 = code.split(".")[0].zfill(6)
        prefix = "sh." if code6.startswith(("60", "68", "90", "50", "51", "52", "56", "58", "10", "11")) else "sz."
        return prefix + code6

    def fetch_financials_a(self, code: str, years: int = 5) -> dict:
        """利润表关键字段 · query_profit_data."""
        if not _BS_OK:
            raise ProviderError("baostock 未安装")
        try:
            self._ensure_login()
            from datetime import datetime
            bs_code = self._bs_code(code)
            current_year = datetime.now().year
            results = []
            for y in range(current_year - years, current_year + 1):
                for q in range(1, 5):
                    rs = bs.query_profit_data(code=bs_code, year=y, quarter=q)
                    while rs.error_code == "0" and rs.next():
                        results.append(rs.get_row_data())
            return {"ok": True, "raw": results, "fields": ["code", "pubDate", "statDate",
                                                            "roeAvg", "npMargin", "gpMargin",
                                                            "netProfit", "epsTTM", "MBRevenue"]}
        except Exception as e:
            raise ProviderError(f"baostock.profit_data: {e}")

    def fetch_kline_a(self, code: str, start: str = "2020-01-01") -> list[dict]:
        """K 线 · query_history_k_data_plus."""
        if not _BS_OK:
            raise ProviderError("baostock 未安装")
        try:
            self._ensure_login()
            bs_code = self._bs_code(code)
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume,amount,turn,pctChg",
                start_date=start,
                frequency="d",
                adjustflag="2",  # 前复权
            )
            rows = []
            while rs.error_code == "0" and rs.next():
                row = rs.get_row_data()
                rows.append({
                    "date": row[0],
                    "open": float(row[1] or 0),
                    "high": float(row[2] or 0),
                    "low": float(row[3] or 0),
                    "close": float(row[4] or 0),
                    "volume": float(row[5] or 0),
                    "amount": float(row[6] or 0),
                    "turn": float(row[7] or 0),
                    "pct_chg": float(row[8] or 0),
                })
            return rows
        except Exception as e:
            raise ProviderError(f"baostock.kline: {e}")


register(_BaostockProvider())

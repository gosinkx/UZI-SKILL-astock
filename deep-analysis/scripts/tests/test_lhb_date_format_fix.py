"""Regression test · LHB 数据抓取修复.

Background (2026-04-25 用户在 002361 神剑股份 测龙虎榜功能时发现):
- akshare 1.18+ 已不接受 `stock_lhb_stock_detail_em(symbol=..., date="近一月")`
  这种字符串参数，会触发 ``TypeError: 'NoneType' object is not subscriptable``.
- 老实现 ``except Exception: return []`` 静默吞掉异常，导致所有股票
  ``lhb_count_30d=0`` / ``matched_youzi=[]`` / ``inst_vs_youzi`` 全 0.
- 直观影响：lhb-analyzer / deep-analysis 龙虎榜模块**永远跑不出数据**.

修复策略：
1. 用 ``stock_lhb_stock_detail_date_em`` 拿该股所有历史上榜日.
2. 按 ``days`` 范围过滤.
3. 逐日调 ``stock_lhb_stock_detail_em(symbol, date=YYYYMMDD)``.
4. 统一列名 ``交易营业部名称 → 营业部名称`` 让下游消费者无改动.

All tests mock network calls — zero real network dependency.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))


def _mk_dates_df(days_ago_list: list[int]) -> pd.DataFrame:
    """Mock the dates df returned by ``stock_lhb_stock_detail_date_em``."""
    base = datetime.now()
    return pd.DataFrame(
        [
            {
                "序号": i + 1,
                "股票代码": "002361",
                "交易日": (base - timedelta(days=d)).strftime("%Y-%m-%d"),
            }
            for i, d in enumerate(days_ago_list)
        ]
    )


def _mk_seat_df(rows: list[tuple[str, float, float]]) -> pd.DataFrame:
    """Mock per-date seat df returned by ``stock_lhb_stock_detail_em``."""
    return pd.DataFrame(
        [
            {
                "序号": i + 1,
                "交易营业部名称": seat,  # legacy column name from akshare
                "买入金额": buy,
                "卖出金额": sell,
                "净额": buy - sell,
                "类型": "日换手率达到20%的前5只证券",
            }
            for i, (seat, buy, sell) in enumerate(rows)
        ]
    )


# ─── Bug 1 · 老实现遇到新 akshare 必然返回空 ────────────────────────

def test_old_string_date_arg_returns_none_in_modern_akshare():
    """复现：``date="近一月"`` 在 akshare 1.18+ 触发 TypeError."""
    from lib import data_sources as ds
    from lib.market_router import parse_ticker

    ti = parse_ticker("002361")

    def _broken_detail_em(symbol, date):
        if date in ("近一月", "近三月"):
            raise TypeError("'NoneType' object is not subscriptable")
        # YYYYMMDD path 才返回数据
        return _mk_seat_df([("机构专用", 1e8, 5e7)])

    with patch.object(ds.ak, "stock_lhb_stock_detail_em", side_effect=_broken_detail_em), \
         patch.object(ds.ak, "stock_lhb_stock_detail_date_em",
                      return_value=_mk_dates_df([1, 5, 15])):
        ds.fetch_lhb_recent.cache_clear() if hasattr(ds.fetch_lhb_recent, "cache_clear") else None
        records = ds._fetch_lhb_impl(ti, days=30)
        # 修复后应该走 YYYYMMDD 路径，拿到 3 条
        assert len(records) == 3, f"expected 3 records via YYYYMMDD path, got {len(records)}"


# ─── Bug 2 · days 范围过滤正确 ────────────────────────────────────

def test_days_window_filters_old_dates():
    """45 天前的上榜日不应进入 days=30 的结果."""
    from lib import data_sources as ds
    from lib.market_router import parse_ticker

    ti = parse_ticker("002361")
    # 3 个日期：1 天前、20 天前、45 天前
    dates_df = _mk_dates_df([1, 20, 45])
    seat_df = _mk_seat_df([("机构专用", 1e8, 5e7)])

    with patch.object(ds.ak, "stock_lhb_stock_detail_date_em", return_value=dates_df), \
         patch.object(ds.ak, "stock_lhb_stock_detail_em", return_value=seat_df) as m_detail:
        records = ds._fetch_lhb_impl(ti, days=30)
        # 1 + 20 天的 2 个进 30 天窗口；45 天那个不进
        assert m_detail.call_count == 2, \
            f"expected 2 date-level calls (1d & 20d), got {m_detail.call_count}"
        assert len(records) == 2


# ─── Bug 3 · 列名归一化 ────────────────────────────────────────────

def test_seat_column_renamed_for_downstream():
    """``交易营业部名称`` 必须重命名为 ``营业部名称`` 让 split_inst_vs_youzi 工作."""
    from lib import data_sources as ds
    from lib.market_router import parse_ticker

    ti = parse_ticker("002361")
    dates_df = _mk_dates_df([1])
    seat_df = _mk_seat_df([("机构专用", 1e8, 5e7), ("华泰证券深圳深南大道", 5e7, 8e7)])

    with patch.object(ds.ak, "stock_lhb_stock_detail_date_em", return_value=dates_df), \
         patch.object(ds.ak, "stock_lhb_stock_detail_em", return_value=seat_df):
        records = ds._fetch_lhb_impl(ti, days=30)

    assert len(records) == 2
    for r in records:
        assert "营业部名称" in r, f"missing 营业部名称, has: {list(r.keys())}"
        assert r["营业部名称"] in ("机构专用", "华泰证券深圳深南大道")


# ─── Bug 4 · 日期 column 含时间戳的鲁棒处理 ────────────────────────

def test_handles_timestamp_format_in_dates_column():
    """有些 akshare 版本 ``交易日`` 是 ``YYYY-MM-DD HH:MM:SS``，要能截前 10 位."""
    from lib import data_sources as ds
    from lib.market_router import parse_ticker

    ti = parse_ticker("002361")
    base = datetime.now()
    dates_df = pd.DataFrame(
        [{"序号": 1, "股票代码": "002361",
          "交易日": (base - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")}]
    )

    captured: dict = {}

    def _capture_date(symbol, date):
        captured["date"] = date
        return _mk_seat_df([("机构专用", 1e8, 5e7)])

    with patch.object(ds.ak, "stock_lhb_stock_detail_date_em", return_value=dates_df), \
         patch.object(ds.ak, "stock_lhb_stock_detail_em", side_effect=_capture_date):
        records = ds._fetch_lhb_impl(ti, days=30)

    assert len(records) == 1
    # 必须是 8 位 YYYYMMDD，不是 19 位 timestamp
    assert len(captured["date"]) == 8, f"expected YYYYMMDD, got {captured['date']}"


# ─── Bug 5 · 空 dates_df 静默返回 ─────────────────────────────────

def test_empty_dates_df_returns_empty():
    """该股从未上过榜（如冷门票）— 不报错，返回 []."""
    from lib import data_sources as ds
    from lib.market_router import parse_ticker

    ti = parse_ticker("688027")  # 国盾量子，30 天没上榜
    with patch.object(ds.ak, "stock_lhb_stock_detail_date_em",
                      return_value=pd.DataFrame()):
        records = ds._fetch_lhb_impl(ti, days=30)
    assert records == []


# ─── Bug 6 · 单日抓取异常不应中断整个 loop ───────────────────────

def test_per_date_exception_isolated():
    """某一天 detail_em 报错时 skip 该日，不让其他日的数据丢失."""
    from lib import data_sources as ds
    from lib.market_router import parse_ticker

    ti = parse_ticker("002361")
    dates_df = _mk_dates_df([1, 3, 5])
    call_count = {"n": 0}

    def _flaky(symbol, date):
        call_count["n"] += 1
        if call_count["n"] == 2:  # 第 2 次调用炸
            raise ValueError("network glitch")
        return _mk_seat_df([("机构专用", 1e8, 5e7)])

    with patch.object(ds.ak, "stock_lhb_stock_detail_date_em", return_value=dates_df), \
         patch.object(ds.ak, "stock_lhb_stock_detail_em", side_effect=_flaky):
        records = ds._fetch_lhb_impl(ti, days=30)

    # 3 个日期，第 2 个炸了，应拿到 2 条
    assert len(records) == 2

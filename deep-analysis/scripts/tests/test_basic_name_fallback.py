#!/usr/bin/env python3
"""Regression checks for A-share field-level basic fallback.

UZI000 exposed a gap where Eastmoney direct fallback could fill part of
0_basic, while other critical fields stayed empty. Legacy fallback gates were
mostly source-level or price/PE/PB gated, so partial success could still leave
report-critical gaps such as name. These tests require the post-processing gate
to patch missing fields without clobbering already fetched values.
"""

from lib.data_sources import (
    _append_fallback_snap,
    _ensure_a_share_basic_fields,
    _merge_missing_basic_fields,
)
from lib.market_router import parse_ticker


def _em_direct_like_out():
    return {
        "code": "600519.SH",
        "price": 1351.0,
        "pe_ttm": 15.53,
        "pb": 6.29,
        "market_cap": "16918.2亿",
        "market_cap_raw": 1691817060465.0,
        "industry": "白酒",
        "_fallback_snap": "em-direct",
    }


def test_ensure_a_share_basic_fields_uses_tencent_when_name_missing(monkeypatch):
    ti = parse_ticker("600519.SH")
    out = _em_direct_like_out()

    def fake_qt(market, code_raw):
        assert market == "A"
        assert code_raw == "600519"
        return {"name": "贵州茅台", "price": 1350.69, "pe_ttm": 20.45, "pb": 6.24}

    monkeypatch.setattr("lib.data_sources._fetch_price_tencent_qt", fake_qt)

    fixed = _ensure_a_share_basic_fields(out, ti)

    assert fixed["name"] == "贵州茅台"
    assert "field:tencent_qt" in fixed["_fallback_snap"]
    # Existing populated quote fields should not be overwritten by field repair.
    assert fixed["price"] == 1351.0
    assert fixed["pe_ttm"] == 15.53
    assert fixed["pb"] == 6.29


def test_ensure_a_share_basic_fields_repairs_market_cap_from_tencent(monkeypatch):
    ti = parse_ticker("600519.SH")
    out = {**_em_direct_like_out(), "name": "贵州茅台", "listed_date": "2001-08-27"}
    out.pop("market_cap")
    out.pop("market_cap_raw")

    def fake_qt(_market, _code_raw):
        return {"market_cap": "16968.39亿", "market_cap_raw": 1696839000000.0}

    monkeypatch.setattr("lib.data_sources._fetch_price_tencent_qt", fake_qt)

    fixed = _ensure_a_share_basic_fields(out, ti)

    assert fixed["market_cap"] == "16968.39亿"
    assert fixed["market_cap_raw"] == 1696839000000.0
    assert "field:tencent_qt" in fixed["_fallback_snap"]


def test_ensure_a_share_basic_fields_short_circuits_when_required_fields_exist(monkeypatch):
    ti = parse_ticker("600519.SH")
    out = {**_em_direct_like_out(), "name": "已有名称", "listed_date": "2001-08-27"}

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("field fallback should not be called when all critical fields exist")

    monkeypatch.setattr("lib.data_sources._fetch_price_tencent_qt", fail_if_called)

    fixed = _ensure_a_share_basic_fields(out, ti)

    assert fixed["name"] == "已有名称"
    assert fixed["_fallback_snap"] == "em-direct"


def test_field_gate_uses_baostock_after_tencent_failure(monkeypatch):
    ti = parse_ticker("600519.SH")
    out = {"code": "600519.SH", "industry": "白酒", "_fallback_snap": "em-direct"}

    def fake_qt(_market, _code_raw):
        raise RuntimeError("tencent unavailable")

    def fake_baostock(_ti, *, include_quote=True):
        assert include_quote is True
        return {
            "name": "贵州茅台",
            "price": 1351.0,
            "pe_ttm": 20.4,
            "pb": 7.15,
            "listed_date": "2001-08-27",
        }

    monkeypatch.setattr("lib.data_sources._fetch_price_tencent_qt", fake_qt)
    monkeypatch.setattr("lib.data_sources._fetch_a_share_basic_from_baostock", fake_baostock)

    fixed = _ensure_a_share_basic_fields(out, ti)

    assert fixed["name"] == "贵州茅台"
    assert fixed["price"] == 1351.0
    assert fixed["pe_ttm"] == 20.4
    assert fixed["pb"] == 7.15
    assert fixed["listed_date"] == "2001-08-27"
    assert "field:baostock" in fixed["_fallback_snap"]
    assert "_field_tencent_err" in fixed


def test_merge_missing_basic_fields_never_overwrites_existing_values():
    out = {"price": 10.0, "pe_ttm": 8.0, "_fallback_snap": "primary"}
    source = {"price": 11.0, "pe_ttm": 9.0, "pb": 1.2, "name": "测试股份"}

    changed = _merge_missing_basic_fields(out, source, "fallback", fields=("price", "pe_ttm", "pb", "name"))

    assert changed is True
    assert out["price"] == 10.0
    assert out["pe_ttm"] == 8.0
    assert out["pb"] == 1.2
    assert out["name"] == "测试股份"
    assert out["_fallback_snap"] == "primary+fallback"


def test_append_fallback_snap_deduplicates_markers():
    out = {"_fallback_snap": "em-direct+field:tencent_qt"}

    _append_fallback_snap(out, "field:tencent_qt")
    _append_fallback_snap(out, "field:ak_code_name")

    assert out["_fallback_snap"] == "em-direct+field:tencent_qt+field:ak_code_name"

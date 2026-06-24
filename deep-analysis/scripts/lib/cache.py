"""Tiered JSON cache for fetcher scripts.

TTL is differentiated by data volatility:
- Real-time quote (price/change_pct):        60s
- Intraday K-line / capital flow / sentiment: 5 min
- Daily aggregates (LHB, north-bound):       2 hours
- News:                                       1 hour
- Quarterly financials / valuation history:  24 hours
- Static metadata (industry, name):          7 days

Set env STOCK_NO_CACHE=1 to bypass cache entirely (force refresh).
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Callable

# Tiered TTL constants (seconds)
TTL_REALTIME    = 60          # 1 minute — price snapshot
TTL_INTRADAY    = 5 * 60      # 5 min — kline, fund flow, sentiment hot rank
TTL_HOURLY      = 60 * 60     # 1 hour — news
TTL_DAILY       = 2 * 60 * 60 # 2 hours — LHB, northbound, margin (after market close)
TTL_QUARTERLY   = 24 * 60 * 60       # 24 hours — financials, research reports
TTL_STATIC      = 7 * 24 * 60 * 60   # 7 days — industry classification

# Default TTL when caller doesn't specify
CACHE_TTL_SECONDS = TTL_INTRADAY

CACHE_ROOT = Path(".cache")
NO_CACHE = os.environ.get("STOCK_NO_CACHE") == "1"


def _cache_path(ticker: str, key: str) -> Path:
    h = hashlib.md5(key.encode("utf-8")).hexdigest()[:12]
    safe_key = "".join(c if c.isalnum() or c in "._-" else "_" for c in key)[:60]
    return CACHE_ROOT / ticker / "api_cache" / f"{safe_key}__{h}.json"


def cached(ticker: str, key: str, fetch_fn: Callable[[], Any], ttl: int = CACHE_TTL_SECONDS) -> Any:
    """Return cached value if fresh, else call fetch_fn and store.
    Set STOCK_NO_CACHE=1 in the environment to force refresh.
    """
    path = _cache_path(ticker, key)
    now = time.time()

    if not NO_CACHE and path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if now - payload.get("_cached_at", 0) < ttl:
                return payload["data"]
        except (json.JSONDecodeError, KeyError):
            pass

    data = fetch_fn()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"_cached_at": now, "data": data, "_ttl": ttl}, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return data


def market_status() -> dict:
    """Return current A-share market status: open/closed + next event.
    Used to label data freshness in the report header.
    """
    from datetime import datetime, time as dt_time
    now = datetime.now()
    weekday = now.weekday()  # 0=Mon, 6=Sun
    t = now.time()

    if weekday >= 5:
        return {"is_open": False, "label": "已收盘 (周末)", "now": now.isoformat(timespec="seconds")}

    morning_open = dt_time(9, 30)
    morning_close = dt_time(11, 30)
    afternoon_open = dt_time(13, 0)
    afternoon_close = dt_time(15, 0)

    if morning_open <= t < morning_close or afternoon_open <= t < afternoon_close:
        return {"is_open": True, "label": "交易中", "now": now.isoformat(timespec="seconds")}
    if morning_close <= t < afternoon_open:
        return {"is_open": False, "label": "午间休市", "now": now.isoformat(timespec="seconds")}
    if t < morning_open:
        return {"is_open": False, "label": "未开盘", "now": now.isoformat(timespec="seconds")}
    return {"is_open": False, "label": "已收盘", "now": now.isoformat(timespec="seconds")}


def write_task_output(ticker: str, task_name: str, data: dict) -> Path:
    """Write a task's final JSON to .cache/{ticker}/{task_name}.json"""
    path = CACHE_ROOT / ticker / f"{task_name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def read_task_output(ticker: str, task_name: str) -> dict | None:
    path = CACHE_ROOT / ticker / f"{task_name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def require_task_output(ticker: str, task_name: str) -> dict:
    """Hard gate: raise if previous task hasn't run."""
    data = read_task_output(ticker, task_name)
    if data is None:
        raise RuntimeError(
            f"Gate failed: {task_name}.json missing for {ticker}. "
            f"Run the previous task first."
        )
    return data

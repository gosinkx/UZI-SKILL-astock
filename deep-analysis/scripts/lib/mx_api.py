"""Thin client for 东方财富妙想 Skills Hub API (`mkapi2.dfcfs.com/finskillshub`).

This is an OFFICIAL, authenticated data source with far better stability than
scraping `push2.eastmoney.com` (which is commonly blocked in 2026 Mainland
networks). Requires a free API key from https://dl.dfcfs.com/m/itc4 exposed as
the env var `MX_APIKEY`.

Usage:
    from lib.mx_api import MXClient
    client = MXClient()                              # reads MX_APIKEY from env
    if client.available:
        hits = client.resolve_entity("北部湾港")
        snap = client.fetch_snapshot("000582")
    else:
        # fall back to xueqiu / akshare chain

Endpoints (header must carry `apikey: <MX_APIKEY>`):
    POST /finskillshub/api/claw/query        — natural-language financial data
    POST /finskillshub/api/claw/news-search  — news / announcements

All requests go through `lib.cache.cached` with a 30-minute TTL to cap spend.
"""
from __future__ import annotations

import os
import time
from typing import Any, Optional

from .cache import cached

try:
    import requests
except ImportError:
    requests = None


BASE = "https://mkapi2.dfcfs.com/finskillshub/api/claw"
QUERY_URL = f"{BASE}/query"
NEWS_URL = f"{BASE}/news-search"

_MX_TTL = 30 * 60  # 30 min — MX responses are semi-fresh, cache to cap quota


def _post(url: str, body: dict, api_key: str, timeout: int = 30, attempts: int = 2) -> dict:
    """POST with small retry. Returns parsed JSON or {'error': ...}."""
    if requests is None:
        return {"error": "requests library missing"}
    headers = {"Content-Type": "application/json", "apikey": api_key}
    last_err = None
    for i in range(attempts):
        try:
            r = requests.post(url, headers=headers, json=body, timeout=timeout)
            if r.status_code != 200:
                last_err = f"HTTP {r.status_code}: {r.text[:200]}"
                # 401/403: don't retry, key issue
                if r.status_code in (401, 403):
                    break
                time.sleep(1.0 * (i + 1))
                continue
            return r.json()
        except Exception as e:
            last_err = f"{type(e).__name__}: {str(e)[:200]}"
            time.sleep(1.0 * (i + 1))
    return {"error": last_err or "unknown"}


class MXClient:
    """Client for 妙想 Skills Hub. Safe to instantiate without a key — check `.available`."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MX_APIKEY") or ""
        self.available = bool(self.api_key)

    # ── Raw endpoints ─────────────────────────────────────────

    def query(self, tool_query: str) -> dict:
        """Natural-language query. Cached 30 min."""
        if not self.available:
            return {"error": "MX_APIKEY not set"}

        def _fetch():
            return _post(QUERY_URL, {"toolQuery": tool_query}, self.api_key)

        return cached("_global", f"mx_query__{tool_query[:80]}", _fetch, ttl=_MX_TTL)

    def news_search(self, query: str) -> dict:
        """News / announcement search. Cached 30 min."""
        if not self.available:
            return {"error": "MX_APIKEY not set"}

        def _fetch():
            return _post(NEWS_URL, {"query": query}, self.api_key)

        return cached("_global", f"mx_news__{query[:80]}", _fetch, ttl=_MX_TTL)

    # ── High-level helpers ────────────────────────────────────

    def resolve_entity(self, name: str) -> list[dict]:
        """Map a Chinese stock name (possibly with typo) to code candidates.

        Returns list of {"fullName", "secuCode", "entityType"}. Empty on failure.
        The MX NLP layer handles character-order typos gracefully.
        """
        if not self.available:
            return []
        result = self.query(f"{name} 股票代码 所属行业")
        return _extract_entity_tags(result)

    def fetch_snapshot(self, code_or_name: str) -> dict:
        """Best-effort snapshot (price / mcap / PE / PB / industry).

        Returns flat dict with whatever fields could be extracted; empty dict on failure.
        """
        if not self.available:
            return {}
        result = self.query(f"{code_or_name} 最新价 总市值 PE PB 所属行业 主营业务")
        return _extract_first_table_row(result)


# ═══════════════════════════════════════════════════════════════
# Response parsers
# ═══════════════════════════════════════════════════════════════

def _extract_entity_tags(result: dict) -> list[dict]:
    """Extract entity info from MX query response. Multi-source parse because
    the top-level `entityTagDTOList` is often empty for NLP-resolved queries —
    the actual code lives inside each `dataTableDTO.code` / `.entityName`.
    """
    import re

    if not isinstance(result, dict) or result.get("error"):
        return []
    if result.get("status") not in (0, None):
        return []
    data = result.get("data") or {}
    inner = data.get("data") or {}
    sr = inner.get("searchDataResultDTO") or {}

    out: list[dict] = []
    seen: set[str] = set()

    # Source 1: top-level entityTagDTOList (rare but authoritative when present)
    for t in sr.get("entityTagDTOList") or []:
        if not isinstance(t, dict):
            continue
        full_name = t.get("fullName") or t.get("shortName") or ""
        code = t.get("secuCode") or t.get("code") or ""
        etype = t.get("entityTypeName") or t.get("entityType") or ""
        if full_name and code and code not in seen:
            seen.add(code)
            out.append({"fullName": full_name, "secuCode": code, "entityType": etype})

    # Source 2: dataTableDTOList[].code / .entityName (MX NLP-resolved typical path)
    for dto in sr.get("dataTableDTOList") or []:
        if not isinstance(dto, dict):
            continue
        code = (dto.get("code") or "").strip()
        entity_name = (dto.get("entityName") or "").strip()
        if not code or code in seen:
            continue
        # entityName is "北部湾港(000582.SZ)" — strip parenthetical code to get clean name
        m = re.match(r"^(.+?)\s*[（(][^)）]+[)）]\s*$", entity_name)
        clean_name = m.group(1).strip() if m else entity_name
        seen.add(code)
        out.append({
            "fullName": clean_name,
            "secuCode": code,
            "entityType": dto.get("dataType", "") or "股票",
        })

    return out


def _extract_first_table_row(result: dict) -> dict:
    """Extract indicator→value map from the first dataTableDTO. Best-effort."""
    if not isinstance(result, dict) or result.get("error"):
        return {}
    data = result.get("data") or {}
    inner = data.get("data") or {}
    sr = inner.get("searchDataResultDTO") or {}
    dto_list = sr.get("dataTableDTOList") or []
    if not dto_list or not isinstance(dto_list[0], dict):
        return {}
    dto = dto_list[0]
    table = dto.get("table") or {}
    if not isinstance(table, dict):
        return {}
    name_map = dto.get("nameMap") or {}
    if isinstance(name_map, list):
        name_map = {str(i): v for i, v in enumerate(name_map)}
    headers = table.get("headName") or []

    out: dict[str, Any] = {"_mx_entity": (dto.get("entityName") or "")}
    for key, values in table.items():
        if key == "headName":
            continue
        label = name_map.get(key) or name_map.get(str(key)) or str(key)
        if isinstance(values, list) and values:
            # Take the most recent (last) value for snapshots; headName is date column.
            out[str(label)] = values[-1]
        else:
            out[str(label)] = values
    return out


if __name__ == "__main__":
    import json
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "北部湾港"
    c = MXClient()
    print(f"available: {c.available}")
    if not c.available:
        print("Set MX_APIKEY to test. See .env.example.")
        sys.exit(0)
    print(f"\n── resolve_entity('{q}') ──")
    print(json.dumps(c.resolve_entity(q), ensure_ascii=False, indent=2))
    print(f"\n── fetch_snapshot('{q}') ──")
    print(json.dumps(c.fetch_snapshot(q), ensure_ascii=False, indent=2))

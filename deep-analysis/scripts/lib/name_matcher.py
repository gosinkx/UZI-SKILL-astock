"""Fuzzy matching for Chinese stock names · zero-dependency.

Handles typo/character-order mistakes like "北部港湾" → "北部湾港" (000582.SZ).

Two-stage pipeline:
    1. Character-set Jaccard filter (fast; rules out >99% of the 5000-stock A-share universe)
    2. Levenshtein distance ranking on survivors (accurate; picks the right reorder)

A-share (code, name) index is loaded from akshare.stock_info_a_code_name() and cached
for 7 days (names rarely change). Caller passes a plain Chinese string; we return a list
of scored candidates.

Usage:
    from lib.name_matcher import fuzzy_match
    hits = fuzzy_match("北部港湾", top_k=5)
    # → [{"code": "000582", "name": "北部湾港", "distance": 1, "jaccard": 1.0}, ...]
"""
from __future__ import annotations

from typing import Any

from .cache import cached, TTL_STATIC

try:
    import akshare as ak
except ImportError:
    ak = None


# ═══════════════════════════════════════════════════════════════
# Primitive similarity metrics (pure stdlib)
# ═══════════════════════════════════════════════════════════════

def levenshtein(a: str, b: str) -> int:
    """Edit distance · classic two-row DP. O(len(a) * len(b)) time, O(len(b)) space."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr[j] = min(
                curr[j - 1] + 1,       # insert
                prev[j] + 1,           # delete
                prev[j - 1] + cost,    # substitute
            )
        prev = curr
    return prev[-1]


def char_set_jaccard(a: str, b: str) -> float:
    """Character-set Jaccard similarity (ignores ordering). 1.0 means same character multiset."""
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    union = sa | sb
    if not union:
        return 0.0
    return len(sa & sb) / len(union)


# ═══════════════════════════════════════════════════════════════
# A-share name index
# ═══════════════════════════════════════════════════════════════

def _build_index_raw() -> list[dict]:
    """Pull the full A-share (code, name) table via akshare. Raises if akshare unavailable."""
    if ak is None:
        return []
    # stock_info_a_code_name: ~5000 rows, ~100KB. Returns cols ['code', 'name'] (lowercase).
    df = ak.stock_info_a_code_name()
    if df is None or df.empty:
        return []
    # Robust to column naming variants.
    code_col = "code" if "code" in df.columns else df.columns[0]
    name_col = "name" if "name" in df.columns else df.columns[1]
    return [
        {"code": str(row[code_col]).zfill(6), "name": str(row[name_col])}
        for _, row in df.iterrows()
        if row[name_col]
    ]


def build_a_share_index() -> list[dict]:
    """Cached wrapper — index is static enough for 7-day TTL."""
    return cached("_global", "a_share_name_index", _build_index_raw, ttl=TTL_STATIC)


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════

def fuzzy_match(
    query: str,
    top_k: int = 5,
    max_distance: int = 2,
    min_jaccard: float = 0.6,
) -> list[dict]:
    """Find closest A-share names to `query`.

    Args:
        query: user input (Chinese name, possibly with character-order typo)
        top_k: return at most this many candidates
        max_distance: maximum allowed Levenshtein distance
        min_jaccard: pre-filter threshold (characters must overlap)

    Returns:
        list of {"code", "name", "distance", "jaccard"} sorted by (distance asc, jaccard desc).
        Empty list if index unavailable or no candidate within threshold.
    """
    query = query.strip()
    if not query:
        return []

    index = build_a_share_index()
    if not index:
        return []

    # Stage 1: cheap Jaccard pre-filter
    # Use a slightly looser threshold for 2-char queries (they can't overlap much).
    eff_jaccard = min_jaccard if len(query) >= 3 else 0.5
    shortlist: list[tuple[dict, float]] = []
    for entry in index:
        j = char_set_jaccard(query, entry["name"])
        if j >= eff_jaccard:
            shortlist.append((entry, j))

    if not shortlist:
        return []

    # Stage 2: Levenshtein ranking
    scored: list[dict] = []
    for entry, j in shortlist:
        d = levenshtein(query, entry["name"])
        if d <= max_distance:
            scored.append({
                "code": entry["code"],
                "name": entry["name"],
                "distance": d,
                "jaccard": round(j, 3),
            })

    scored.sort(key=lambda x: (x["distance"], -x["jaccard"]))
    return scored[:top_k]


if __name__ == "__main__":
    import json
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "北部港湾"
    hits = fuzzy_match(q)
    print(f"Query: {q}")
    print(json.dumps(hits, ensure_ascii=False, indent=2))

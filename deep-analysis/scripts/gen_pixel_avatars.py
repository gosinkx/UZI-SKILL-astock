"""Pre-generate 50 DiceBear pixel-art SVG avatars for the investor panel.

Run once at install or when adding new investors:
    python scripts/gen_pixel_avatars.py

Output: skills/deep-analysis/assets/avatars/{id}.svg

DiceBear v9 HTTP API (free, MIT, no key). Falls back to deterministic
hash-based identicon if offline. Pure stdlib — no requests dep.
"""
from __future__ import annotations

import hashlib
import io
import os
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# Inline INVESTORS so this script can run standalone without lib import.
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from lib.investor_db import INVESTORS  # noqa: E402

DICEBEAR_BASE = "https://api.dicebear.com/9.x/pixel-art/svg"
OUTPUT_DIR = HERE.parent / "assets" / "avatars"

# Force UTF-8 stdout on Windows GBK consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def fetch_one(seed: str, timeout: int = 12) -> str | None:
    # Light theme: use very light cream/warm tints so the pixel face stands out
    # on white cards without merging into the background.
    params = {
        "seed": seed,
        "size": "128",
        "backgroundColor": "fef3c7,d1fae5,cffafe,e0e7ff,fce7f3",
        "backgroundType": "solid",
        "scale": "90",
    }
    url = f"{DICEBEAR_BASE}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "stock-deep-analyzer/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status == 200:
                return r.read().decode("utf-8")
    except Exception as e:
        print(f"    ! dicebear failed for {seed}: {e}", file=sys.stderr)
    return None


def fallback_svg(seed: str) -> str:
    """Tiny offline identicon — colored grid based on seed hash. Deterministic."""
    h = hashlib.md5(seed.encode()).digest()
    hue = h[0] * 360 // 256
    sat = 60 + (h[1] % 30)
    cells = []
    for y in range(8):
        for x in range(4):
            if h[(y * 4 + x) % 16] & (1 << (x % 8)):
                color = f"hsl({hue}, {sat}%, 55%)"
                cells.append(f'<rect x="{x * 16}" y="{y * 16}" width="16" height="16" fill="{color}"/>')
                cells.append(f'<rect x="{(7 - x) * 16}" y="{y * 16}" width="16" height="16" fill="{color}"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
<rect width="128" height="128" fill="#0a0e17"/>
{"".join(cells)}
</svg>'''


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    success = fail = skip = 0
    for inv in INVESTORS:
        out = OUTPUT_DIR / f"{inv['id']}.svg"
        if out.exists() and out.stat().st_size > 100:
            skip += 1
            continue
        seed = inv.get("avatar_seed") or inv["id"]
        svg = fetch_one(seed)
        if svg is None:
            svg = fallback_svg(seed)
            fail += 1
            tag = "fallback"
        else:
            success += 1
            tag = "dicebear"
        out.write_text(svg, encoding="utf-8")
        print(f"  [ok] {inv['id']:<14} ({inv['name']:<10}) [{tag}]")
    print(f"\nDone. {success} from DiceBear, {fail} fallback, {skip} skipped (already exists). Total {len(INVESTORS)}.")
    print(f"Output: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Bundle a generated full-report.html into a single self-contained file.

Reads the report HTML, finds all `<img src="avatars/{id}.svg">` references,
and replaces them with inline data URIs. Output: full-report-standalone.html

Usage: python scripts/inline_assets.py {ticker}
"""
from __future__ import annotations

import base64
import re
import sys
from datetime import datetime
from pathlib import Path


def main(ticker: str) -> Path:
    date = datetime.now().strftime("%Y%m%d")
    report_dir = Path("reports") / f"{ticker}_{date}"
    if not report_dir.exists():
        # try any matching dir
        candidates = list(Path("reports").glob(f"{ticker}_*"))
        if not candidates:
            raise FileNotFoundError(f"No report dir for {ticker}")
        report_dir = sorted(candidates)[-1]

    html_path = report_dir / "full-report.html"
    if not html_path.exists():
        raise FileNotFoundError(f"{html_path} missing")

    avatars_dir = report_dir / "avatars"
    html = html_path.read_text(encoding="utf-8")

    def replace_img(match: re.Match) -> str:
        src = match.group(1)
        if not src.startswith("avatars/"):
            return match.group(0)
        avatar_name = src.split("/", 1)[1]
        avatar_path = avatars_dir / avatar_name
        if not avatar_path.exists():
            return match.group(0)
        svg_bytes = avatar_path.read_bytes()
        b64 = base64.b64encode(svg_bytes).decode("ascii")
        return f'src="data:image/svg+xml;base64,{b64}"'

    inlined = re.sub(r'src="(avatars/[^"]+)"', replace_img, html)
    out = report_dir / "full-report-standalone.html"
    out.write_text(inlined, encoding="utf-8")

    avatar_count = inlined.count("data:image/svg+xml;base64,")
    print(f"[ok] standalone report: {out}")
    print(f"     inlined {avatar_count} avatar refs")
    print(f"     size: {len(inlined):,} bytes ({len(inlined)//1024} KB)")
    return out


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "MOCK.SZ"
    main(ticker)

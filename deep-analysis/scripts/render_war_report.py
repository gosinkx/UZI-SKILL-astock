"""Render the 1920×1080 war-report PNG (微信群横图)."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from render_share_card import render  # noqa: E402


def main(ticker: str) -> None:
    """v2.6 · alias for stage2 import compatibility."""
    render(ticker, selector="#war-report", out_name="war-report.png", scale=2)


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "002273.SZ"
    main(ticker)

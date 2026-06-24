#!/usr/bin/env python3
"""v2.10 · Segmental Revenue Build-Up CLI.

两种用法：

  1. 生成骨架（agent 用）:
      python compute_segmental.py discover <ticker>
      → 写 .cache/<ticker>/segmental_skeleton.json
      → 打印 markdown 骨架给 agent 看

  2. 校验 agent 填完的模型:
      python compute_segmental.py validate <ticker>
      → 读 .cache/<ticker>/segmental_model.json
      → 输出 pass/fail + errors + warnings

Workflow:
  stage1 生成 raw_data.json
  → compute_segmental discover <ticker>   # 生成 skeleton
  → agent 读 skeleton，填入 drivers / thesis_tag / 3 情景 CAGR
  → agent 写 .cache/<ticker>/segmental_model.json
  → compute_segmental validate <ticker>   # 自查
  → 进 synthesis/HTML 报告
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))


def cmd_discover(ticker: str) -> int:
    from lib.cache import read_task_output, write_task_output
    from lib.segmental_model import discover_segments, render_skeleton_markdown

    raw = read_task_output(ticker, "raw_data")
    if not raw:
        print(f"❌ {ticker} raw_data.json 不存在 — 请先跑 stage1", file=sys.stderr)
        return 1

    skel = discover_segments(raw)
    skel_dict = skel.to_dict()
    write_task_output(ticker, "segmental_skeleton", skel_dict)

    md = render_skeleton_markdown(skel)
    print(md)
    print(f"\n→ 骨架 JSON 已写入: .cache/{ticker}/segmental_skeleton.json")
    print(f"→ Agent 下一步: 读此 JSON，填 segments[*].drivers / thesis_tag / bull_base_bear_growth_3y_cagr")
    print(f"→ 填完写回 .cache/{ticker}/segmental_model.json")
    print(f"→ 然后跑: python compute_segmental.py validate {ticker}")
    return 0


def cmd_validate(ticker: str) -> int:
    from lib.cache import read_task_output, write_task_output
    from lib.segmental_model import validate_model

    raw = read_task_output(ticker, "raw_data")
    if not raw:
        print(f"❌ {ticker} raw_data.json 不存在", file=sys.stderr)
        return 1
    filled = read_task_output(ticker, "segmental_model")
    if not filled:
        print(f"❌ {ticker} segmental_model.json 不存在 — agent 尚未填入", file=sys.stderr)
        return 1

    report = validate_model(filled, raw)
    write_task_output(ticker, "segmental_validation", report)

    print(f"{'✓' if report['passed'] else '✗'} Segmental Model Validation · {ticker}")
    summary = report.get("summary", {})
    if summary:
        print(f"  对账: sum={summary.get('sum_segments')} vs actual={summary.get('total_actual')} · gap={summary.get('reconciliation_gap_pct')}%")
        if "base_3y_total_growth_pct" in summary:
            print(f"  Base 情景 3 年总增速: {summary['base_3y_total_growth_pct']}%")
    if report.get("errors"):
        print("\n🔴 ERRORS:")
        for e in report["errors"]:
            print(f"  - {e}")
    if report.get("warnings"):
        print("\n🟡 WARNINGS:")
        for w in report["warnings"]:
            print(f"  - {w}")
    if report["passed"] and not report.get("warnings"):
        print("  全部通过 · 可进 synthesis/HTML")

    return 0 if report["passed"] else 1


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("discover", "validate"):
        print(__doc__, file=sys.stderr)
        sys.exit(64)
    cmd = sys.argv[1]
    ticker = sys.argv[2]
    sys.exit(cmd_discover(ticker) if cmd == "discover" else cmd_validate(ticker))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""v2.9 · Self-review CLI — agent 必须在 stage2 完成后、HTML 生成前运行。

用法:
    python review_stage_output.py <ticker>

    # exit 0 = critical_count == 0, 可以进 HTML
    # exit 1 = 有 critical issues, 必须先修
    # exit 2 = 只有 warning issues（HTML 仍可生成，但建议 ack）

产物:
    .cache/<ticker>/_review_issues.json   — 给 stage2 / agent 读
    stdout                                 — 人读摘要

设计原则:
    - agent 必须读 _review_issues.json，对每条 critical issue 执行 suggested_fix
    - 修完再跑一次，直到 critical_count == 0
    - stage2 的 HTML 生成入口会检查这个文件：不通过就拒绝发 HTML
    - 这是**机械级**强制，代替以往"软 HARD-GATE"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))


def main():
    if len(sys.argv) < 2:
        print("用法: python review_stage_output.py <ticker>", file=sys.stderr)
        sys.exit(64)

    ticker = sys.argv[1]

    from lib.self_review import review_all, write_review, format_human

    report = review_all(ticker)
    path = write_review(ticker, report)
    print(format_human(report))
    print(f"\n→ Issues JSON: {path}")
    print(f"→ passed: {report['passed']}  (critical={report['critical_count']}, "
          f"warning={report['warning_count']}, info={report['info_count']})")

    if report["critical_count"] > 0:
        print("\n⛔ BLOCKED: 必须修 critical 后重跑 review 再出 HTML。")
        sys.exit(1)
    elif report["warning_count"] > 0:
        print("\n⚠  WARN: warning 级问题存在，建议 agent 在 agent_analysis.review_acknowledged 写明")
        sys.exit(2)
    else:
        print("\n✓ OK: 全部通过，可以进 HTML 生成。")
        sys.exit(0)


if __name__ == "__main__":
    main()

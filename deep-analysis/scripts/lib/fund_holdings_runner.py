"""fund_holdings_runner · v3.4.0 · ETF/LOF 持仓批量分析.

### 设计

ETF/LOF 没有 ROE/护城河等个股财务字段 · 不能直接跑 22 维 + 51 评委.
但可以**循环分析它的前 N 大持仓股** · 每只成分股都得到完整 stock 报告 ·
最后聚合一份 fund-holdings-summary.html.

### 流程

1. preflight (run.py) 检测到 ETF/LOF · 不再 early-exit
2. 调 `confirm_and_run_holdings(ti, top_holdings)`:
   - 列出持仓清单 + 估算耗时/消耗
   - **二次确认**：y / N / 输入数字限制只跑前 K 只
3. 用户确认 → 循环跑 stock-analyze
4. 聚合 fund summary HTML（链接到 N 份子报告）

### 致谢
设计来自用户反馈："基金和 etf 很简单 · 你就搜索这个基金的持仓分析就行了 ·
但是在使用前要提醒用户因为要搜索十个股票 · 可能时间和消耗会变大 · 需要他二次确认"
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


# ─── 一些辅助常量 ───────────────────────────────────────────────

# 单只股票的耗时估算（秒）按 depth 分档
PER_STOCK_TIME_BY_DEPTH = {
    "lite":   60,
    "medium": 240,
    "deep":   900,
}


def _estimate_runtime(n_stocks: int, depth: str = "medium") -> str:
    """估算批量分析总耗时."""
    sec = n_stocks * PER_STOCK_TIME_BY_DEPTH.get(depth, 240)
    if sec < 120:
        return f"约 {sec} 秒"
    minutes = sec / 60
    if minutes < 60:
        return f"约 {minutes:.0f} 分钟"
    return f"约 {minutes / 60:.1f} 小时"


def confirm_and_run_holdings(
    fund_ticker: str,
    fund_label: str,
    top_holdings: list[dict],
    *,
    depth: str = "medium",
    auto_yes: bool = False,
    interactive: bool | None = None,
) -> dict:
    """提示用户二次确认 · 然后循环跑 holdings 分析.

    Args:
      fund_ticker: 基金代码（如 510300.SH / 161005.SZ）
      fund_label:  "ETF" / "LOF 基金" / etc
      top_holdings: [{rank, code, name, weight_pct}, ...]
      depth: lite / medium / deep
      auto_yes: 跳过交互直接确认（CI / agent）
      interactive: None=auto detect (sys.stdin.isatty)

    Returns:
      {
        "status": "completed" | "cancelled" | "no_holdings",
        "fund_ticker": ...,
        "analyzed": [...],     # 实际跑过的成分股 ticker
        "report_dirs": [...],  # 各子报告目录
        "summary_html": str,   # 聚合报告路径
      }
    """
    if not top_holdings:
        return {
            "status": "no_holdings",
            "fund_ticker": fund_ticker,
            "message": f"{fund_label} {fund_ticker} 拉不到持仓清单 · 跳过批量分析",
        }

    if interactive is None:
        interactive = sys.stdin.isatty() and not auto_yes

    n_total = len(top_holdings)
    print()
    print("━" * 60)
    print(f"📊 {fund_label} {fund_ticker} · 持仓批量分析")
    print("━" * 60)
    print(f"\n该基金前 {n_total} 大持仓：")
    for h in top_holdings:
        pct = f"{h['weight_pct']:.2f}%" if h.get("weight_pct") else "—"
        print(f"  {h['rank']:2d}. {h['name']:<14s} ({h['code']:<10s})  占比 {pct}")

    est = _estimate_runtime(n_total, depth)
    print(f"\n⚠️  循环分析 {n_total} 只成分股 · 预计 {est}（按 depth={depth})")
    print(f"    每只股票会跑完整 22 维 + 51 评委 + 17 机构方法 → 生成单独 HTML 报告")
    print(f"    所有报告都是缓存的（resume=True）· 重跑只会增量")

    # 二次确认
    if auto_yes:
        n_to_run = n_total
        print(f"\n   → auto_yes=True · 跑全部 {n_total} 只")
    elif interactive:
        try:
            choice = input(
                f"\n继续？\n"
                f"  y    = 跑全部 {n_total} 只\n"
                f"  数字 = 只跑前 K 只（如输入 5 跑前 5）\n"
                f"  N    = 取消（默认）\n"
                f"  请选择: "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n   已取消。")
            return {"status": "cancelled", "fund_ticker": fund_ticker}

        if choice in ("y", "yes"):
            n_to_run = n_total
        elif choice.isdigit():
            n_to_run = max(1, min(int(choice), n_total))
        else:
            print("   已取消。")
            return {"status": "cancelled", "fund_ticker": fund_ticker}
    else:
        # 非交互环境 + 没 auto_yes · 默认取消（agent 应明确传 auto_yes=True）
        print("   ⚠️  非交互环境 · 默认取消（agent 应传 UZI_FUND_AUTO_YES=1 明确确认）")
        return {"status": "cancelled", "fund_ticker": fund_ticker}

    selected = top_holdings[:n_to_run]
    print(f"\n   ✓ 即将分析 {n_to_run} 只成分股 · 估算 {_estimate_runtime(n_to_run, depth)}")
    print()

    # 循环跑 stock 分析
    from lib.pipeline.run import run_pipeline as _run_pipeline
    analyzed = []
    report_paths = []
    failed = []
    t0 = time.time()
    for i, h in enumerate(selected, 1):
        code = h["code"]
        name = h.get("name", code)
        print(f"\n━━━ [{i}/{n_to_run}] {name} ({code}) ━━━")
        try:
            report = _run_pipeline(code, resume=True)
            analyzed.append(code)
            report_paths.append(report)
        except Exception as e:
            print(f"   ⚠️  {code} 分析失败: {type(e).__name__}: {str(e)[:80]}")
            failed.append({"code": code, "name": name, "error": str(e)[:200]})
            continue

    dt = time.time() - t0
    print(f"\n━━━ 批量分析完成 · {dt:.0f}s · 成功 {len(analyzed)}/{n_to_run} ━━━")

    # 聚合 summary HTML
    summary_html = _generate_summary_html(
        fund_ticker, fund_label, top_holdings, analyzed, report_paths, failed,
    )

    return {
        "status": "completed",
        "fund_ticker": fund_ticker,
        "fund_label": fund_label,
        "analyzed": analyzed,
        "failed": failed,
        "report_paths": [str(p) for p in report_paths],
        "summary_html": str(summary_html),
        "total_runtime_sec": int(dt),
    }


def _generate_summary_html(
    fund_ticker: str,
    fund_label: str,
    all_holdings: list[dict],
    analyzed_codes: list[str],
    report_paths: list,
    failed: list[dict],
) -> Path:
    """聚合 HTML 报告 · 索引页链接所有子报告."""
    out_dir = Path("reports") / f"{fund_ticker}_holdings_{datetime.now().strftime('%Y%m%d')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "fund-holdings-summary.html"

    rows = []
    for h in all_holdings:
        code = h["code"]
        name = h.get("name", code)
        weight = h.get("weight_pct")
        weight_str = f"{weight:.2f}%" if weight else "—"
        if code in analyzed_codes:
            idx = analyzed_codes.index(code)
            try:
                report_p = Path(report_paths[idx])
                rel = os.path.relpath(report_p, out_dir)
                status_html = f'<a href="{rel}" target="_blank" style="color:#0891b2">查看报告 →</a>'
            except Exception:
                status_html = '<span style="color:#9ca3af">报告路径异常</span>'
        elif any(f["code"] == code for f in failed):
            err = next(f for f in failed if f["code"] == code)["error"]
            status_html = f'<span style="color:#dc2626" title="{err}">❌ 失败</span>'
        else:
            status_html = '<span style="color:#9ca3af">未分析</span>'

        rows.append(
            f'<tr><td>{h["rank"]}</td><td><strong>{name}</strong></td>'
            f'<td><code>{code}</code></td><td>{weight_str}</td>'
            f'<td>{status_html}</td></tr>'
        )

    rows_html = "\n".join(rows)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>{fund_label} {fund_ticker} · 持仓分析汇总</title>
  <style>
    body {{ font-family: -apple-system, "Helvetica Neue", sans-serif; max-width: 880px; margin: 40px auto; padding: 20px; color: #111; }}
    h1 {{ color: #0891b2; border-bottom: 3px solid #0891b2; padding-bottom: 8px; }}
    .meta {{ color: #6b7280; font-size: 14px; margin: 12px 0 24px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e5e7eb; text-align: left; font-size: 14px; }}
    th {{ background: #f3f4f6; font-weight: 600; }}
    tr:hover {{ background: #f9fafb; }}
    code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-size: 13px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px;
              background: #06b6d4; color: #fff; font-weight: 700; letter-spacing: 1px; }}
    .summary {{ background: #f0fdfa; border-left: 4px solid #06b6d4; padding: 14px 18px;
                margin: 20px 0; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>📊 {fund_label} 持仓分析汇总</h1>
  <div class="meta">
    <span class="badge">FUND HOLDINGS</span>
    <strong>{fund_ticker}</strong> · 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
  </div>

  <div class="summary">
    <strong>分析进度</strong>：成功 {len(analyzed_codes)} / 失败 {len(failed)} / 总持仓 {len(all_holdings)}<br>
    点击下方"查看报告 →"打开各成分股的完整 22 维 + 51 评委分析.
  </div>

  <table>
    <thead>
      <tr><th>排名</th><th>名称</th><th>代码</th><th>占净值比例</th><th>状态</th></tr>
    </thead>
    <tbody>
{rows_html}
    </tbody>
  </table>

  <p style="margin-top:30px;color:#6b7280;font-size:12px;text-align:center">
    UZI-Skill v3.4.0 · 基金/ETF 持仓批量分析功能 · 数据来自 akshare.fund_portfolio_hold_em
  </p>
</body>
</html>"""

    out_file.write_text(html, encoding="utf-8")
    print(f"\n📄 持仓分析汇总报告: {out_file}")
    return out_file

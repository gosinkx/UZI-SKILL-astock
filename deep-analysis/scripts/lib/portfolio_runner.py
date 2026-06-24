"""v3.6.0 · 用户自定义组合批量分析 (--portfolio file.csv).

用户用法:
    # holdings.csv:
    #   ticker,weight,note
    #   600519.SH,0.30,白酒龙头
    #   000858.SZ,0.15,白酒第二
    #   002594.SZ,0.25,电动车
    #   贵州茅台,0.30                   # 也支持中文名
    python run.py --portfolio holdings.csv

输出:
    reports/portfolio_{name}_{date}/
      ├── index.html         · 总览（组合健康度 + 排名 + 加权汇总 + 各成分简版）
      ├── stock_<ticker>/    · 每只票的单独完整报告（指向 reports/{ticker}_{date}/）
      └── metadata.json      · 组合摘要（供 SaaS / 后续追踪用）

特性:
    · resume=True · 已分析过的票直接复用 cache
    · weights 自动归一化 · 不足 1.0 也兼容
    · 失败容忍 · 单只 fail 不阻断其他
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = SCRIPTS_DIR.parent / "assets"


def _parse_csv(path: Path) -> list[dict]:
    """Parse holdings CSV · 容错 · ticker 必须 · weight/note 可选.

    支持:
        · 第一行 header 含 ticker (或 code/symbol/股票)
        · 无 header · 单列 ticker
        · weight 列名 weight / 权重 / 仓位 / pct（数值 0-1 或 0-100 都可）
    """
    if not path.exists():
        raise FileNotFoundError(f"组合文件不存在: {path}")

    rows: list[dict] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        # 探测 header
        first_line = f.readline().strip()
        f.seek(0)

        has_header = any(k in first_line.lower() for k in
                         ["ticker", "code", "symbol", "weight", "权重", "股票"])

        if has_header:
            reader = csv.DictReader(f)
            # 归一化 key 名
            tk_keys = ["ticker", "code", "symbol", "股票", "代码"]
            wt_keys = ["weight", "权重", "仓位", "pct", "比例"]
            note_keys = ["note", "备注", "remark"]

            for r in reader:
                # case-insensitive lookup
                norm = {k.lower().strip(): v for k, v in r.items() if k}
                ticker = next((norm.get(k) for k in tk_keys if norm.get(k)), None)
                if not ticker:
                    continue
                weight = next((norm.get(k) for k in wt_keys if norm.get(k)), None)
                note = next((norm.get(k) for k in note_keys if norm.get(k)), "")

                try:
                    w = float(weight) if weight not in (None, "") else None
                    if w is not None and w > 1.0:
                        w = w / 100.0  # 50 当 50%
                except (TypeError, ValueError):
                    w = None

                rows.append({"ticker": ticker.strip(), "weight": w, "note": (note or "").strip()})
        else:
            # 无 header · 假设单列 ticker
            reader = csv.reader(f)
            for r in reader:
                if r and r[0].strip():
                    rows.append({"ticker": r[0].strip(), "weight": None, "note": ""})

    if not rows:
        raise ValueError(f"组合文件 {path} 解析后为空")

    return rows


def _normalize_weights(holdings: list[dict]) -> list[dict]:
    """归一化 weight · 总和 → 1.0 · 缺失 → 平均分配."""
    n = len(holdings)
    weighted = [h for h in holdings if h.get("weight") is not None]
    unweighted = [h for h in holdings if h.get("weight") is None]

    if not weighted:
        # 全部平均
        for h in holdings:
            h["weight"] = 1.0 / n
        return holdings

    total = sum(h["weight"] for h in weighted)
    if unweighted:
        # 已加权部分 + 未加权部分均分剩余
        remain = max(0.0, 1.0 - total)
        share = remain / len(unweighted) if remain > 0 else 0
        for h in unweighted:
            h["weight"] = share
        # 重新计算 · 防止 total > 1
        total = sum(h["weight"] for h in holdings)

    # 归一化
    if total > 0:
        for h in holdings:
            h["weight"] = h["weight"] / total
    return holdings


def _load_metrics_for(ticker: str) -> dict | None:
    """直接复用 versus_runner._extract_metrics + _load_cache."""
    from lib.versus_runner import _load_cache, _extract_metrics
    bundle = _load_cache(ticker)
    if not bundle:
        return None
    return _extract_metrics(bundle)


def _portfolio_health(metrics: list[dict]) -> dict:
    """计算组合健康度（加权评分 + 集中度 + 分散度）."""
    valid = [m for m in metrics if m and m.get("overall_score") is not None]
    if not valid:
        return {"weighted_score": 0, "max_weight": 0, "n_industries": 0, "verdict": "数据不足"}

    weighted_score = sum(m["overall_score"] * m["_weight"] for m in valid)
    max_weight = max(m["_weight"] for m in valid)
    industries = set(m.get("industry", "—") for m in valid if m.get("industry") != "—")

    # 健康度判定
    if weighted_score >= 70 and max_weight < 0.40 and len(industries) >= 3:
        verdict = "🟢 健康 · 加权分高 · 分散度好"
    elif weighted_score >= 55:
        verdict = "🟡 一般 · 有改善空间"
    else:
        verdict = "🔴 风险 · 加权分偏低或过度集中"

    return {
        "weighted_score": round(weighted_score, 1),
        "max_weight": round(max_weight, 3),
        "n_industries": len(industries),
        "industries": sorted(industries),
        "verdict": verdict,
        "n_valid": len(valid),
        "n_total": len(metrics),
    }


def _render_html(portfolio_name: str, metrics: list[dict], health: dict, depth: str) -> str:
    """单 HTML · 组合总览 + 排名 + 加权汇总."""
    from lib.versus_runner import _esc  # v3.7.2 · 复用 HTML 转义助手 · 防 self-XSS
    template_path = ASSETS_DIR / "report-template.html"
    full = template_path.read_text(encoding="utf-8")
    style_start = full.find("<style>")
    style_end = full.find("</style>") + len("</style>")
    main_style = full[style_start:style_end] if style_start > 0 else ""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    portfolio_name = _esc(portfolio_name)  # title / h1 都用它 · 先转义

    # 排序：按 score 降序
    ranked = sorted(
        [m for m in metrics if m],
        key=lambda m: m.get("overall_score") or 0,
        reverse=True,
    )

    # 排名表
    rows = []
    for i, m in enumerate(ranked, 1):
        sc = m.get("overall_score") or 0
        sc_color = "var(--bull-green)" if sc >= 65 else "var(--neon-gold)" if sc >= 50 else "var(--bear-red)"
        w = m.get("_weight", 0) * 100
        rows.append(
            f'<tr style="border-bottom:1px solid var(--border)">'
            f'  <td style="padding:10px 16px;color:var(--text-dim);font-family:Fira Code,monospace;font-size:11px">#{i}</td>'
            f'  <td style="padding:10px 16px"><div style="font-weight:700;color:var(--text-bright)">{_esc(m["name"])}</div>'
            f'    <div style="font-size:11px;color:var(--text-dim);font-family:Fira Code,monospace">{_esc(m["ticker"])} · {_esc(m.get("industry","—"))}</div></td>'
            f'  <td style="padding:10px 16px;text-align:right;font-variant-numeric:tabular-nums">{w:.1f}%</td>'
            f'  <td style="padding:10px 16px;text-align:right;color:{sc_color};font-weight:700;font-variant-numeric:tabular-nums">{sc:.1f}</td>'
            f'  <td style="padding:10px 16px;font-size:12px;color:var(--text-main)">{_esc(m.get("verdict","—"))}</td>'
            f'  <td style="padding:10px 16px;text-align:center;font-size:11px">'
            f'    <span style="color:var(--bull-green)">📈{m.get("bull_count",0)}</span> · '
            f'    <span style="color:var(--bear-red)">📉{m.get("bear_count",0)}</span>'
            f'  </td>'
            f'</tr>'
        )

    # 加权 KPI
    health_color = ("var(--bull-green)" if "🟢" in health["verdict"]
                    else "var(--neon-gold)" if "🟡" in health["verdict"]
                    else "var(--bear-red)")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>组合 · {portfolio_name}</title>
{main_style}
</head>
<body>
<div class="container" style="max-width:1180px;margin:0 auto;padding:30px 24px">
  <div class="topbar">
    <div class="left">
      <div class="dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div>
      <div class="brand">FloatFu-true <span>PORTFOLIO</span></div>
    </div>
    <div class="status">
      <span>组合分析 · depth={depth} · {now}</span>
      <button class="theme-toggle" id="theme-toggle" title="切换暗色 / 浅色主题">🌙</button>
    </div>
  </div>

  <div style="text-align:center;margin:24px 0">
    <div style="font-family:Space Grotesk,sans-serif;font-size:11px;letter-spacing:.24em;color:var(--neon-cyan);text-transform:uppercase">📊 PORTFOLIO HEALTH</div>
    <h1 style="font-size:32px;font-weight:900;color:var(--text-bright);margin:8px 0 4px">{portfolio_name}</h1>
    <div style="font-size:12px;color:var(--text-dim);font-family:Fira Code,monospace">{health["n_valid"]}/{health["n_total"]} 只成分股 · {health["n_industries"]} 个行业</div>
  </div>

  <!-- KPI grid -->
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin:24px 0">
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:18px;box-shadow:var(--shadow-sm)">
      <div style="font-size:10px;letter-spacing:.16em;color:var(--text-dim);margin-bottom:6px">加权评分</div>
      <div style="font-size:32px;font-weight:900;color:{health_color};font-variant-numeric:tabular-nums" class="count-up">{health["weighted_score"]}</div>
      <div style="font-size:11px;color:var(--text-dim)">/ 100</div>
    </div>
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:18px;box-shadow:var(--shadow-sm)">
      <div style="font-size:10px;letter-spacing:.16em;color:var(--text-dim);margin-bottom:6px">最大单只仓位</div>
      <div style="font-size:32px;font-weight:900;color:var(--text-bright);font-variant-numeric:tabular-nums">{health["max_weight"]*100:.1f}<span style="font-size:18px">%</span></div>
      <div style="font-size:11px;color:var(--text-dim)">{'⚠️ 集中度偏高' if health['max_weight'] > 0.4 else '✓ 分散合理'}</div>
    </div>
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:18px;box-shadow:var(--shadow-sm)">
      <div style="font-size:10px;letter-spacing:.16em;color:var(--text-dim);margin-bottom:6px">行业分散</div>
      <div style="font-size:32px;font-weight:900;color:var(--text-bright);font-variant-numeric:tabular-nums">{health["n_industries"]}</div>
      <div style="font-size:11px;color:var(--text-dim)">{', '.join(_esc(x) for x in health.get("industries", [])[:3])}{'...' if len(health.get("industries", [])) > 3 else ''}</div>
    </div>
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:18px;box-shadow:var(--shadow-sm)">
      <div style="font-size:10px;letter-spacing:.16em;color:var(--text-dim);margin-bottom:6px">综合判定</div>
      <div style="font-size:18px;font-weight:700;color:{health_color};line-height:1.3;margin-top:4px">{health["verdict"]}</div>
    </div>
  </div>

  <!-- Ranking table -->
  <div class="section-head" style="margin:32px 0 14px">
    <div class="section-tag">01 / RANKING</div>
    <h2 class="section-title">成分股排名</h2>
    <div class="section-line"></div>
  </div>

  <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:separate;border-spacing:0;background:var(--bg-card);border:1px solid var(--border);border-radius:12px;overflow:hidden">
      <thead style="background:var(--bg-tinted);border-bottom:2px solid var(--border)">
        <tr style="font-size:11px;letter-spacing:.1em;color:var(--text-dim);text-transform:uppercase">
          <th style="padding:12px 16px;text-align:left">排名</th>
          <th style="padding:12px 16px;text-align:left">股票</th>
          <th style="padding:12px 16px;text-align:right">仓位</th>
          <th style="padding:12px 16px;text-align:right">总评</th>
          <th style="padding:12px 16px;text-align:left">判定</th>
          <th style="padding:12px 16px;text-align:center">多空</th>
        </tr>
      </thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
  </div>

  <div style="margin:32px 0 20px;padding:18px;background:var(--bg-tinted);border-radius:10px;border:1px dashed var(--border)">
    <div style="font-size:11px;color:var(--text-dim);letter-spacing:.14em;margin-bottom:6px">📌 USAGE</div>
    <div style="font-size:13px;color:var(--text-main);line-height:1.6">
      加权分 = Σ (个股总评 × 权重)。集中度 / 行业数 仅作风险参考 · 不构成调仓建议. 完整 22 维 + 51 评委分析见各自独立报告 · 路径在终端输出.
    </div>
  </div>

  <div style="text-align:center;padding:30px 0 16px;color:var(--text-dim);font-size:11px;letter-spacing:.1em">
    Generated by FloatFu-true · UZI-Skill v3.6.0 · 组合分析模式
  </div>
</div>

<script>
(function() {{
  const KEY = 'uzi-theme';
  const root = document.documentElement;
  const stored = localStorage.getItem(KEY);
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  root.setAttribute('data-theme', stored || (prefersDark ? 'dark' : 'light'));
  const btn = document.getElementById('theme-toggle');
  const syncIcon = () => {{ if (btn) btn.textContent = root.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙'; }};
  syncIcon();
  btn?.addEventListener('click', () => {{
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem(KEY, next);
    syncIcon();
  }});
}})();
</script>
</body>
</html>"""


def run_portfolio(
    csv_path: str | Path,
    *,
    depth: str = "lite",
    auto_open: bool = True,
    portfolio_name: str | None = None,
) -> dict:
    """跑用户自定义组合 · CSV → 循环分析 → 单 HTML."""
    path = Path(csv_path).expanduser().resolve()
    try:
        rows = _parse_csv(path)
    except (FileNotFoundError, ValueError) as e:
        return {"status": "csv_error", "error": str(e)}

    name = portfolio_name or path.stem
    print()
    print("━" * 60)
    print(f"📊 组合分析模式 · {name} · {len(rows)} 只成分股 · depth={depth}")
    print("━" * 60)
    for r in rows:
        w = f"{r['weight']:.1%}" if r.get("weight") is not None else "—"
        print(f"  · {r['ticker']:<18s}  仓位 {w:<6s}  {r.get('note', '')}")

    if depth:
        os.environ.setdefault("UZI_DEPTH", depth)

    from lib.pipeline.run import run_pipeline as _run_pipeline
    from lib.market_router import parse_ticker

    t0 = time.time()
    rows = _normalize_weights(rows)
    metrics_list: list[dict] = []
    failed = []
    for i, r in enumerate(rows, 1):
        t = r["ticker"]
        print(f"\n━━━ [{i}/{len(rows)}] {t} ━━━")
        try:
            _run_pipeline(t, resume=True)
        except Exception as e:
            print(f"   ⚠️  pipeline 异常: {type(e).__name__}: {str(e)[:80]} · 继续读 cache")

        try:
            ti = parse_ticker(t)
            cache_key = ti.full
        except Exception:
            cache_key = t

        m = _load_metrics_for(cache_key) or _load_metrics_for(t)
        if m:
            m["_weight"] = r["weight"]
            m["_note"] = r.get("note", "")
            metrics_list.append(m)
        else:
            failed.append({"ticker": t, "weight": r["weight"]})

    if len(metrics_list) < 1:
        return {
            "status": "insufficient_data",
            "loaded": 0,
            "failed": failed,
            "message": "无可用成分股 · 至少需 1 只成功才能出组合报告",
        }

    health = _portfolio_health(metrics_list)

    date = datetime.now().strftime("%Y%m%d")
    safe_name = name.replace(" ", "_").replace("/", "_")
    out_dir = SCRIPTS_DIR / "reports" / f"portfolio_{safe_name}_{date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(_render_html(name, metrics_list, health, depth), encoding="utf-8")

    # metadata 摘要 · 供 SaaS / 追踪用
    meta = {
        "portfolio_name": name,
        "depth": depth,
        "generated_at": datetime.now().isoformat(),
        "health": health,
        "holdings": [
            {"ticker": m["ticker"], "name": m["name"], "weight": m["_weight"],
             "overall_score": m.get("overall_score"), "verdict": m.get("verdict"),
             "note": m.get("_note", "")}
            for m in metrics_list
        ],
        "failed": failed,
    }
    (out_dir / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    dt = int(time.time() - t0)
    print(f"\n━━━ 组合分析完成 · {dt}s · 成功 {len(metrics_list)}/{len(rows)} ━━━")
    print(f"📄 报告: {out_file}")
    print(f"📊 加权评分 {health['weighted_score']} · {health['verdict']}")

    if auto_open and not os.environ.get("UZI_NO_AUTO_OPEN"):
        try:
            import webbrowser
            webbrowser.open(out_file.as_uri())
        except Exception:
            pass

    return {
        "status": "completed",
        "portfolio_name": name,
        "loaded": len(metrics_list),
        "failed": failed,
        "health": health,
        "report_path": str(out_file),
        "metadata_path": str(out_dir / "metadata.json"),
        "runtime_sec": dt,
    }

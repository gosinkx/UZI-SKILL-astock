"""v3.6.0 · 多股横向对比 runner.

用户用法:
    python run.py --versus 600519.SH 000858.SZ
    python run.py --versus 茅台 五粮液 --depth lite

流程：
    1. 循环跑每只票（resume=True · 复用 cache）
    2. 读各自 synthesis.json + panel.json + raw_data.dimensions
    3. 抽取核心维度（overall_score / verdict / PE / PB / ROE / 营收 / 毛利率 / 51 评委投票）
    4. 生成单 HTML：左右/三列/四列网格 · 同维度跨股对比 · 高亮谁更优

返回：versus_html 路径
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parents[1]  # .../scripts
ASSETS_DIR = SCRIPTS_DIR.parent / "assets"  # .../deep-analysis/assets


def _safe(v, default="—"):
    if v is None or v == "" or v == "?":
        return default
    return v


def _esc(v, default="—") -> str:
    """v3.7.2 · HTML 转义 · 防御性纵深（股票名/备注若含 < > & 不会注入）.

    数据源是 akshare/东财 · 通常无恶意 · 但 --portfolio 的 CSV note/name 是
    用户可控字段 · 统一转义杜绝 self-XSS。
    """
    import html as _html
    s = _safe(v, default)
    return _html.escape(str(s), quote=True)


def _num(v, decimals=1):
    try:
        return f"{float(v):.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def _winner(values: list[float | None], higher_is_better: bool = True) -> int:
    """返回 winner 的索引（0-based）· 全空返 -1."""
    valid = [(i, v) for i, v in enumerate(values) if v is not None and v != 0]
    if not valid:
        return -1
    if higher_is_better:
        return max(valid, key=lambda t: t[1])[0]
    return min(valid, key=lambda t: t[1])[0]


def _load_cache(ticker: str) -> dict | None:
    """读 .cache/{ticker}/{synthesis,raw_data,panel}.json · 全有才返."""
    cache = SCRIPTS_DIR / ".cache" / ticker
    try:
        syn = json.loads((cache / "synthesis.json").read_text(encoding="utf-8"))
        raw = json.loads((cache / "raw_data.json").read_text(encoding="utf-8"))
        panel_path = cache / "panel.json"
        panel = json.loads(panel_path.read_text(encoding="utf-8")) if panel_path.exists() else {}
        return {"syn": syn, "raw": raw, "panel": panel, "ticker": ticker}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"   ⚠️  {ticker} cache 读取失败: {type(e).__name__}: {e}")
        return None


def _extract_metrics(bundle: dict) -> dict:
    """从一个 ticker 的 cache 抽出横向对比所需的字段."""
    syn = bundle["syn"]
    raw = bundle["raw"]
    panel = bundle["panel"]
    dims = raw.get("dimensions", {}) or {}
    basic = (dims.get("0_basic") or {}).get("data") or {}
    fin = (dims.get("1_financials") or {}).get("data") or {}
    val = (dims.get("10_valuation") or {}).get("data") or {}
    sig = panel.get("signal_distribution") or {}

    def _f(x):
        try:
            return float(x) if x is not None else None
        except (TypeError, ValueError):
            return None

    return {
        "ticker": bundle["ticker"],
        "name": syn.get("name") or basic.get("name") or bundle["ticker"],
        "industry": basic.get("industry") or "—",
        "price": _f(basic.get("price")),
        "market_cap_yi": _f(basic.get("market_cap_yi") or basic.get("market_cap")),
        "pe_ttm": _f(basic.get("pe_ttm") or val.get("pe_ttm")),
        "pb": _f(basic.get("pb") or val.get("pb")),
        "roe": _f(fin.get("roe") or fin.get("roe_ttm")),
        "net_margin": _f(fin.get("net_margin")),
        "gross_margin": _f(fin.get("gross_margin")),
        "rev_growth_3y": _f(fin.get("rev_growth_3y") or fin.get("revenue_growth_3y")),
        "overall_score": _f(syn.get("overall_score")),
        "fund_score": _f(syn.get("fundamental_score")),
        "consensus": _f(syn.get("panel_consensus") or panel.get("panel_consensus")),
        "verdict": syn.get("verdict_label") or "—",
        "verdict_detail": syn.get("verdict_detail") or "",
        "bull_count": sig.get("bullish", 0),
        "bear_count": sig.get("bearish", 0),
        "neutral_count": sig.get("neutral", 0),
        "skip_count": sig.get("skip", 0),
        "punchline": (syn.get("debate") or {}).get("punchline", ""),
        "trap_level": ((dims.get("18_trap") or {}).get("data") or {}).get("trap_level", "🟢 安全"),
        "school_lock": syn.get("school_lock"),  # v3.5.0 兼容
        "report_path": None,  # 由 caller 填
    }


# ─── COMPARISON RUBRIC ─────────────────────────────────────
# (label, key, decimals, higher_is_better, group)
ROWS = [
    ("价格", "price", 2, None, "basic"),
    ("市值（亿）", "market_cap_yi", 0, None, "basic"),
    ("行业", "industry", None, None, "basic"),
    ("PE TTM", "pe_ttm", 1, False, "value"),
    ("PB", "pb", 2, False, "value"),
    ("ROE %", "roe", 1, True, "quality"),
    ("净利率 %", "net_margin", 1, True, "quality"),
    ("毛利率 %", "gross_margin", 1, True, "quality"),
    ("3y 营收增速 %", "rev_growth_3y", 1, True, "growth"),
    ("总评 /100", "overall_score", 1, True, "score"),
    ("基本面分 /100", "fund_score", 1, True, "score"),
    ("评委共识 %", "consensus", 1, True, "score"),
]


def _render_comparison_grid(stocks: list[dict]) -> str:
    """生成核心对比表 HTML."""
    n = len(stocks)
    col_pct = f"{100 / (n + 1):.2f}%"

    def header_row():
        cells = [f'<th style="width:{col_pct};text-align:left;padding:12px 16px">指标</th>']
        for s in stocks:
            cells.append(
                f'<th style="width:{col_pct};padding:12px 16px;text-align:center">'
                f'<div style="font-size:16px;font-weight:700;color:var(--text-bright)">{_esc(s["name"])}</div>'
                f'<div style="font-family:Fira Code,monospace;font-size:11px;color:var(--text-dim);margin-top:2px">'
                f'{_esc(s["ticker"])}</div></th>'
            )
        return "<tr>" + "".join(cells) + "</tr>"

    rows_html = []
    for label, key, dec, higher, group in ROWS:
        vals = [s.get(key) for s in stocks]
        if all(v is None or v == "—" for v in vals):
            continue
        winner_idx = _winner([v for v in vals if isinstance(v, (int, float))], higher_is_better=bool(higher)) if higher is not None else -1
        # 重新映射 winner 到原始索引
        if winner_idx >= 0:
            real_idx = [i for i, v in enumerate(vals) if isinstance(v, (int, float))][winner_idx]
        else:
            real_idx = -1

        cells = [
            f'<td style="padding:10px 16px;color:var(--text-mid);font-size:12px;letter-spacing:.06em">{label}</td>'
        ]
        for i, v in enumerate(vals):
            if v is None:
                display = "—"
            elif dec is None:
                display = str(v)
            else:
                display = _num(v, dec)
            color = "var(--bull-green)" if i == real_idx else "var(--text-main)"
            weight = "700" if i == real_idx else "500"
            badge = ' <span style="font-size:9px;color:var(--bull-green);letter-spacing:.1em">★ WIN</span>' if i == real_idx else ""
            cells.append(
                f'<td style="padding:10px 16px;text-align:center;color:{color};font-weight:{weight};font-variant-numeric:tabular-nums">'
                f'{display}{badge}</td>'
            )
        rows_html.append("<tr>" + "".join(cells) + "</tr>")

    return (
        f'<table style="width:100%;border-collapse:separate;border-spacing:0;'
        f'background:var(--bg-card);border:1px solid var(--border);border-radius:12px;overflow:hidden">'
        f'<thead style="background:var(--bg-tinted);border-bottom:2px solid var(--border)">'
        f'{header_row()}</thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        f'</table>'
    )


def _render_verdict_cards(stocks: list[dict]) -> str:
    cards = []
    for s in stocks:
        sc = s.get("overall_score") or 0
        sc_color = "var(--bull-green)" if sc >= 65 else "var(--neon-gold)" if sc >= 50 else "var(--bear-red)"
        bull = s.get("bull_count", 0)
        bear = s.get("bear_count", 0)
        neut = s.get("neutral_count", 0)
        cards.append(
            f'<div style="flex:1;min-width:240px;background:var(--bg-card);border:1px solid var(--border);'
            f'border-radius:12px;padding:20px;box-shadow:var(--shadow-sm)">'
            f'  <div style="font-size:11px;color:var(--text-dim);letter-spacing:.14em;margin-bottom:4px">{_esc(s["ticker"])}</div>'
            f'  <div style="font-size:18px;font-weight:700;color:var(--text-bright)">{_esc(s["name"])}</div>'
            f'  <div style="font-size:11px;color:var(--text-dim);margin-top:2px">{_esc(s["industry"])}</div>'
            f'  <div style="margin:14px 0;display:flex;align-items:baseline;gap:8px">'
            f'    <span style="font-size:36px;font-weight:900;color:{sc_color};font-variant-numeric:tabular-nums" class="count-up">{_num(sc, 1)}</span>'
            f'    <span style="font-size:14px;color:var(--text-dim)">/ 100</span>'
            f'  </div>'
            f'  <div style="font-size:13px;font-weight:600;color:{sc_color}">{_esc(s["verdict"])}</div>'
            f'  <div style="font-size:11px;color:var(--text-dim);margin-top:4px">{_esc(s.get("verdict_detail", ""), "")}</div>'
            f'  <div style="margin-top:14px;padding-top:14px;border-top:1px dashed var(--border);'
            f'display:flex;gap:10px;font-size:11px">'
            f'    <span style="color:var(--bull-green)">📈 {bull}</span>'
            f'    <span style="color:var(--text-dim)">⚖️ {neut}</span>'
            f'    <span style="color:var(--bear-red)">📉 {bear}</span>'
            f'  </div>'
            f'  <div style="margin-top:10px;font-size:11px;color:var(--text-mid);font-style:italic;line-height:1.4">'
            f'    {_esc(s.get("punchline", "")[:120], "")}'
            f'  </div>'
            f'</div>'
        )
    return f'<div style="display:flex;gap:16px;flex-wrap:wrap;margin:24px 0">{"".join(cards)}</div>'


def _render_html(stocks: list[dict], depth: str) -> str:
    """v3.6.0 · 拼装最终 versus HTML · 复用 main report 的 CSS 主题变量."""
    titles = " VS ".join(_esc(s["name"]) for s in stocks)
    tickers_csv = " · ".join(_esc(s["ticker"]) for s in stocks)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 复用主模板的 :root + dark-theme + jargon CSS · 单独读
    template_path = ASSETS_DIR / "report-template.html"
    full = template_path.read_text(encoding="utf-8")
    style_start = full.find("<style>")
    style_end = full.find("</style>") + len("</style>")
    main_style = full[style_start:style_end] if style_start > 0 else ""

    verdict_cards = _render_verdict_cards(stocks)
    grid = _render_comparison_grid(stocks)

    # 简化 punchline 大对决
    punch_block = ""
    if all(s.get("punchline") for s in stocks):
        cells = []
        for s in stocks:
            cells.append(
                f'<div style="flex:1;padding:16px 20px;background:var(--bg-tinted);'
                f'border-left:3px solid var(--neon-cyan);border-radius:8px">'
                f'<div style="font-size:10px;letter-spacing:.16em;color:var(--neon-cyan);margin-bottom:6px">'
                f'PUNCHLINE · {_esc(s["name"])}</div>'
                f'<div style="font-size:13px;color:var(--text-main);line-height:1.5;font-style:italic">'
                f'{_esc(s["punchline"][:200], "")}</div>'
                f'</div>'
            )
        punch_block = f'<div style="display:flex;gap:14px;margin:24px 0;flex-wrap:wrap">{"".join(cells)}</div>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>VS · {titles}</title>
{main_style}
<style>
.versus-hero {{
  margin: 24px 0 12px;
  text-align: center;
}}
.versus-hero .label {{
  font-family: 'Space Grotesk', sans-serif;
  font-size: 11px;
  letter-spacing: .24em;
  color: var(--neon-pink);
  text-transform: uppercase;
}}
.versus-hero h1 {{
  font-size: 32px;
  font-weight: 900;
  color: var(--text-bright);
  margin: 6px 0 4px;
  letter-spacing: -.01em;
}}
.versus-hero .sub {{
  font-size: 12px;
  color: var(--text-dim);
  font-family: 'Fira Code', monospace;
}}
</style>
</head>
<body>
<div class="container" style="max-width:1200px;margin:0 auto;padding:30px 24px">
  <div class="topbar">
    <div class="left">
      <div class="dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div>
      <div class="brand">FloatFu-true <span>VERSUS</span></div>
    </div>
    <div class="status">
      <span>横向对比 · depth={depth} · {now}</span>
      <button class="theme-toggle" id="theme-toggle" title="切换暗色 / 浅色主题">🌙</button>
    </div>
  </div>

  <div class="versus-hero">
    <div class="label">▶ HEAD TO HEAD · 横向对决</div>
    <h1>{titles}</h1>
    <div class="sub">{tickers_csv}</div>
  </div>

  {verdict_cards}

  <div class="section-head" style="margin:32px 0 14px">
    <div class="section-tag">01 / METRICS</div>
    <h2 class="section-title">核心指标对照</h2>
    <div class="section-line"></div>
  </div>

  {grid}

  {punch_block}

  <div style="margin:32px 0 20px;padding:18px;background:var(--bg-tinted);border-radius:10px;border:1px dashed var(--border)">
    <div style="font-size:11px;color:var(--text-dim);letter-spacing:.14em;margin-bottom:6px">📌 USAGE</div>
    <div style="font-size:13px;color:var(--text-main);line-height:1.6">
      表内★ WIN 仅为单维度高低对比 · 不构成投资建议. 完整 22 维 + 51 评委分析见各自独立报告 ·
      路径在终端输出 · 也可 <code>python run.py {stocks[0]["ticker"]}</code> 单独跑.
    </div>
  </div>

  <div style="text-align:center;padding:30px 0 16px;color:var(--text-dim);font-size:11px;letter-spacing:.1em">
    Generated by FloatFu-true · UZI-Skill v3.6.0 · 横向对比模式
  </div>
</div>

<script>
// 复用主模板的 dark-mode toggle · 极简版（避免重复整套 JS）
(function() {{
  const KEY = 'uzi-theme';
  const root = document.documentElement;
  const stored = localStorage.getItem(KEY);
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  root.setAttribute('data-theme', stored || (prefersDark ? 'dark' : 'light'));
  const btn = document.getElementById('theme-toggle');
  const syncIcon = () => {{
    if (btn) btn.textContent = root.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
  }};
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


def run_versus(tickers: list[str], *, depth: str = "lite", auto_open: bool = True) -> dict:
    """对 2-4 只股票做横向对比 · 生成单 HTML.

    Returns:
        {
          "status": "completed" | "insufficient_data",
          "tickers": [...],
          "report_path": "...html",
          "runtime_sec": int,
        }
    """
    if not (2 <= len(tickers) <= 4):
        return {"status": "invalid_input", "message": f"--versus 接受 2-4 只 · 实际 {len(tickers)}"}

    print()
    print("━" * 60)
    print(f"⚔️  横向对比模式 · {' VS '.join(tickers)} · depth={depth}")
    print("━" * 60)

    # 设深度
    if depth:
        os.environ.setdefault("UZI_DEPTH", depth)

    try:
        from lib.pipeline.run import run_pipeline as _run_pipeline
    except Exception as e:
        return {"status": "pipeline_unavailable", "error": str(e)}

    bundles: list[dict] = []
    t0 = time.time()
    for i, t in enumerate(tickers, 1):
        print(f"\n━━━ [{i}/{len(tickers)}] {t} ━━━")
        try:
            _run_pipeline(t, resume=True)
        except Exception as e:
            print(f"   ⚠️  {t} pipeline 异常: {type(e).__name__}: {str(e)[:80]} · 继续读 cache")

        # cache key 可能是原 ticker 也可能是标准化后的 · 试两种
        from lib.market_router import parse_ticker
        try:
            ti = parse_ticker(t)
            cache_key = ti.full
        except Exception:
            cache_key = t
        bundle = _load_cache(cache_key) or _load_cache(t)
        if bundle:
            bundles.append(bundle)
        else:
            print(f"   ⚠️  {t} cache 缺失 · 跳过对比")

    if len(bundles) < 2:
        return {
            "status": "insufficient_data",
            "tickers": tickers,
            "loaded": len(bundles),
            "message": "至少需要 2 只票成功读到 cache · 才能生成对比报告",
        }

    metrics = [_extract_metrics(b) for b in bundles]

    # 输出 HTML
    safe_keys = "_vs_".join(m["ticker"].replace(".", "_") for m in metrics)
    date = datetime.now().strftime("%Y%m%d")
    out_dir = SCRIPTS_DIR / "reports" / f"versus_{safe_keys}_{date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    out_file.write_text(_render_html(metrics, depth), encoding="utf-8")

    dt = int(time.time() - t0)
    print(f"\n━━━ 横向对比完成 · {dt}s ━━━")
    print(f"📄 报告: {out_file}")

    if auto_open and not os.environ.get("UZI_NO_AUTO_OPEN"):
        try:
            import webbrowser
            webbrowser.open(out_file.as_uri())
        except Exception:
            pass

    return {
        "status": "completed",
        "tickers": tickers,
        "loaded": len(bundles),
        "report_path": str(out_file),
        "runtime_sec": dt,
    }

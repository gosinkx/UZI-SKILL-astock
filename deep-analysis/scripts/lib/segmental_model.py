"""Segmental Revenue Build-Up Model · v2.10 (feature branch).

## Why this exists

UZI 已有的 17 种机构方法里，DCF / 3-statement / IC Memo 都是**自上而下**：
从整体营收 × 增长率假设推未来。这套方法简洁，但遇到业务结构在转型的公司
就失真——例如：
  - 贵州茅台 直销比例 17% → 目标 50%+
  - 宁德时代 动力电池 vs 储能 vs 海外三条曲线增速完全不同
  - Credo（文章案例）Serdes 底座辐射 Retimer/DSP/AEC 三条线，又叠加 SiPh 收购

单一营收增速假设掩盖了这些业务结构分化。

**本模块做一件事**：
  把公司拆成 3-5 条业务/产品线，每条独立给 driver（价 × 量 × 市占 × 渗透），
  Bull/Base/Bear 三情景 × 3 年 projection，总量必须 reconcile 到当前营收。

## 设计原则（区别于 17 种现有方法）

  - **bottom-up** 不是 top-down
  - **thesis-aware** 围绕公司的核心转型叙事组织（而不是统一增速）
  - **agent 写 driver, 脚本做骨架 + 校验**
  - **必须对账**（sum(segment) 必须接近 total_revenue ±10%）

## 数据来源

  - `5_chain.main_business_breakdown` / `breakdown_top` — 业务分段原料
  - `1_financials.revenue_history` — 历史营收对账基线
  - `15_events` — 识别核心 inflection（收购/分拆/新产品/新市场）
  - `6_research` — 卖方研报对业务分段的看法

## 产物

    scripts/.cache/<ticker>/segmental_skeleton.json  (脚本生成)
      → agent 读，填入 driver assumptions
    scripts/.cache/<ticker>/segmental_model.json     (agent 写回)
      → 由 compute_segmental validate + 进入报告

Reference: 极客厨子《Credo Model 拆分》（微信公众号 2026-04）
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


# ═══════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════

@dataclass
class Segment:
    """一条业务/产品线的骨架."""
    name: str                          # e.g. "直销" / "批发" / "动力电池" / "AEC"
    latest_revenue_yi: float            # 最新一期营收（亿元）
    latest_share_pct: float             # 占比 %
    yoy_growth_pct: float | None = None  # 最近同比（若有）
    # v2.10 · 富字段（脚本自动填，来自 main_business_raw）
    gross_margin_pct: float | None = None     # 毛利率 %
    profit_share_pct: float | None = None     # 利润占比 %（vs 营收占比对比揭示高/低毛利段）
    revenue_history_yi: list[float] = field(default_factory=list)  # 该 segment 历史营收（季度或年）
    history_periods: list[str] = field(default_factory=list)        # 对应报告期
    # 以下字段由 agent 填
    drivers: list[str] = field(default_factory=list)           # e.g. ["ASP +5%", "shipment +20%"]
    thesis_tag: str = ""                # e.g. "growth_engine" / "declining" / "stable_cash_cow"
    bull_growth_3y_cagr: float | None = None  # 看多情景 3 年 CAGR
    base_growth_3y_cagr: float | None = None
    bear_growth_3y_cagr: float | None = None
    agent_note: str = ""


@dataclass
class SegmentalSkeleton:
    ticker: str
    name: str
    currency: str                      # CNY / HKD / USD
    total_revenue_latest_yi: float
    total_revenue_history_yi: list[float]
    segments: list[Segment]
    inflection_candidates: list[str]   # 从 15_events 里抽出的潜在拐点
    source_notes: list[str]            # 数据溯源 / 空洞提示

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "currency": self.currency,
            "total_revenue_latest_yi": self.total_revenue_latest_yi,
            "total_revenue_history_yi": self.total_revenue_history_yi,
            "segments": [asdict(s) for s in self.segments],
            "inflection_candidates": self.inflection_candidates,
            "source_notes": self.source_notes,
        }


# ═══════════════════════════════════════════════════════════════
# Discovery (script 层 · 不 LLM)
# ═══════════════════════════════════════════════════════════════

def discover_segments(raw: dict, min_share_pct: float = 3.0, max_segments: int = 6) -> SegmentalSkeleton:
    """从 raw_data.json 抽取业务分段骨架.

    参数:
      raw: run_real_test.collect_raw_data 返回的 dict (完整 raw_data.json)
      min_share_pct: 占比小于此的 segment 合并到"其他"
      max_segments: 最多抽 N 个具名 segment

    数据源优先级（从富到贫）：
      1. 5_chain.main_business_raw  — 最富（元级别营收 + 毛利率 + 分类类型 × 多期）
      2. 5_chain.main_business_breakdown  — value 是 decimal share (0-1)
      3. 5_chain.breakdown_top  — 老格式，value 是 pct (0-100)

    返回: SegmentalSkeleton (未填 driver，等 agent 介入)
    """
    dims = raw.get("dimensions") or {}
    basic = (dims.get("0_basic") or {}).get("data") or {}
    chain = (dims.get("5_chain") or {}).get("data") or {}
    fin = (dims.get("1_financials") or {}).get("data") or {}
    events = (dims.get("15_events") or {}).get("data") or {}

    name = basic.get("name") or raw.get("ticker", "")
    currency = fin.get("currency") or ("HKD" if basic.get("market") == "H" else ("USD" if basic.get("market") == "U" else "CNY"))

    rev_hist = fin.get("revenue_history") or []
    latest_rev = rev_hist[-1] if rev_hist else 0.0

    segments: list[Segment] = []
    source_notes: list[str] = []

    # ═══ Tier 1 · main_business_raw（最富的数据源）═══
    # 包含：分类类型（行业/产品/地区）× 主营构成 × 主营收入(元) × 收入比例(decimal) × 毛利率
    # 优先按"产品分类"（更细粒度），其次"行业分类"，最后"地区分类"
    mb_raw: list[dict] = chain.get("main_business_raw") or []
    if mb_raw:
        # 找最新报告期
        periods = sorted({str(r.get("报告日期", "")) for r in mb_raw if r.get("报告日期")}, reverse=True)
        latest_period = periods[0] if periods else None
        # 在该期内按分类类型优先级过滤
        if latest_period:
            same_period = [r for r in mb_raw if str(r.get("报告日期")) == latest_period]
            # 优先产品分类 > 行业分类 > 地区分类
            by_product = [r for r in same_period if "产品" in str(r.get("分类类型", ""))]
            by_industry = [r for r in same_period if "行业" in str(r.get("分类类型", ""))]
            chosen = by_product or by_industry or same_period
            classification = "按产品分类" if by_product else ("按行业分类" if by_industry else "mixed")

            other_share = 0.0
            # v2.10 · 拉历史数据供 sparkline 用（同 segment 多报告期）
            # 按报告期排序（旧→新），供每个 segment 画趋势
            all_periods_sorted = sorted({str(r.get("报告日期", "")) for r in mb_raw if r.get("报告日期")})

            for r in chosen:
                nm = str(r.get("主营构成", "")).strip()
                if not nm or nm in ("合计", "总计", "其他(补充)"):
                    continue
                rev_yuan = r.get("主营收入") or 0
                share_dec = r.get("收入比例") or 0
                try:
                    rev_yuan = float(rev_yuan)
                    share_dec = float(share_dec)
                except (ValueError, TypeError):
                    continue
                if rev_yuan <= 0:
                    continue
                share_pct = round(share_dec * 100, 2)
                if share_pct < min_share_pct:
                    other_share += share_pct
                    continue

                # 富字段：毛利率 + 利润占比
                gross_margin_pct = None
                profit_share_pct = None
                try:
                    gm = r.get("毛利率")
                    if gm is not None and not (isinstance(gm, float) and gm != gm):  # NaN filter
                        gross_margin_pct = round(float(gm) * 100, 1)
                except (ValueError, TypeError):
                    pass
                try:
                    ps = r.get("利润比例")
                    if ps is not None:
                        profit_share_pct = round(float(ps) * 100, 2)
                except (ValueError, TypeError):
                    pass

                # 富字段：该 segment 的历史营收（用同分类同 segment 的多期数据）
                hist_rev: list[float] = []
                hist_periods: list[str] = []
                same_seg_records = [
                    rr for rr in mb_raw
                    if str(rr.get("主营构成", "")).strip() == nm
                    and str(rr.get("分类类型", "")) == classification
                ]
                same_seg_records.sort(key=lambda x: str(x.get("报告日期", "")))
                for rr in same_seg_records:
                    try:
                        yi = float(rr.get("主营收入", 0)) / 1e8
                        if yi > 0:
                            hist_rev.append(round(yi, 2))
                            hist_periods.append(str(rr.get("报告日期", ""))[:10])
                    except (ValueError, TypeError):
                        continue

                seg = Segment(
                    name=nm[:20],
                    latest_revenue_yi=round(rev_yuan / 1e8, 2),
                    latest_share_pct=share_pct,
                    gross_margin_pct=gross_margin_pct,
                    profit_share_pct=profit_share_pct,
                    revenue_history_yi=hist_rev,
                    history_periods=hist_periods,
                )
                segments.append(seg)
                if len(segments) >= max_segments:
                    break
            if other_share >= min_share_pct:
                segments.append(Segment(
                    name="其他合计",
                    latest_revenue_yi=round(latest_rev * other_share / 100, 2),
                    latest_share_pct=round(other_share, 2),
                ))
            source_notes.append(f"分段来源: 5_chain.main_business_raw · {classification} · 报告期 {latest_period} · {len(segments)} 项")

    # ═══ Tier 2 · main_business_breakdown (value = decimal 0-1 share) ═══
    if not segments:
        mb_bd: list[dict] = chain.get("main_business_breakdown") or []
        if mb_bd:
            for item in mb_bd[:max_segments]:
                nm = str(item.get("name", "")).strip()
                if not nm or "补充" in nm:
                    continue
                v = item.get("value", 0) or 0
                try:
                    v = float(v)
                except (ValueError, TypeError):
                    continue
                # 判断格式：如果所有 value 都 <= 1，当 decimal 处理；否则当 pct
                share_pct = round(v * 100, 2) if v <= 1 else round(v, 2)
                if share_pct < min_share_pct:
                    continue
                seg_rev = round(latest_rev * share_pct / 100, 2) if latest_rev else 0
                segments.append(Segment(
                    name=nm[:20],
                    latest_revenue_yi=seg_rev,
                    latest_share_pct=share_pct,
                ))
            source_notes.append(f"分段来源: 5_chain.main_business_breakdown ({len(segments)} 项)")

    # ═══ Tier 3 · breakdown_top (legacy format, value = pct 0-100) ═══
    if not segments:
        breakdown_top: list[dict] = chain.get("breakdown_top") or []
        if breakdown_top:
            for item in breakdown_top[:max_segments]:
                nm = str(item.get("name", ""))[:20]
                share = float(item.get("value", 0) or 0)
                if share < min_share_pct:
                    continue
                seg_rev = round(latest_rev * share / 100, 2) if latest_rev else 0
                segments.append(Segment(name=nm, latest_revenue_yi=seg_rev, latest_share_pct=share))
            source_notes.append(f"分段来源: 5_chain.breakdown_top ({len(segments)} 项)")

    if not segments:
        source_notes.append("⚠️ 5_chain 无可用分段数据 — agent 需从 6_research 或 0_basic.main_business 文字描述手动归纳")

    # 3. 拐点候选 — 从 15_events 抓关键词
    inflection_candidates: list[str] = []
    evs = events.get("events") or events.get("recent_events") or []
    INFLECTION_KEYWORDS = ["收购", "分拆", "剥离", "重组", "合并", "新品", "上市", "产能投产",
                          "海外", "出海", "转型", "高端化", "客户突破", "订单", "中标",
                          "ODM", "OEM", "自研", "专利", "集采", "降价", "提价", "扩产", "投产"]
    for ev in evs[:30]:
        title = str(ev.get("title") or ev.get("name") or "") if isinstance(ev, dict) else str(ev)
        for kw in INFLECTION_KEYWORDS:
            if kw in title:
                inflection_candidates.append(title[:80])
                break
        if len(inflection_candidates) >= 8:
            break

    if not inflection_candidates:
        source_notes.append("⚠️ 15_events 里未抽到拐点关键词 — agent 需从 6_research 或 14_moat 补")

    return SegmentalSkeleton(
        ticker=raw.get("ticker", ""),
        name=name,
        currency=currency,
        total_revenue_latest_yi=round(latest_rev, 2),
        total_revenue_history_yi=[round(x, 2) for x in rev_hist],
        segments=segments,
        inflection_candidates=inflection_candidates,
        source_notes=source_notes,
    )


# ═══════════════════════════════════════════════════════════════
# Validation (script 层 · 防止 agent 写离谱模型)
# ═══════════════════════════════════════════════════════════════

def validate_model(filled: dict, raw: dict) -> dict:
    """校验 agent 填完的 segmental 模型.

    核心规则：
      1. sum(segment.latest_revenue_yi) 必须接近 total_revenue_latest_yi ±10%
      2. 每个 segment 的 bull/base/bear CAGR 必须合理（bull > base > bear）
      3. Base 情景 3 年后总营收 growth 不能 > 100%（除非明确 note 有收购）

    返回: {
        "passed": bool,
        "errors": [...],
        "warnings": [...],
        "summary": {...}
    }
    """
    errors: list[str] = []
    warnings: list[str] = []
    summary: dict = {}

    dims = raw.get("dimensions") or {}
    fin = (dims.get("1_financials") or {}).get("data") or {}
    total_rev = (fin.get("revenue_history") or [0])[-1] if fin.get("revenue_history") else 0

    segments = filled.get("segments") or []
    if not segments:
        errors.append("segments 为空")
        return {"passed": False, "errors": errors, "warnings": warnings, "summary": summary}

    sum_rev = sum(s.get("latest_revenue_yi", 0) or 0 for s in segments)
    reconciliation_pct = abs(sum_rev - total_rev) / max(total_rev, 1) * 100 if total_rev else 0
    summary["total_actual"] = total_rev
    summary["sum_segments"] = round(sum_rev, 2)
    summary["reconciliation_gap_pct"] = round(reconciliation_pct, 2)

    # 规则 1: 对账
    if total_rev > 0 and reconciliation_pct > 10:
        errors.append(
            f"segments 总和 {sum_rev:.1f} 亿 vs 实际 revenue {total_rev:.1f} 亿 差 {reconciliation_pct:.0f}%（阈值 10%）"
        )

    # 规则 2: CAGR 单调性
    for s in segments:
        bull = s.get("bull_growth_3y_cagr")
        base = s.get("base_growth_3y_cagr")
        bear = s.get("bear_growth_3y_cagr")
        if bull is None or base is None or bear is None:
            warnings.append(f"segment {s.get('name')!r} 缺 3 情景 CAGR，agent 未填完")
            continue
        if not (bull >= base >= bear):
            errors.append(
                f"segment {s.get('name')!r} CAGR 不单调: bull={bull} base={base} bear={bear}"
            )

    # 规则 3: Base 情景总增速合理
    base_3y_total_growth = 0
    for s in segments:
        base = s.get("base_growth_3y_cagr") or 0
        share = s.get("latest_share_pct", 0) / 100
        base_3y_total_growth += share * ((1 + base / 100) ** 3 - 1) * 100
    summary["base_3y_total_growth_pct"] = round(base_3y_total_growth, 1)
    if base_3y_total_growth > 100:
        warnings.append(
            f"Base 情景 3 年总营收增速 {base_3y_total_growth:.0f}%（>100%）—— 需要明确收购/新业务 note 支撑"
        )

    # 规则 4: 每个 segment 必须有 drivers + thesis_tag
    for s in segments:
        if not s.get("drivers"):
            warnings.append(f"segment {s.get('name')!r} 未填 drivers（价/量/市占/渗透）")
        if not s.get("thesis_tag"):
            warnings.append(f"segment {s.get('name')!r} 未填 thesis_tag")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


# ═══════════════════════════════════════════════════════════════
# Rendering helpers (供 assemble_report 或 agent 直接用)
# ═══════════════════════════════════════════════════════════════

def render_skeleton_markdown(skel: SegmentalSkeleton) -> str:
    """Human-readable skeleton 格式，给 agent 看着填."""
    lines = [
        f"# Segmental Build-Up · {skel.name} ({skel.ticker})",
        f"",
        f"**总营收最新**: {skel.total_revenue_latest_yi} 亿 {skel.currency}",
        f"**历史营收（近 6 年）**: {skel.total_revenue_history_yi}",
        f"",
        f"## 业务分段（{len(skel.segments)} 条）",
    ]
    for i, s in enumerate(skel.segments, 1):
        lines.append(f"\n### {i}. {s.name}")
        lines.append(f"  - 最新营收: {s.latest_revenue_yi} 亿（占比 {s.latest_share_pct}%）")
        lines.append(f"  - 同比: {s.yoy_growth_pct if s.yoy_growth_pct is not None else '—'}")
        lines.append(f"  - [agent 待填] drivers: ")
        lines.append(f"  - [agent 待填] thesis_tag: ")
        lines.append(f"  - [agent 待填] Bull 3Y CAGR: __% · Base __% · Bear __%")
    if skel.inflection_candidates:
        lines.append(f"\n## 潜在拐点候选（来自 15_events）")
        for c in skel.inflection_candidates[:6]:
            lines.append(f"  - {c}")
    if skel.source_notes:
        lines.append(f"\n## 数据溯源注记")
        for n in skel.source_notes:
            lines.append(f"  - {n}")
    return "\n".join(lines)

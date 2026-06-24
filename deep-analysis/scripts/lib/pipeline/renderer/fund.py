"""FundRenderer · 基金经理抄作业 section · 从 assemble_report.py 迁移.

v2.15.x 教训集合：
- v2.15.1: lite 行不能当 full-card 渲染（return_5y=None 时跳）
- v2.15.1: lite 按 fund_code 去重 + cap 30
- v2.15.1: MANAGER_AVATAR_MAP · 但只在 fetch_fund_manager_name 成功时管用（SSL 封即失效）
- v2.15.2（本次）: 新增 FUND_CODE_TO_MANAGER 反查 · fund_code → manager_name · 解决"抄作业没头像"
"""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


# v2.15.2 · fund_code → manager_name 备份映射
# 当 fund.eastmoney.com SSL 封 fetch_fund_manager_name 挂时用这个
# 仅收录中国公募价值派 / 成长派明星经理的核心基金 · 覆盖 ~60% 高知名度持仓
FUND_CODE_TO_MANAGER = {
    # 朱少醒 · 富国天惠（A/B 161005 · C 003494 · D 022645）
    "161005": "朱少醒", "003494": "朱少醒", "022645": "朱少醒",
    # 张坤 · 易方达蓝筹 (005827) · 易方达亚洲 (118001) · 易方达优质 (110011)
    "005827": "张坤", "118001": "张坤", "110011": "张坤",
    # 谢治宇 · 兴全合润 (163406) · 兴全社会责任 (340007)
    "163406": "谢治宇", "340007": "谢治宇",
    # 冯柳 · 高毅邻山 (不公开) · 只能看公开披露
    # 邓晓峰 · 高毅晓峰
    # 田瑀 · 中泰星宇价值成长 (A 012001 / C 012002)
    "012001": "田瑀", "012002": "田瑀",
    # 刘彦春 · 景顺长城新兴成长 (260108) · 景顺长城鼎益 (162605)
    "260108": "刘彦春", "162605": "刘彦春",
    # 葛兰 · 中欧医疗健康 (A 003095 / C 003096)
    "003095": "葛兰", "003096": "葛兰",
    # 朱少醒 富国天益 (100056)
    "100056": "朱少醒",
    # 劳杰男 · 汇添富价值精选 (519069)
    "519069": "劳杰男",
    # 傅鹏博 · 睿远成长价值 (007119)
    "007119": "傅鹏博",
    # 萧楠 · 易方达消费行业 (110022)
    "110022": "萧楠",
}


# 头像 svg slug · 本地 avatars/*.svg 有的
MANAGER_AVATAR_SLUG = {
    "张坤": "zhangkun",
    "谢治宇": "xiezhiyu",
    "朱少醒": "zhushaoxing",
    "冯柳": "fengliu",
    "邓晓峰": "dengxiaofeng",
    # 扩展（后续 Phase 补 svg）
    # "田瑀": "tianyu",
    # "刘彦春": "liuyanchun",
    # "葛兰": "gelan",
    # "劳杰男": "laojienan",
    # "傅鹏博": "fupengbo",
    # "萧楠": "xiaonan",
}


def resolve_manager(fund_code: str, current_name: str = "—") -> str:
    """按 fund_code 查真实经理名 · 用于 fetch_fund_manager_name 挂掉的 fallback.

    优先级：
    1. current_name 已知（非"—" / 非空）→ 返 current_name
    2. FUND_CODE_TO_MANAGER 映射命中 → 返映射值
    3. 都没有 → 返 "—"
    """
    if current_name and current_name not in ("—", "-", "", None, "n/a"):
        return current_name
    return FUND_CODE_TO_MANAGER.get(fund_code, "—")


def resolve_avatar(manager_name: str) -> str:
    """按 manager_name 查 avatar svg slug · 返空表示用文字 placeholder."""
    if not manager_name or manager_name in ("—", "-"):
        return ""
    return MANAGER_AVATAR_SLUG.get(manager_name, "")


def enrich_manager(m: dict) -> dict:
    """给 fund_managers 列表里单条记录补经理名 + 头像 · in-place 返回 copy.

    这是 fetch_fund_holders 返回后的 post-processing · 本次重构新加的动作.
    """
    out = dict(m)  # copy
    fund_code = out.get("fund_code", "")
    current_name = out.get("name", "")
    resolved = resolve_manager(fund_code, current_name)
    if resolved != current_name:
        out["name"] = resolved
        out["_name_resolved_by"] = "fund_code_map"
    if resolved and resolved not in ("—", "-"):
        avatar = resolve_avatar(resolved)
        if avatar and not out.get("avatar"):
            out["avatar"] = avatar
    return out


# ─── 实际 renderer（迁移自 assemble_report.render_fund_managers）──────

class FundRenderer(SectionRenderer):
    """基金经理抄作业 · 对应 6_fund_holders."""

    section_id = "fund_managers"
    section_title = "大佬抄作业 · 公募基金持仓"

    # 设计参数（从 assemble_report.py 拷出来）
    INITIAL_FULL_CAP = 6        # full card 最多 6 张
    LITE_CAP = 30               # lite compact row 最多 30 行

    def render_full(self, ctx: RenderContext) -> str:
        """渲染 · 内部自己按 _row_type 分 full / lite."""
        managers = ctx.data.get("fund_managers") or []
        if not managers:
            return self.render_gap(ctx, reason="无公募基金持仓数据")

        # v2.15.2 · 先 enrich（补经理名 + 头像）· 这是新加的
        enriched = [enrich_manager(m) for m in managers]

        # 分 full / lite
        full_mgrs = [m for m in enriched
                     if m.get("_row_type") == "full" and m.get("return_5y") is not None]
        lite_mgrs = [m for m in enriched
                     if m.get("_row_type") == "lite" or m.get("return_5y") is None]

        # v2.15.1 · lite 按 fund_code 去重 + cap
        lite_deduped = _dedupe_by_code(lite_mgrs)
        lite_capped = lite_deduped[: self.LITE_CAP]
        lite_overflow = max(0, len(lite_deduped) - self.LITE_CAP)

        # 渲染 full cards（最多 6）
        full_cards = [self._render_full_card(m) for m in full_mgrs[: self.INITIAL_FULL_CAP]]

        # 渲染 compact rows
        compact_rows = [
            self._render_compact_row(m, rank=i + 1 + len(full_cards))
            for i, m in enumerate(lite_capped)
        ]

        header = self._render_header(
            total=len(enriched),
            full_count=len(full_mgrs),
            lite_count=len(lite_deduped),
            overflow=lite_overflow,
        )

        grid = f'<div class="fund-mgr-grid">{"".join(full_cards)}</div>' if full_cards else ""
        compact_html = ""
        if compact_rows:
            compact_html = (
                f'<div class="fund-compact-list">'
                f'<div class="fund-compact-head">'
                f'<span class="fc-h-rank">#</span>'
                f'<span class="fc-h-avatar"></span>'
                f'<span class="fc-h-name">基金经理 / 基金</span>'
                f'<span class="fc-h-metric">持仓</span>'
                f'<span class="fc-h-link"></span>'
                f'</div>'
                f'{"".join(compact_rows)}'
                f'</div>'
            )

        return f'<section id="{self.section_id}">{header}{grid}{compact_html}</section>'

    # ─── private helpers ──────────────────────────────────

    def _render_header(self, total: int, full_count: int, lite_count: int, overflow: int) -> str:
        total_display = total + overflow  # lite_overflow 隐藏的也算总数
        if lite_count > 0:
            overflow_note = f"（另有 {overflow} 家未列 · 点基金链接自行查）" if overflow > 0 else ""
            return (
                f'<div class="fund-mgr-header">✨ <strong>{total_display} 家公募基金</strong>持有本股 · '
                f'头部 <strong>{full_count}</strong> 家有完整 5Y 业绩，'
                f'其余 <strong>{lite_count}</strong> 家按持仓占比列出{overflow_note}</div>'
            )
        return (
            f'<div class="fund-mgr-header">✨ <strong>{full_count} 位公募基金经理</strong>'
            f'持有本股 · 按 5 年累计收益排序 · 你可以直接"抄作业"</div>'
        )

    def _render_full_card(self, m: dict) -> str:
        name = m.get("name") or "—"
        fund_name = m.get("fund_name") or "—"
        avatar = m.get("avatar") or ""
        position = m.get("position_pct") or 0
        rank = m.get("rank_in_fund", 0)
        quarters = m.get("holding_quarters", 0)
        trend = m.get("position_trend", "持平")
        trend_icon = "📈" if trend == "加仓" else "📉" if trend == "减仓" else "➡️"
        trend_color = "#16a34a" if trend == "加仓" else "#dc2626" if trend == "减仓" else "#64748b"

        ret_5y = m.get("return_5y") or 0
        ann_5y = m.get("annualized_5y") or 0
        max_dd = m.get("max_drawdown") or 0
        sharpe = m.get("sharpe") or 0
        peer_rank = m.get("peer_rank_pct") or 50

        ret_color = "#16a34a" if ret_5y > 0 else "#dc2626"
        dd_color = "#16a34a" if max_dd > -20 else "#f59e0b" if max_dd > -40 else "#dc2626"
        sharpe_color = "#16a34a" if sharpe > 1 else "#f59e0b" if sharpe > 0.5 else "#dc2626"
        rank_color = "#16a34a" if peer_rank < 20 else "#f59e0b" if peer_rank < 50 else "#dc2626"

        if avatar:
            avatar_html = (
                f'<img src="avatars/{avatar}.svg" style="width:54px;height:54px;'
                f'image-rendering:pixelated;border:2px solid #d97706;'
                f'border-radius:8px;background:#fff;flex-shrink:0">'
            )
        else:
            initial = (name[0] if name and name != "—" else "?")
            avatar_html = (
                f'<div style="width:54px;height:54px;background:#fef3c7;'
                f'border:2px solid #d97706;border-radius:8px;'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-family:Fira Sans;font-size:20px;font-weight:900;'
                f'color:#d97706;flex-shrink:0">{initial}</div>'
            )

        stars = "⭐" * max(1, min(5, int((100 - peer_rank) / 20) + 1))
        fund_code = m.get("fund_code", "")
        fund_url = m.get("fund_url") or f"https://fund.eastmoney.com/{fund_code}.html"

        return f'''<div class="fund-card">
  <div class="fund-header" style="display:flex;gap:12px;align-items:center">
    {avatar_html}
    <div style="flex:1;min-width:0">
      <div class="fund-manager-name"><strong>{name}</strong> <span class="fund-stars">{stars}</span></div>
      <div class="fund-name">{fund_name}</div>
      <div class="fund-meta">持本股 {quarters} 季 · 位列第 {rank} 大 · 占基金 {position}% · <span style="color:{trend_color};font-weight:700">{trend_icon} {trend}</span></div>
    </div>
  </div>
  <div class="fund-metrics-grid">
    <div class="fund-metric"><div class="fm-label">5 年累计</div><div class="fm-value" style="color:{ret_color}">{"+" if ret_5y > 0 else ""}{ret_5y:.1f}%</div></div>
    <div class="fund-metric"><div class="fm-label">年化</div><div class="fm-value">{"+" if ann_5y > 0 else ""}{ann_5y:.1f}%</div></div>
    <div class="fund-metric"><div class="fm-label">最大回撤</div><div class="fm-value" style="color:{dd_color}">{max_dd:.1f}%</div></div>
    <div class="fund-metric"><div class="fm-label">夏普比率</div><div class="fm-value" style="color:{sharpe_color}">{sharpe:.2f}</div></div>
  </div>
  <a href="{fund_url}" target="_blank" rel="noopener" class="fund-link">查看基金 →</a>
</div>'''

    def _render_compact_row(self, m: dict, rank: int) -> str:
        name = m.get("name") or "—"
        fund_name = m.get("fund_name") or "—"
        fund_code = m.get("fund_code", "")
        avatar = m.get("avatar") or ""
        position_pct = m.get("position_pct") or 0
        fund_url = m.get("fund_url") or f"https://fund.eastmoney.com/{fund_code}.html"

        badge_style = (
            "background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff"
            if rank <= 3 else
            "background:#e2e8f0;color:#475569" if rank <= 10 else
            "background:#f1f5f9;color:#64748b"
        )

        if avatar:
            avatar_html = f'<img src="avatars/{avatar}.svg" class="fc-avatar" alt="">'
        else:
            # v2.15.2 · 没 avatar 时用 name 首字（"朱" / "张"），不再默认 "?"
            initial = (name[0] if name and name not in ("—", "-") else
                       fund_name[0] if fund_name and fund_name not in ("—", "-") else "?")
            avatar_html = f'<div class="fc-avatar fc-avatar-ph">{initial}</div>'

        # lite 行展示："持仓 X%" · 点进去看业绩
        metric_html = (
            f'<span class="fc-return" style="color:#64748b">持仓 {position_pct:.2f}%</span>'
            f'<span class="fc-rank-pct" style="color:#94a3b8;font-size:10px">点→查业绩</span>'
        )

        name_display = name if name not in ("—", "-") else fund_name
        fund_display = f"代码 {fund_code}" if name not in ("—", "-") else ""

        return f'''<div class="fund-compact-row">
  <span class="fc-rank" style="{badge_style}">{rank}</span>
  {avatar_html}
  <div class="fc-info">
    <div class="fc-name">{name_display}</div>
    <div class="fc-fund">{fund_display}</div>
  </div>
  {metric_html}
  <a href="{fund_url}" target="_blank" rel="noopener" class="fc-link" title="查看基金详情">→</a>
</div>'''


def _dedupe_by_code(mgrs: list[dict]) -> list[dict]:
    """按 fund_code 去重 · 保留 position_pct 最高的那条 · 按 pct 倒序."""
    by_code = {}
    for m in sorted(mgrs, key=lambda x: -(x.get("position_pct") or 0)):
        code = m.get("fund_code")
        if not code:
            continue
        if code not in by_code:
            by_code[code] = m
    return list(by_code.values())

"""MoatRenderer · 护城河 section · 对应 14_moat.

Phase 3 迁移 · 含 v2.15.1 _SUPERSTAR_POLLUTERS 逻辑（那是 fetcher 侧的）·
render 这里主要展示四力评分 + 文字描述 + 数据溯源.
"""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


# 四力评分阈值
SCORE_COLORS = {
    "strong": "#16a34a",   # ≥ 7
    "medium": "#f59e0b",   # 4-6
    "weak": "#dc2626",     # ≤ 3
}


def _score_color(score: int) -> str:
    if score >= 7:
        return SCORE_COLORS["strong"]
    if score <= 3:
        return SCORE_COLORS["weak"]
    return SCORE_COLORS["medium"]


class MoatRenderer(SectionRenderer):
    section_id = "moat"
    section_title = "🏰 护城河四力（intangible / switching / network / scale）"

    def render_full(self, ctx: RenderContext) -> str:
        data = ctx.data
        scores = data.get("scores") or {}

        # 四维展示
        fields = [
            ("intangible", "无形资产", data.get("intangible") or "—"),
            ("switching", "转换成本", data.get("switching") or "—"),
            ("network", "网络效应", data.get("network") or "—"),
            ("scale", "规模优势", data.get("scale") or "—"),
        ]

        items_html = []
        for key, zh_label, text in fields:
            s = scores.get(key, 5)
            color = _score_color(s)
            body_preview = text[:200] if text and text != "—" else "数据不足"
            items_html.append(f'''<div class="moat-item">
  <div class="moat-head">
    <strong>{zh_label}</strong>
    <span class="moat-score" style="color:{color};font-weight:700">{s}/10</span>
  </div>
  <div class="moat-body" style="font-size:12px;color:#475569;margin-top:6px">{body_preview}</div>
</div>''')

        rd_summary = data.get("rd_summary") or ""
        rd_block = ""
        if rd_summary and rd_summary != "—":
            rd_block = f'<div class="moat-rd" style="margin-top:12px;padding:10px;background:#f8fafc;border-left:3px solid #d97706"><strong>R&D 摘要</strong>：{rd_summary[:300]}</div>'

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <div class="moat-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
    {"".join(items_html)}
  </div>
  {rd_block}
</section>'''

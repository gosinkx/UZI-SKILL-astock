"""EventsRenderer · 事件驱动 section · 对应 15_events."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class EventsRenderer(SectionRenderer):
    section_id = "events"
    section_title = "📅 事件驱动 · 近期催化与风险"

    def render_full(self, ctx: RenderContext) -> str:
        data = ctx.data
        timeline = data.get("event_timeline") or []
        catalysts = data.get("catalyst") or data.get("catalysts") or []
        warnings = data.get("warnings") or []
        news = data.get("recent_news") or []

        if not timeline and not catalysts and not warnings and not news:
            return self.render_gap(ctx, "无事件数据")

        # 时间线（Top 8）
        timeline_html = ""
        if timeline:
            items = "".join(f'<li>{ev}</li>' for ev in timeline[:8] if isinstance(ev, str))
            timeline_html = f'<div><h3>时间线</h3><ul style="font-size:12px">{items}</ul></div>'

        # catalysts
        catalyst_html = ""
        if catalysts:
            items = []
            for c in catalysts[:5]:
                if not isinstance(c, dict):
                    continue
                items.append(f'<li><strong>{c.get("date", "—")}</strong> · {c.get("event", "") or c.get("title", "")}</li>')
            if items:
                catalyst_html = f'<div><h3>🟢 催化剂</h3><ul style="font-size:12px">{"".join(items)}</ul></div>'

        # warnings
        warning_html = ""
        if warnings:
            items = "".join(f'<li style="color:#dc2626">{w}</li>' for w in warnings[:5] if isinstance(w, str))
            warning_html = f'<div><h3>🔴 警示</h3><ul style="font-size:12px">{items}</ul></div>'

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  {catalyst_html}
  {warning_html}
  {timeline_html}
</section>'''

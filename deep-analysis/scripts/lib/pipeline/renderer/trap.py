"""TrapRenderer · 杀猪盘排查 · 对应 18_trap."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class TrapRenderer(SectionRenderer):
    section_id = "trap"
    section_title = "⚠️ 杀猪盘排查"

    def render_full(self, ctx: RenderContext) -> str:
        d = ctx.data
        risk_score = d.get("risk_score") or 0
        pump_signals = d.get("pump_dump_signals") or []
        warning_flags = d.get("warning_flags") or []
        trap_likelihood = d.get("trap_likelihood") or "—"

        # 风险等级颜色
        if isinstance(risk_score, (int, float)) and risk_score > 60:
            color = "#dc2626"
            level = "高风险"
        elif isinstance(risk_score, (int, float)) and risk_score > 30:
            color = "#f59e0b"
            level = "中风险"
        else:
            color = "#16a34a"
            level = "低风险"

        flags_html = ""
        if warning_flags:
            items = "".join(f'<li style="color:#dc2626">{f}</li>' for f in warning_flags[:8] if isinstance(f, str))
            if items:
                flags_html = f'<div><strong>警示标记</strong><ul style="font-size:12px">{items}</ul></div>'

        signals_html = ""
        if pump_signals:
            items = "".join(f'<li>{s}</li>' for s in pump_signals[:5] if isinstance(s, str))
            if items:
                signals_html = f'<div><strong>拉升信号</strong><ul style="font-size:12px">{items}</ul></div>'

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <div style="font-size:13px">
    <div>风险分 · <span style="color:{color};font-weight:700">{risk_score}/100</span> · {level}</div>
    <div>杀猪盘可能性 · {trap_likelihood}</div>
    {signals_html}
    {flags_html}
  </div>
</section>'''

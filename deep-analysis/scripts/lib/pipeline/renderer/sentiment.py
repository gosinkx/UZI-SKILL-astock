"""SentimentRenderer · 舆情 section · 对应 17_sentiment."""
from __future__ import annotations

from .base import SectionRenderer, RenderContext


class SentimentRenderer(SectionRenderer):
    section_id = "sentiment"
    section_title = "🗣️ 舆情温度"

    def render_full(self, ctx: RenderContext) -> str:
        data = ctx.data
        heat_raw = data.get("thermometer_value") or 0
        positive_pct = data.get("positive_pct") or "—"
        label = data.get("sentiment_label") or "—"
        big_v = data.get("big_v_mentions") or "—"

        # 热榜命中 (v2.12)
        hot_trend = data.get("hot_trend_mentions") or {}
        hot_hits = data.get("hot_trend_hit_count") or 0

        # 新闻命中 (v2.13.7)
        news_ok = data.get("news_sources_ok") or 0
        news_hits = data.get("news_total_hits") or 0

        # 热度 bar
        bar_width = min(100, int(heat_raw)) if isinstance(heat_raw, (int, float)) else 0
        bar_color = "#dc2626" if bar_width > 80 else "#f59e0b" if bar_width > 50 else "#16a34a"

        return f'''<section id="{self.section_id}">
  <h2>{self.section_title}</h2>
  <div class="sentiment-bar" style="margin:8px 0">
    <div style="font-size:12px;color:#64748b">热度 {bar_width}/100 · {label}</div>
    <div style="background:#f1f5f9;border-radius:4px;overflow:hidden;margin-top:4px">
      <div style="background:{bar_color};height:8px;width:{bar_width}%"></div>
    </div>
  </div>
  <div class="sentiment-grid" style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:8px;font-size:12px">
    <div>正面占比 · <strong>{positive_pct}</strong></div>
    <div>大V 提及 · <strong>{big_v}</strong></div>
    <div>热榜命中 · <strong>{hot_hits}</strong></div>
    <div>新闻源 · <strong>{news_ok}/4 · {news_hits} 条</strong></div>
  </div>
</section>'''

"""抽象 SectionRenderer · 每个报告 section 一个独立 renderer.

设计目标：
1. 把 assemble_report.py (3100+ 行) 按 section 拆散 · 每个 < 400 行
2. 每个 renderer 有明确的 `expected_data_shape` (schema 声明)
3. 支持 3 种渲染模式：full / lite / gap (数据缺失)
4. 不碰全局状态 · 输入 RenderContext · 输出 html string
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RenderContext:
    """Renderer 输入上下文 · 所有 section 共享."""

    ticker: str
    name: str                             # 中文名（如"中密控股"）
    market: str = "A"                     # A / H / U
    data: dict[str, Any] = field(default_factory=dict)  # section 自己的数据
    meta: dict[str, Any] = field(default_factory=dict)  # raw meta（如 industry/market_cap/now）
    quality: str = "full"                 # full / partial / missing / error


class SectionRenderer(ABC):
    """每个 section 继承 · 子类实现 render_{full,lite,gap}."""

    section_id: str = ""                  # 如 "fund_managers" / "moat" · 用于 DOM anchor
    section_title: str = ""               # 中文标题

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.section_id:
            raise TypeError(f"{cls.__name__} 必须声明 section_id")

    def render(self, ctx: RenderContext) -> str:
        """顶层渲染 · 根据 quality 分派到 render_full/lite/gap · 子类通常不覆盖."""
        q = ctx.quality or "full"
        if q == "error":
            return self.render_gap(ctx, reason="fetcher 失败")
        if q == "missing":
            return self.render_gap(ctx, reason="数据未抓到")
        if q == "partial":
            # partial 走 lite · 展示已有数据 + 标注 gap
            return self.render_lite(ctx)
        return self.render_full(ctx)

    @abstractmethod
    def render_full(self, ctx: RenderContext) -> str:
        """完整数据渲染 · 子类必须实现."""
        raise NotImplementedError

    def render_lite(self, ctx: RenderContext) -> str:
        """部分数据渲染 · 子类可覆盖 · 默认等同 full."""
        return self.render_full(ctx)

    def render_gap(self, ctx: RenderContext, reason: str = "数据不足") -> str:
        """数据缺失渲染 · 显示占位 + 为什么 · 子类可覆盖."""
        return (
            f'<section id="{self.section_id}" class="section-gap">'
            f'<h2>{self.section_title or self.section_id}</h2>'
            f'<div class="gap-notice" style="padding:24px;text-align:center;color:#94a3b8;font-size:12px">'
            f'⚠️ {reason}（{self.section_id}）</div>'
            f'</section>'
        )

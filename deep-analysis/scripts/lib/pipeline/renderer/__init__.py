"""Section renderers · 从 assemble_report.py (3100+ 行巨文件) 逐步拆出.

迁移顺序：
- fund.py ✅ Phase 1（示范迁移 · 对应 v2.15.1 bug 温床）
- moat.py (TODO Phase 2)
- peers.py (TODO Phase 2)
- industry.py (TODO Phase 2)
- ...
"""
from .base import SectionRenderer, RenderContext
from .registry import RENDERER_REGISTRY, get_renderer, list_renderers

__all__ = ["SectionRenderer", "RenderContext", "RENDERER_REGISTRY", "get_renderer", "list_renderers"]

"""pipeline.synthesize · stage2 merge · delegate wrapper (Phase 6a).

**本阶段不重写 legacy 逻辑** · 仅提供统一调用入口。
Phase 6（未来 session）：render 循环调 RENDERER_REGISTRY · assemble_report 逻辑挪进来.

当前策略：直接调 legacy stage2 · 无任何改动.

安全保证：assemble_report.py 不改 · 只从外部调用 · 零业务影响.
"""
from __future__ import annotations


def synthesize_and_render(ticker: str) -> str:
    """给定已有 .cache/<ticker>/{raw_data,dimensions,panel,agent_analysis}.json · 调 legacy stage2 生成报告.

    返回：HTML 报告绝对路径 str.
    """
    import run_real_test as rrt
    return rrt.stage2(ticker)

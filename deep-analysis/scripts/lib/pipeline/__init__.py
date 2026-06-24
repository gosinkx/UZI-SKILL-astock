"""v3.0.0 · 管道式架构（pipeline architecture）· coexists with legacy code.

这是 UZI-Skill 重构 Phase 1：建立标准化骨架 · 老代码继续跑 · 新 fetcher/renderer
按 MIGRATION.md 逐步迁移。

核心概念：
- `schema.py` · DimResult / FetcherSpec / Quality 枚举 · 统一数据容器
- `base_fetcher.py` · BaseFetcher ABC · 所有新 fetcher 继承
- `validators.py` · 统一空值约定（is_empty_value / is_data_gap）
- `renderer/base.py` · SectionRenderer · 每个 section 独立文件
- `renderer/fund.py` · 第一个迁移示范（抽自 assemble_report.render_fund_managers）

老代码入口（`run_real_test.py`, `assemble_report.py`, 22 个 `fetch_*.py`）保持工作 ·
迁移过程零回归。
"""

from .schema import DimResult, FetcherSpec, Quality
from .base_fetcher import BaseFetcher
from .validators import is_empty_value, is_data_gap
from .collect import collect, is_pipeline_enabled
from .run import run_pipeline

__all__ = [
    "DimResult",
    "FetcherSpec",
    "Quality",
    "BaseFetcher",
    "is_empty_value",
    "is_data_gap",
    "collect",
    "is_pipeline_enabled",
    "run_pipeline",
]

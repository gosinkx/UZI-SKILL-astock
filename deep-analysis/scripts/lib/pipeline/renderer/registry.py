"""Renderer 注册表 · dim_key → SectionRenderer · Phase 3+5 完成 21 个 renderer."""
from __future__ import annotations

from .basic_header import BasicHeaderRenderer
from .capital_flow import CapitalFlowRenderer
from .chain import ChainRenderer
from .contests import ContestsRenderer
from .events import EventsRenderer
from .financials import FinancialsRenderer
from .fund import FundRenderer
from .futures import FuturesRenderer
from .governance import GovernanceRenderer
from .industry import IndustryRenderer
from .kline import KlineRenderer
from .lhb import LhbRenderer
from .macro import MacroRenderer
from .materials import MaterialsRenderer
from .moat import MoatRenderer
from .peers import PeersRenderer
from .policy import PolicyRenderer
from .research import ResearchRenderer
from .sentiment import SentimentRenderer
from .trap import TrapRenderer
from .valuation import ValuationRenderer

# 全 21 个 renderer 已注册（Phase 3 + Phase 5）
RENDERER_REGISTRY: dict[str, type] = {
    "0_basic": BasicHeaderRenderer,
    "1_financials": FinancialsRenderer,
    "2_kline": KlineRenderer,
    "3_macro": MacroRenderer,
    "4_peers": PeersRenderer,
    "5_chain": ChainRenderer,
    "6_fund_holders": FundRenderer,
    "6_research": ResearchRenderer,
    "7_industry": IndustryRenderer,
    "8_materials": MaterialsRenderer,
    "9_futures": FuturesRenderer,
    "10_valuation": ValuationRenderer,
    "11_governance": GovernanceRenderer,
    "12_capital_flow": CapitalFlowRenderer,
    "13_policy": PolicyRenderer,
    "14_moat": MoatRenderer,
    "15_events": EventsRenderer,
    "16_lhb": LhbRenderer,
    "17_sentiment": SentimentRenderer,
    "18_trap": TrapRenderer,
    "19_contests": ContestsRenderer,
}


def get_renderer(dim_key: str):
    """根据 dim_key 取 renderer 实例 · 未注册返 None."""
    cls = RENDERER_REGISTRY.get(dim_key)
    return cls() if cls else None


def list_renderers() -> list[str]:
    return sorted(RENDERER_REGISTRY.keys())

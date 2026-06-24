"""Investor Knowledge Base — 真实持仓 / 市场偏好 / 行业亲和度 / 不适用场景。

每个投资者不是一个"规则引擎"，而是一个有血有肉的人。
这个文件记录他们的真实世界约束：
  - 实际持仓 / 曾经持仓的股票
  - 能力圈（哪些市场/行业他们真的会看）
  - 不能力圈（哪些市场/行业他们绝对不碰）
  - 对特定公司的已知态度（公开发言）

规则引擎（investor_criteria.py）给出量化骨架分，
本文件给出"这个人会不会真的看这只票"的现实检验。

evaluator 调用顺序：
  1. market_filter() — 这个人看不看这个市场？游资不看美股
  2. affinity_bonus() — 持仓/行业亲和度加减分
  3. rule_engine_score — investor_criteria 的量化分
  4. 最终分 = clamp(rule_score + affinity_adjust, 0, 100)
"""
from __future__ import annotations

from typing import Any


# ═══════════════════════════════════════════════════════════════
# 1. MARKET SCOPE — 每个投资者能看哪些市场
# ═══════════════════════════════════════════════════════════════
# "all" = 全球都看, "A" = 只看 A 股, "US" = 只看美股
# "A+HK" = A 股 + 港股, etc.

MARKET_SCOPE: dict[str, str] = {
    # ═══════════════════════════════════════════════════════
    # 设计原则:
    #   - 投资方法论是通用的（巴菲特的 ROE 标准对 A 股同样有效）
    #   - 只有"交易执行"有市场限制的才 skip（游资只做 A 股 T+1 打板）
    #   - 大多数投资者 → "all"（可以评价任何市场的股票）
    # ═══════════════════════════════════════════════════════

    # Group A · Classic Value — 方法论全球通用
    "buffett": "all",         # ROE/护城河/现金流 哪里都适用，实际也买了比亚迪(HK)
    "graham": "all",          # PE/PB/安全边际 是数学，不分市场
    "fisher": "all",          # 15 要点评估框架，全球通用
    "munger": "all",          # 好生意+好价格+好管理，全球通用
    "templeton": "all",       # 全球逆向投资先驱
    "klarman": "all",         # 安全边际哪里都能算

    # Group B · Growth — 方法论全球通用
    "lynch": "all",           # PEG / tenbagger 逻辑全球通用
    "oneill": "all",          # CANSLIM 7 因子哪个市场都能跑
    "thiel": "all",           # 0到1 垄断判断全球通用
    "wood": "all",            # 颠覆式创新 5 平台全球通用

    # Group C · Macro/Hedge — 天然全球视角
    "soros": "all",
    "dalio": "all",
    "marks": "all",           # 市场周期判断全球通用
    "druck": "all",
    "robertson": "all",

    # Group D · Technical — 图表不分国界
    "livermore": "all",
    "minervini": "all",       # Stage Analysis 全球通用
    "darvas": "all",
    "gann": "all",

    # Group E · China Value — 方法论通用，但更熟悉中国市场
    "duan": "all",            # 段永平：苹果/腾讯/茅台都买，全球视野
    "zhangkun": "all",        # 方法论通用，只是基金合同限制A+HK
    "zhushaoxing": "all",     # 方法论通用
    "xiezhiyu": "all",
    "fengliu": "all",         # 弱者体系全球通用
    "dengxiaofeng": "all",

    # Group F · 游资 — 【唯一需要市场限制的群体】
    # 游资的方法论(打板/龙虎榜/T+1/涨停板)只在 A 股有效
    "zhang_mz": "A", "zhao_lg": "A", "fs_wyj": "A", "bj_cj": "A",
    "yangjia": "A", "sun_ge": "A", "chen_xq": "A", "hu_jl": "A",
    "fang_xx": "A", "zuoshou": "A", "xiao_ey": "A", "jiao_yy": "A",
    "mao_lb": "A", "xiao_xian": "A", "lasa": "A", "chengdu": "A",
    "sunan": "A", "ningbo_st": "A", "liuyi_zl": "A", "liu_sh": "A",
    "gu_bl": "A", "wang_zr": "A", "xin_dd": "A",
    "ghzw": "A",            # v3.9.0 · 股海贼王 · 淘股吧实盘 · 接力/打板只在 A 股 T+1 生态有效

    # Group G · Quant — 全球
    "simons": "all",
    "thorp": "US",
    "shaw": "all",
    "asness": "all",          # v3.8.1 · AQR 因子(价值×质量×动量)是数学 · 全球通用

    # Group B 新晋 VC (v3.7.0 · v3.8.1 显式登记) — 主战场美股 · 软件/平台方法论全球通用
    "andreessen": "all",      # "Software eats the world" 不分市场
    "gurley": "all",          # marketplace/unit economics 框架全球通用
    "naval": "all",           # 杠杆/复利哲学全球通用
    "gerstner": "all",        # Altimeter 实际持过美团/拼多多 · 全球科技视野
    "chamath": "all",         # disruptor thesis 全球通用

    # Group C 做空猎手 (v3.7.0) — 估值泡沫/会计造假判断全球通用
    "burry": "all",           # 价值+逆向是数学 · 也做过中概 ADR
    "chanos": "all",          # 会计质量分析全球通用 · 历史空过中概

    # Group E 高瓴 (v3.7.0)
    "zhang_lei": "all",       # 腾讯(HK)/京东(US)/宁德(A) 全市场布局

    # Group H · 科技领袖派 (v3.7.0) — 看的是自家产业链 · 上下游横跨 A/H/U
    "jensen_huang": "all",    # AI 算力链供应商遍布 TW/KR/CN/US (A 股光模块在视野内)
    "musk": "all",            # EV/电池链大量 A 股供应商
    "altman": "all",          # AGI 供应链(算力/能源)全球
    "saylor": "all",          # BTC/数字资产叙事不分市场

    # Group I · AI 卡位/瓶颈猎手 — 主战场美股，但 AI 供应链卡点逻辑全球通用
    "serenity": "all",
}


def market_match(investor_id: str, market: str) -> bool:
    """Return True if this investor would look at this market.

    market: "A", "HK", "US"
    """
    scope = MARKET_SCOPE.get(investor_id, "all")
    if scope == "all":
        return True
    return market.upper() in scope.upper()


# ═══════════════════════════════════════════════════════════════
# 2. KNOWN HOLDINGS — 真实持仓 / 曾经公开买过的标的
# ═══════════════════════════════════════════════════════════════
# 格式: {investor_id: [(ticker_pattern, attitude, note), ...]}
# ticker_pattern: 股票代码前缀或名称关键词
# attitude: "bullish_known" / "bearish_known" / "held" / "exited"
# note: 公开来源说明

KNOWN_HOLDINGS: dict[str, list[tuple[str, str, str]]] = {
    "buffett": [
        ("AAPL", "held", "伯克希尔第一大持仓，2016年起买入，多次加仓"),
        ("苹果", "held", "同上，中文名匹配"),
        ("KO", "held", "可口可乐，1988年起持有至今"),
        ("BAC", "held", "美国银行，大量持仓"),
        ("OXY", "held", "西方石油，2022年大举买入"),
        ("BYD", "held", "比亚迪，2008年买入港股"),
        ("比亚迪", "held", "同上"),
        ("AXP", "held", "美国运通"),
        ("MCO", "held", "穆迪"),
        ("DVA", "held", "达维塔"),
        ("茅台", "bullish_known", "芒格/段永平圈子都认可，巴菲特对白酒生意模式评价很高"),
    ],
    "munger": [
        ("BABA", "held", "2021年买入阿里巴巴，后减仓"),
        ("阿里", "held", "同上"),
        ("BYD", "held", "比亚迪投资来自芒格推荐"),
        ("比亚迪", "held", "同上"),
        ("好市多", "held", "Costco 董事会成员"),
        ("COST", "held", "同上"),
    ],
    "duan": [
        ("AAPL", "held", "段永平2011年前后买入苹果，长期持有"),
        ("苹果", "held", "同上"),
        ("茅台", "held", "贵州茅台长期持仓"),
        ("600519", "held", "同上"),
        ("腾讯", "held", "长期持有腾讯"),
        ("00700", "held", "同上"),
        ("GOOG", "held", "持有谷歌"),
    ],
    "zhangkun": [
        ("茅台", "held", "易方达蓝筹精选重仓"),
        ("600519", "held", "同上"),
        ("五粮液", "held", "重仓白酒"),
        ("000858", "held", "同上"),
        ("泸州老窖", "held", "重仓"),
        ("腾讯", "held", "港股重仓"),
        ("美团", "held", "港股持仓"),
    ],
    "fengliu": [
        ("海康", "held", "冯柳重仓海康威视"),
        ("002415", "held", "同上"),
        ("紫金矿业", "held", "周期股代表持仓"),
    ],
    "wood": [
        ("TSLA", "held", "ARK 第一大持仓"),
        ("特斯拉", "held", "同上"),
        ("COIN", "held", "加密货币交易所"),
        ("ROKU", "held", "流媒体"),
        ("SQ", "held", "Block/Square"),
        ("RKLB", "held", "火箭实验室 — 太空"),
        ("量子", "bullish_known", "ARK 看好量子计算赛道"),
        ("基因", "bullish_known", "ARK Genomic Revolution"),
        ("AI", "bullish_known", "ARK 五大平台之一"),
    ],
    "lynch": [
        ("消费", "bullish_known", "林奇最擅长在日常消费中发现 tenbagger"),
    ],
    "soros": [
        ("NVDA", "held", "索罗斯基金持有英伟达"),
    ],
}


def check_known_holdings(investor_id: str, ticker: str, name: str) -> tuple[str, str] | None:
    """Check if this investor has a known attitude toward this stock.

    Returns (attitude, note) or None.
    """
    holdings = KNOWN_HOLDINGS.get(investor_id, [])
    for pattern, attitude, note in holdings:
        if pattern in ticker or pattern in name:
            return (attitude, note)
    return None


# ═══════════════════════════════════════════════════════════════
# 3. INDUSTRY AFFINITY — 行业亲和度
# ═══════════════════════════════════════════════════════════════
# 格式: {investor_id: {"love": [...], "hate": [...], "neutral_default": True/False}}
# love: 关键词列表，命中加分
# hate: 关键词列表，命中减分

INDUSTRY_AFFINITY: dict[str, dict] = {
    "buffett": {
        "love": ["消费", "保险", "银行", "金融", "饮料", "食品", "零售", "能源", "白酒"],
        "hate": ["生物科技", "半导体", "量子", "加密", "区块链", "mRNA"],
        "note": "能力圈：消费品 + 金融 + 能源。科技股只买苹果（特例）",
    },
    "graham": {
        "love": ["银行", "保险", "公用事业", "铁路", "基础设施"],
        "hate": ["科技", "互联网", "AI", "半导体", "量子", "生物"],
        "note": "只看低PE低PB的传统行业",
    },
    "wood": {
        "love": ["AI", "人工智能", "量子", "基因", "机器人", "自动驾驶", "电池",
                 "锂电", "新能源", "储能", "3D打印", "太空", "卫星", "区块链",
                 "数字货币", "mRNA", "脑机", "半导体", "软件", "云"],
        "hate": ["银行", "保险", "石油", "煤炭", "钢铁", "地产", "白酒"],
        "note": "只看颠覆式创新，传统行业完全不碰",
    },
    "thiel": {
        "love": ["AI", "太空", "量子", "生物科技", "加密", "国防", "数据"],
        "hate": ["传统制造", "零售", "地产"],
        "note": "0到1，只看垄断性创新",
    },
    "lynch": {
        "love": ["消费", "零售", "餐饮", "医药", "成长"],
        "hate": [],
        "note": "逛商场选股，关注日常生活能接触到的公司",
    },
    "duan": {
        "love": ["消费电子", "互联网", "白酒", "平台"],
        "hate": ["周期", "化工", "钢铁", "航运"],
        "note": "段永平：看得懂的好生意，长期持有",
    },
    "soros": {
        "love": ["宏观", "外汇", "商品", "金融", "科技"],
        "hate": [],
        "note": "宏观对冲，什么都做但核心是宏观趋势",
    },
}


def compute_affinity(investor_id: str, industry: str, name: str = "") -> int:
    """Return affinity score adjustment: +10 to -10.

    Positive = this investor naturally likes this type of stock.
    Negative = outside their comfort zone.
    """
    info = INDUSTRY_AFFINITY.get(investor_id)
    if not info:
        return 0

    text = (industry + " " + name).lower()
    love_hits = sum(1 for kw in info.get("love", []) if kw.lower() in text)
    hate_hits = sum(1 for kw in info.get("hate", []) if kw.lower() in text)

    return min(10, love_hits * 4) - min(10, hate_hits * 5)


# ═══════════════════════════════════════════════════════════════
# 4. COMPOSITE REALITY CHECK
# ═══════════════════════════════════════════════════════════════

def reality_check(
    investor_id: str,
    market: str,
    ticker: str,
    name: str,
    industry: str,
) -> dict:
    """Comprehensive reality check: should this investor even comment on this stock?

    Returns:
        {
            "should_evaluate": bool,
            "skip_reason": str | None,     # why they shouldn't evaluate
            "holding_match": (attitude, note) | None,
            "affinity_adjust": int,        # -10 to +10
            "override_signal": str | None, # "bullish" if they actually hold it
        }
    """
    result: dict[str, Any] = {
        "should_evaluate": True,
        "skip_reason": None,
        "holding_match": None,
        "affinity_adjust": 0,
        "override_signal": None,
    }

    # 1. Market filter
    if not market_match(investor_id, market):
        result["should_evaluate"] = False
        result["skip_reason"] = f"不看{market}市场"
        return result

    # 2. Known holdings
    holding = check_known_holdings(investor_id, ticker, name)
    if holding:
        result["holding_match"] = holding
        attitude, note = holding
        if attitude in ("held", "bullish_known"):
            result["override_signal"] = "bullish"
            result["affinity_adjust"] = 15  # strong bonus for actual holdings

    # 3. Industry affinity
    affinity = compute_affinity(investor_id, industry, name)
    result["affinity_adjust"] += affinity

    return result


if __name__ == "__main__":
    import json
    # Test: Buffett on Apple
    r = reality_check("buffett", "US", "AAPL", "苹果", "消费电子")
    print("Buffett × Apple:", json.dumps(r, ensure_ascii=False, default=str))

    # Test: 游资 on Apple
    r2 = reality_check("zhao_lg", "US", "AAPL", "苹果", "消费电子")
    print("赵老哥 × Apple:", json.dumps(r2, ensure_ascii=False, default=str))

    # Test: Wood on quantum
    r3 = reality_check("wood", "A", "688027.SH", "国盾量子", "量子通信")
    print("Wood × 国盾量子:", json.dumps(r3, ensure_ascii=False, default=str))

    # Test: Graham on AI company
    r4 = reality_check("graham", "US", "NVDA", "英伟达", "半导体AI")
    print("Graham × 英伟达:", json.dumps(r4, ensure_ascii=False, default=str))

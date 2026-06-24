"""Per-investor authentic decision profile · v2.8.

Each investor fills THREE fields according to their own methodology — NOT a uniform
template. This is the "因地制宜" layer: Buffett's time horizon is "10+ years",
赵老哥's is "T+2"; Buffett's position sizing is "集中前 5 大 70%+", Simons' is
"等权数千只，单票 < 0.5%".

Fields:
    time_horizon:              该投资者自然持仓周期
    position_sizing:           该投资者的仓位/集中度风格
    what_would_change_my_mind: 什么会让他/她**翻盘** — 触发卖出/反向的条件

Design principle:
- 22 个标志性人物各自手写 authentic 内容（覆盖 7 个流派）
- 其余 ~29 人用 GROUP_DEFAULT 按流派 fallback（好过通用默认，但不冒充个人风格）
- 未注册人物回 GENERIC_FALLBACK

Keys follow `id` in lib/investor_db.py.
Sources are real quotes / methodology summaries / published behavior patterns.
"""
from __future__ import annotations


# ═══════════════════════════════════════════════════════════════
# 22 标志性人物 · 每人 authentic 3 字段
# ═══════════════════════════════════════════════════════════════
PROFILES: dict[str, dict[str, str]] = {
    # ────── Group A · 经典价值 ──────
    "buffett": {
        "time_horizon": "10 年以上 / 永远；如果你不愿意持有十年，就不要持有十分钟",
        "position_sizing": "集中持仓，前 5 大通常占 70%+；好机会稀有，要重仓",
        "what_would_change_my_mind": "ROE 连续 2 年跌破 12% · CEO 离职且战略转向 · 发现管理层诚信问题 · 商业模式被颠覆（例如纺织、报纸）",
    },
    "graham": {
        "time_horizon": "2-3 年；达到内在价值或持有 2 年仍跑输市场则卖出",
        "position_sizing": "分散至少 30 只，单票上限 5%，防御型投资者的铁律",
        "what_would_change_my_mind": "PE × PB > 22.5 · 流动比率跌破 2 · 连续两年无盈利 · 股息中断",
    },
    "fisher": {
        "time_horizon": "长期持有 5-15 年，让伟大的公司给你长期复利",
        "position_sizing": "集中 10-20 只，深入了解后重仓；不懂的不碰",
        "what_would_change_my_mind": "15 要点中出现 3 项以上恶化 · 管理层对投资者不坦诚 · 研发投入比突降 · 利润率持续侵蚀",
    },
    "munger": {
        "time_horizon": "终身持有好生意，除非基本面永久性恶化",
        "position_sizing": "极度集中，3-5 只占组合 80%+；反过来想，分散是能力不足的承认",
        "what_would_change_my_mind": "反过来想——'这家最可能怎么死？' 看到 2 个以上答案时就要警觉 · 管理层 incentive 跑偏",
    },
    "klarman": {
        "time_horizon": "灵活，有机会就出手，没机会就拿现金；特殊事件驱动为主",
        "position_sizing": "可以 30-50% 现金等机会；单票 5-10%，特殊情形可更高",
        "what_would_change_my_mind": "安全边际消失（市值接近 NAV）· 催化剂被推迟或取消 · 出现更好的错杀机会",
    },

    # ────── Group B · 成长派 ──────
    "lynch": {
        "time_horizon": "公司故事讲完为止，典型 3-5 年；小盘 fast-grower 可以短些",
        "position_sizing": "30-50 只多样化，按 6 类（稳定/周期/fast/慢/困境/资产）配比",
        "what_would_change_my_mind": "PEG > 2（成长不配估值）· 库存/应收增速超过营收 · 故事不再兑现 · 个人能接触的场景里热度消退",
    },
    "oneill": {
        "time_horizon": "握到 cup-and-handle 失败或 50 日均线破位；典型 3-12 个月",
        "position_sizing": "初仓 25%，突破加仓至 100%；CANSLIM 7 维不达标不开仓",
        "what_would_change_my_mind": "M 大盘转熊 · 跌破买入价 7-8% 无条件止损 · RS 强度跌出前 20% · 季度 EPS 减速",
    },
    "thiel": {
        "time_horizon": "Power law 回报，一笔对的能 cover 所有错的；持有至 IPO/被收购",
        "position_sizing": "极度不分散，单笔可 30%+；先找垄断再谈估值",
        "what_would_change_my_mind": "竞争进入（垄断破） · 网络效应被新技术绕过 · 管理层卖股转向",
    },
    "wood": {
        "time_horizon": "5 年视角看颠覆性技术拐点；短期波动不是卖出理由",
        "position_sizing": "高 β 组合单票可 10%+，接受 50% 回撤换 10x 上行",
        "what_would_change_my_mind": "S-curve 采用率斜率走平 · 监管禁令 · 核心技术被更新范式替代",
    },

    # ────── Group C · 宏观对冲 ──────
    "soros": {
        "time_horizon": "反身性循环一轮，通常数周到数月，随时可翻转",
        "position_sizing": "重仓押一次（sterling 1992 那种），但任何时候都可反向",
        "what_would_change_my_mind": "市场停止验证我的叙事（反身性反转）· 基本面超出错误区间 · 更好的非对称机会出现",
    },
    "dalio": {
        "time_horizon": "All Weather 全天候配置，再平衡周期约 1 年；单次押注几天到几月",
        "position_sizing": "风险平价：每类资产的波动率贡献相等，不看单票",
        "what_would_change_my_mind": "经济周期象限切换（增长↑↓ × 通胀↑↓ 四宫格）· 央行政策拐点 · 长债利率结构破位",
    },
    "druck": {
        "time_horizon": "灵活，从几周到 2 年；对错都要快速反应",
        "position_sizing": "不对的时候只下小注，极度对的时候 all-in；集中非常高",
        "what_would_change_my_mind": "央行立场转向 · 自己的赔率判断被市场证伪 · 发现更大赔率的品种",
    },
    "marks": {
        "time_horizon": "完整的市场周期（通常 5-7 年），周期位置决定进出",
        "position_sizing": "逆向：别人抢时不买，别人弃时买；单票仓位按风险定价调",
        "what_would_change_my_mind": "二阶思维反转（我对多数人的判断变了）· 风险溢价收敛到极值 · 周期钟摆触顶",
    },

    # ────── Group D · 技术趋势 ──────
    "livermore": {
        "time_horizon": "吃完主升浪，通常数周到数月，坐住比交易难",
        "position_sizing": "试仓-验证-加仓-重仓 pyramid；错了立刻止损走人",
        "what_would_change_my_mind": "关键支撑破位 · 领涨股走弱 · 整体市场 tone 改变 · 任何反向信号 '立即 get out'",
    },
    "minervini": {
        "time_horizon": "VCP 突破后 3-6 个月吃主升浪；跌破 20 日立即减仓",
        "position_sizing": "初始 25% 仓位，确认追加至 100%；亏损不超过整仓 2%",
        "what_would_change_my_mind": "跌破 10/20 日均线 · 放量下跌 · 趋势模板 8 条件中 3 项以上失效",
    },

    # ────── Group E · 中国价投 ──────
    "duan": {
        "time_horizon": "10-20 年，好的公司尽可能长；搞懂了就敢重仓",
        "position_sizing": "极度集中：Apple 占他组合大半；敢 all-in 到自己真的懂的",
        "what_would_change_my_mind": "生意的本质变了（不是季度波动）· 管理层 incentive 偏移 · 自己真的不懂了就卖",
    },
    "zhangkun": {
        "time_horizon": "3-5 年中期；白酒、医药、大消费要看够一个周期",
        "position_sizing": "易方达蓝筹前十大长期占 70%+，低换手；好公司等回调",
        "what_would_change_my_mind": "ROE 连续 2 年掉队行业平均 · 估值分位超 90% · 管理层大规模变动",
    },
    "fengliu": {
        "time_horizon": "3-6 个月等错杀修复，弱者体系不预测只应对",
        "position_sizing": "偏均衡，单票不超 10%；用足够差价换取错了也能扛",
        "what_would_change_my_mind": "基本面证伪（订单/产能/客户反馈）· 价格修复完毕 · 发现更大错杀",
    },
    "dengxiaofeng": {
        "time_horizon": "2-4 年跨周期，深度研究周期行业与产业链",
        "position_sizing": "集中产业链龙头，单票 10-20%；周期底部布局、顶部卖",
        "what_would_change_my_mind": "产能周期见顶信号 · 价格下行兑现 · 下游需求证伪",
    },

    # ────── Group F · A 股游资 ──────
    "zhao_lg": {
        "time_horizon": "T+2 到 T+5，吃打板主升；强度退化立即走",
        "position_sizing": "龙头板仓位 10-20%，T+1 根据分歧加减；绝不过周末的不隔夜",
        "what_would_change_my_mind": "板上砸盘 · 龙头断板 · 龙虎榜出现对手方机构 · 量能跟不上",
    },
    "zhang_mz": {
        "time_horizon": "核心大龙 7-15 天，吃到主升末期",
        "position_sizing": "打最强龙头，重仓敢拿；接力中军分仓",
        "what_would_change_my_mind": "题材逻辑证伪 · 大盘系统性风险 · 自己席位被跟风破坏节奏",
    },
    # 注：chengdu（成都帮）是席位集合体非个人，按 quotes-knowledge-base 的
    # 「席位类游资·无个人原话」分类走 Group F fallback，而不是冒充成有 authored 方法论。
    "lasa": {
        "time_horizon": "1-2 天，打首板 / 二板为主",
        "position_sizing": "单票 5-15%，封板率高时加仓；封板力度弱就跑",
        "what_would_change_my_mind": "封板时间推后 · 开板即砸 · 情绪周期从亢奋转分歧",
    },

    # ────── Group G · 量化 ──────
    "simons": {
        "time_horizon": "平均持仓 < 2 天；数秒到数月组合，完全由模型决定",
        "position_sizing": "等权数千只，单票仓位 < 0.5%；风险预算由协方差决定",
        "what_would_change_my_mind": "模型信号 Sharpe 跌破 0.5 · 因子衰减 · 市场结构变化（如交易制度改变）",
    },

    # ────── Group H · AI 卡位/瓶颈猎手 ──────
    "serenity": {
        "time_horizon": "thesis-driven，从信息差到机构 rotation 兑现，典型数月到 1-2 年；瓶颈逻辑不破就拿住",
        "position_sizing": "极度集中 + 约 1.3-1.4x margin，最高信念的卡点敢满仓重押；不在链上的一律 0 仓",
        "what_would_change_my_mind": "卡位被证伪（出现可替代方案 / 新增产能放量）· 供给从紧转松 · 下游 roadmap 绕过该节点 · 估值已反映瓶颈、信息差消失",
    },
    "ghzw": {  # v3.9.0 · 股海贼王 · 数据来自其十年实盘 (8951 笔交割单)
        "time_horizon": "超短接力 T+1 到 T+5（持仓中位 1 天）· 时代级格局票可拿数月看三五倍",
        "position_sizing": "同时 3-5 只 · 第一重仓常打五成 · 闲钱逆回购 · 高位票绝不满仓搞",
        "what_would_change_my_mind": "主线退潮 · 弱转强失败/盘口承接消失 · 大盘系统性风险（自认十年最大弱项 · 赚 15 个点就休息）",
    },

}


# ═══════════════════════════════════════════════════════════════
# Group-level fallback · 未单独注册的投资者按流派走
# ═══════════════════════════════════════════════════════════════
# 每个流派给一份**流派级**但仍足够具体的默认，好过通用默认。
# 落在这里的投资者至少不会用错流派的语境回答问题。
GROUP_DEFAULT: dict[str, dict[str, str]] = {
    "A": {  # 经典价值
        "time_horizon": "3-10 年，等公司兑现内在价值",
        "position_sizing": "集中 10-20 只，重仓高确定性机会",
        "what_would_change_my_mind": "基本面永久性恶化 · 管理层诚信受损 · 安全边际被市场吃掉",
    },
    "B": {  # 成长派
        "time_horizon": "2-5 年，跟随公司成长曲线",
        "position_sizing": "中度集中 20-30 只，成长最猛的票重仓",
        "what_would_change_my_mind": "增长失速 · 估值与成长严重背离（PEG>2）· 护城河被穿",
    },
    "C": {  # 宏观对冲
        "time_horizon": "数周到数月，跟随宏观节奏与流动性窗口",
        "position_sizing": "按赔率分配，对的时候敢重仓，错的时候立即认错",
        "what_would_change_my_mind": "宏观叙事被证伪 · 央行/政策转向 · 赔率变得不利",
    },
    "D": {  # 技术趋势
        "time_horizon": "数周到 3 个月，跟趋势做，破位就走",
        "position_sizing": "Pyramid 加仓，亏损严格控制在单笔 2% 以内",
        "what_would_change_my_mind": "关键均线破位 · 量能背离 · 相对强度掉出前列",
    },
    "E": {  # 中国价投
        "time_horizon": "3-5 年，等好公司给好价格",
        "position_sizing": "偏集中，单票 5-15%；深度研究后重仓",
        "what_would_change_my_mind": "ROE / 净利率掉队行业 · 管理层或核心业务大变 · 估值分位过高",
    },
    "F": {  # A 股游资
        "time_horizon": "T+1 到 T+5 超短线，视盘面决定",
        "position_sizing": "单票 5-20%，强度强时加仓、弱时立即走",
        "what_would_change_my_mind": "板上砸盘 / 断板 · 量能不配合 · 龙虎榜对手方压过自己席位",
    },
    "G": {  # 量化
        "time_horizon": "由模型决定，通常数天到数周",
        "position_sizing": "等权或风险平价分散，单票权重由模型算",
        "what_would_change_my_mind": "因子 IC 衰减 · Sharpe 下降 · 市场微观结构改变",
    },
    # v3.8.1 · 补 H/I（之前缺失 → H/I 评委 profile 落到 GENERIC_FALLBACK 全是 "—"）
    "H": {  # 科技领袖派（黄仁勋/马斯克/Altman/Saylor · 看自家产业链）
        "time_horizon": "5-10 年技术周期，跟随平台迁移（AI/EV/AGI/数字资产）",
        "position_sizing": "极度集中——All in 自己看得最清的产业链节点",
        "what_would_change_my_mind": "技术路线被颠覆 · scaling 失效 · 产业链节点被绕过",
    },
    "I": {  # AI 卡位/瓶颈猎手（Serenity）
        "time_horizon": "6-24 个月，从市场未定价埋伏到瓶颈被公认",
        "position_sizing": "高信念集中重仓 1-3 只卡点小盘，确认错了立即清仓",
        "what_would_change_my_mind": "替代方案量产 · 产能瓶颈解除 · 卡点被市场充分定价",
    },
}


# ═══════════════════════════════════════════════════════════════
# Generic fallback · 不在任何已知流派
# ═══════════════════════════════════════════════════════════════
GENERIC_FALLBACK: dict[str, str] = {
    "time_horizon": "—",
    "position_sizing": "—",
    "what_would_change_my_mind": "—",
}


def get_profile(investor_id: str, group: str = "") -> dict[str, str]:
    """Return the authentic 3-field profile for one investor.

    Priority:
      1. PROFILES[investor_id] — 22 个标志性人物手写内容
      2. GROUP_DEFAULT[group]  — 流派级 fallback
      3. GENERIC_FALLBACK      — 最后默认

    参数：
      investor_id: e.g. 'buffett' / 'zhao_lg' / 'simons'
      group:       e.g. 'A' / 'F' — 从 investor_db 取，用于 fallback

    返回：
      {'time_horizon': ..., 'position_sizing': ..., 'what_would_change_my_mind': ...}
    """
    if investor_id in PROFILES:
        return dict(PROFILES[investor_id])
    if group and group in GROUP_DEFAULT:
        return dict(GROUP_DEFAULT[group])
    return dict(GENERIC_FALLBACK)


def stats() -> dict:
    """Coverage report."""
    return {
        "authored_profiles": len(PROFILES),
        "groups_with_defaults": len(GROUP_DEFAULT),
        "authored_ids": sorted(PROFILES.keys()),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(stats(), ensure_ascii=False, indent=2))
    print()
    print("=== Sample profiles ===")
    for inv_id in ("buffett", "zhao_lg", "simons", "lynch", "soros"):
        print(f"\n{inv_id}:")
        print(json.dumps(get_profile(inv_id), ensure_ascii=False, indent=2))

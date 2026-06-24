"""Per-investor signature phrases for the evaluation panel.

Each investor has 3 signal types (bullish/bearish/neutral) and each maps to
2-4 signature lines drawn from their REAL public quotes or methodology.
These are used by run_real_test.py::generate_panel() to produce comments
that actually sound like the person being simulated, not a generic group template.

Keys follow the `id` field in lib/investor_db.py.
Quotes sourced from `skills/investor-panel/references/quotes-knowledge-base.md`.
"""
from __future__ import annotations

# Signature-line templates per investor.
# Variables (filled by run_real_test):
#   {roe}, {pe}, {price}, {name}, {industry}, {growth}, {stage}

PERSONAS: dict[str, dict[str, list[str]]] = {
    # ═══════════════ Group A · 经典价值 ═══════════════
    "buffett": {
        "bullish": [
            "在我们能力圈里的生意，ROE {roe}% 长期稳得住，就值得持有十年。",
            "价格是你付出的，价值是你得到的。这种生意我愿意拿十年。",
            "如果你不愿意持有十年，就不要持有十分钟。这只票我觉得 OK。",
        ],
        "bearish": [
            "ROE 和现金流都有疑问，这不是我们喜欢的生意。",
            "PE {pe} 已经没有安全边际了，等别人恐惧时再看。",
            "我们不碰看不懂的东西，这家的商业模式我没想清楚。",
        ],
        "neutral": [
            "需要再观察几个季度，好公司也得等好价格。",
            "在能力圈边缘，先观察不行动。",
        ],
    },
    "graham": {
        "bullish": [
            "PE {pe}、PB 合理，流动比率达标，符合防御型投资者标准。",
            "7 项硬指标有多数达标，是一只能让我安稳睡觉的票。",
            "长期分红 + 盈利稳定 + 估值不贵，经典价值三要素齐全。",
        ],
        "bearish": [
            "PE × PB 已远超 22.5，不符合最基本的安全边际。",
            "连续 10 年盈利我没看到，防御型组合不应该碰。",
            "市场短期是投票机，但这票投票机都嫌贵了。",
        ],
        "neutral": ["数据不齐，严守不达标不买入的纪律。"],
    },
    "fisher": {
        "bullish": [
            "{industry} 有足够市场潜力，管理层也在投研发，这是好苗子。",
            "利润率能维持，劳资关系稳定，15 要点多数达标。",
            "scuttlebutt 法调研，这家在产业链口碑不错。",
        ],
        "bearish": [
            "管理层对投资者的坦诚度让我怀疑，暂时观望。",
            "研发投入不足以支撑长期竞争力。",
        ],
        "neutral": ["要做更多闲聊式调研，现在信息还不够。"],
    },
    "munger": {
        "bullish": [
            "反过来想：这个生意难被颠覆，管理层也没撒谎，那就可以买。",
            "简单数学算得清，ROE {roe}% 的生意复利起来就是钱。",
            "等待是投资者的伟大优点，但这票已经等够了。",
        ],
        "bearish": [
            "反过来想——这家最可能怎么死？我想到的方式有点多。",
            "心理学偏误在作祟，大家都追这票就要警惕。",
            "如果我知道我会死在哪里，我就永远不去那里。这票风险点我看得见。",
        ],
        "neutral": ["宁可错过，不可做错。"],
    },
    "templeton": {
        "bullish": [
            "PE 在历史低位区，这就是最大悲观点买入的时机。",
            "市场还在怀疑这家，牛市生于悲观，长于怀疑。",
            "和全球同类比这 PE 已经便宜，值得下手。",
        ],
        "bearish": [
            "大众已经开始亢奋，邓普顿的铁律是此时卖出。",
            "全球同类公司估值都更便宜，为什么买这个？",
        ],
        "neutral": ["情绪还没到极度悲观，等更好价格。"],
    },
    "klarman": {
        "bullish": [
            "内在价值折扣 > 30%，安全边际的基石在这里。",
            "下行风险可控，催化剂也可见，Baupost 会考虑。",
            "情绪是仆人不是主人，现在情绪帮我便宜买入。",
        ],
        "bearish": [
            "没看到明确催化剂，安全边际也不够。",
            "最坏情况下这票能亏 50%，风险回报比不对。",
        ],
        "neutral": ["耐心等更明确的机会。"],
    },

    # ═══════════════ Group B · 成长投资 ═══════════════
    "lynch": {
        "bullish": [
            "PEG 合理，成长故事一句话说得清，散户能懂——这是 Fast Grower。",
            "机构持股还不高，内部人在买，林奇喜欢这种票。",
            "买你了解的公司。我对 {industry} 懂一点，这家可以蹲。",
        ],
        "bearish": [
            "PEG 已经超过 2，成长故事不便宜。",
            "机构都进来了，再涨空间不大。",
        ],
        "neutral": ["公司业务我没研究透，先放 watchlist。"],
    },
    "oneill": {
        "bullish": [
            "CANSLIM 多数达标：季度 EPS 超 25%、新高价、机构在加仓。",
            "M 大盘向上 + L 行业前 3，CANSLIM 6 项以上，该进攻了。",
            "最贵的股票通常是最便宜的——强者恒强。",
        ],
        "bearish": [
            "C 季度 EPS 没到 25%，CANSLIM 第一条就不过。",
            "股价没创新高，趋势不对，我不买下跌股。",
        ],
        "neutral": ["N 项缺一不可，目前只达标 4 项。"],
    },
    "thiel": {
        "bullish": [
            "{industry} 里看起来有垄断特征，比第二名好 10 倍。",
            "网络效应 + 规模经济都有，这是好生意的 DNA。",
            "最伟大的公司都从一个秘密开始，这家的秘密我看得见。",
        ],
        "bearish": [
            "竞争激烈意味着这是失败者的游戏。",
            "没看到垄断基因，长期竞争优势可疑。",
        ],
        "neutral": ["还没到 0 → 1 的临界点。"],
    },
    "wood": {
        "bullish": [
            "{industry} 处于 S 曲线拐点，TAM 每年 >30% 增长——买它就是买未来！",
            "We don't buy stocks, we buy the future. {name} 就是那个未来。",
            "成本曲线快速下降中，5 年内会改变整个 {industry} 的游戏规则。",
            "指数型增长刚起步，大多数人还看不懂——这正是我们加仓的时候。",
            "AI / 量子 / 基因 / 机器人 / 能源存储，五大平台之一，必须重仓！",
        ],
        "bearish": [
            "不在我们五大平台里（AI、机器人、储能、量子、多组学），不看。",
            "颠覆性不够——只是传统行业的改良版，不是范式转移。",
            "技术路线不确定，还没到成本曲线拐点，太早了。",
        ],
        "neutral": ["S 曲线还没到拐点，但值得持续跟踪——一旦成本下降 50% 我们就进场。"],
    },

    # ═══════════════ Group C · 宏观对冲 ═══════════════
    "soros": {
        "bullish": [
            "预期与基本面出现正向偏离，反身性循环进入加速期。",
            "市场主动塑造现实，现在买就是押正反馈开始。",
            "我之所以富有是因为我知道我什么时候错——这次没错。",
        ],
        "bearish": [
            "正反馈循环已近顶峰，反身性即将反转。",
            "重要的不是判断对错，而是赚多亏少——现在赢面不够。",
        ],
        "neutral": ["反身性信号还不够强。"],
    },
    "dalio": {
        "bullish": [
            "长期债务周期在早期，信贷环境友好，这种资产会受益。",
            "拥抱现实——数据指向买入。现金是垃圾，这票是资产。",
            "痛苦加反思等于进步，基本面反转的逻辑到了。",
        ],
        "bearish": [
            "债务周期晚期 + 信贷收紧，风险资产都要小心。",
            "全天候配置里这种资产的权重该降。",
        ],
        "neutral": ["宏观信号混乱，观望。"],
    },
    "marks": {
        "bullish": [
            "市场温度计在恐惧区，卓越投资来自买得好不是买得好资产。",
            "为风险买单我不做，但这次风险已经被定价了。",
            "你不能预测但可以准备——现在是准备好的时机。",
        ],
        "bearish": [
            "温度计 80+ 进入贪婪区，这种时候我选离场。",
            "估值最终会回归均值，现在追高是交税。",
        ],
        "neutral": ["温度在中位，按兵不动。"],
    },
    "druck": {
        "bullish": [
            "宏观流动性拐点已到，这类标的最受益——值得集中下注。",
            "永远投资 12-18 个月后的世界，这票符合那个时点的逻辑。",
            "你做对时要下大注，现在就是时候。",
        ],
        "bearish": [
            "流动性还在收紧，这种估值站不住。",
            "我只投资 12-18 个月后的世界，现在这题材已经过气了。",
        ],
        "neutral": ["不是我的确定性标的，放弃。"],
    },
    "robertson": {
        "bullish": [
            "{industry} 里相对最强，Tiger 的做法是做多最强的。",
            "基本面领先同行，长做多短做空组合里这是多头腿。",
        ],
        "bearish": [
            "行业排名中下游，我可能做空它对冲多头。",
            "这不是我会买的，我们是评估公司的高手不是赌大盘的。",
        ],
        "neutral": ["排名中位，不做。"],
    },

    # ═══════════════ Group D · 技术趋势 ═══════════════
    "livermore": {
        "bullish": [
            "突破关键价位 + 量能配合，金字塔加仓条件满足。",
            "钱不在买卖中赚，而在等待中赚——这次等到了。",
            "市场永远是对的，对的是市场，买！",
        ],
        "bearish": [
            "没突破关键位，量能也不对，不做。",
            "永远不要逆趋势加仓。",
        ],
        "neutral": ["等突破信号。"],
    },
    "minervini": {
        "bullish": [
            "Stage 2 + VCP 收缩 + 200 日均线上升——SEPA 8 项达标我就买。",
            "只买强势股，这只票符合 Trend Template 全部标准。",
            "相对强度 >70，距高点 <25%，完美入场条件。",
        ],
        "bearish": [
            "不在 Stage 2，我不碰。",
            "Trend Template 只达标 4 项，不符合 SEPA 纪律。",
            "止损不是建议是命令，这票位置不支持我进场。",
        ],
        "neutral": ["技术面还没到位。"],
    },
    "darvas": {
        "bullish": [
            "箱体上沿被放量突破，这是 Darvas Box 的典型买点。",
            "回踩箱顶不破，强势确认。",
        ],
        "bearish": ["还在箱体震荡，没方向。"],
        "neutral": ["箱顶未破不做。"],
    },
    "gann": {
        "bullish": [
            "距上一低点约 55 交易日（斐波那契窗口），角度线支持做多。",
            "时间周期到位，价格运动遵循自然法则。",
        ],
        "bearish": ["时间窗口进入高风险区。"],
        "neutral": ["时间价格未共振。"],
    },

    # ═══════════════ Group E · 中国价投 ═══════════════
    "duan": {
        "bullish": [
            "生意对、人对、价格对——三问都过，就是我喜欢的。",
            "看 10 年想得明白，商业模式也不复杂，可以拿。",
            "做对的事情，把事情做对。这家两件都沾边。",
        ],
        "bearish": [
            "看 10 年想不明白的公司我不买。这家我没看懂。",
            "价格不对，宁可错过不要做错。",
            "Stop doing list：这种高 PE 成长股不在我的清单里。",
        ],
        "neutral": [
            "看不懂就不要碰，放 watchlist。",
            "本分要紧，看不懂的机会不是我的。",
        ],
    },
    "zhangkun": {
        "bullish": [
            "ROE 持续性强 + 品牌壁垒 + 消费属性——可以进集中持仓。",
            "我们偏好有定价权的公司，这家看起来有。",
            "短期股价无法预测，长期价值终将兑现。",
        ],
        "bearish": [
            "消费属性不够，不是我们集中持仓的标的。",
            "ROE 波动太大，缺乏持续性。",
        ],
        "neutral": ["需要再观察两个季度。"],
    },
    "zhushaoxing": {
        "bullish": [
            "长期成长确定性够高，适合用长期视角。",
            "低换手适配度高，可以放进组合长期拿。",
            "投资是一场长跑，这票能陪我跑。",
        ],
        "bearish": [
            "成长确定性不够，长线资金不应重仓。",
            "行业景气度下行，等更好时点。",
        ],
        "neutral": ["再观察，不急。"],
    },
    "xiezhiyu": {
        "bullish": [
            "GARP 性价比合适——成长和估值平衡得不错。",
            "不追求单纯成长也不追便宜，这家刚好。",
        ],
        "bearish": [
            "PE 相对 G 偏高，性价比不够。",
            "成长质量一般，估值又不便宜，没想法。",
        ],
        "neutral": ["性价比在中位，不急着动。"],
    },
    "fengliu": {
        "bullish": [
            "赔率还不错，弱者体系下值得下注。",
            "预期差存在，市场还没完全认知，时间是朋友。",
            "强者失心时弱者捕捉机会——这次我是弱者。",
        ],
        "bearish": [
            "在混沌时不敢果断给结论，先避开。",
            "赔率不好，共识已经太一致。",
        ],
        "neutral": [
            "我只能依靠时间、赔率与常识，现在时机不明。",
            "寻找共识，依靠常识，等赔率更好。",
        ],
    },
    "dengxiaofeng": {
        "bullish": [
            "产能周期位置不错 + 行业供需拐点到位。",
            "好公司 + 好行业 + 好价格，三者都沾。",
            "企业价值创造的根本力量在这里显现。",
        ],
        "bearish": [
            "产能周期还在释放，供给压力未消化。",
            "投资回报来自价值创造不是博弈，这家价值创造不够。",
        ],
        "neutral": ["周期位置不明。"],
    },

    # ═══════════════ Group F · 游资 ═══════════════
    "zhang_mz": {
        "bullish": [
            "格局打开，目标看上一个台阶，大资金可以进场。",
            "做趋势的人不要预测顶部——这票趋势在。",
            "主流板块的龙头，资金易形成合力。",
        ],
        "bearish": [
            "下降通道里赚钱是偶然的，亏钱是必然的。",
            "不是主流板块，资金合力差，放弃。",
        ],
        "neutral": [
            "不会空仓的人永远不会战斗，不会止损的人死路一条——这票我先等。",
            "市值不够大，不在我的射程里。",
        ],
    },
    "sun_ge": {
        "bullish": [
            "板块有引导属性，可以锁仓。",
            "无招胜有招的前提是基本招式到位——这票到位了。",
        ],
        "bearish": ["板块节奏不对，放弃。"],
        "neutral": ["不识溧阳路，龙头战法白忙碌——这票不是我的菜。"],
    },
    "zhao_lg": {
        "bullish": [
            "二板定龙头，题材在线，我进。",
            "新题材就抛弃旧题材——这是新的，跟。",
            "短期交易不讲价值不讲技术，只讲故事。这故事不错。",
        ],
        "bearish": [
            "没有连板潜力，题材也不新，我不碰。",
            "一板能看出来个毛，没确认龙头地位。",
        ],
        "neutral": [
            "题材不够鲜，先观望。",
            "不是板块最强辨识度的那个，我不做跟风。",
        ],
    },
    "fs_wyj": {
        "bullish": [
            "小盘超跌 + 翘板机会，上车。",
            "系统和纪律就是信仰，这票在系统里。",
        ],
        "bearish": [
            "市值太大不在我射程，一日游不好翘。",
            "执行模式简单第一，这票复杂我不碰。",
        ],
        "neutral": ["盘子不对，不适合。"],
    },
    "yangjia": {
        "bullish": [
            "情绪周期到位了，人气在这——牛股不是资金堆的，是情绪产物。",
            "得散户心者得天下，这票人气开始聚集。",
            "别人贪婪时我更贪婪。",
        ],
        "bearish": [
            "情绪周期已到顶，高手买入龙头，超级高手卖出龙头。",
            "情绪不到绝不重仓。",
        ],
        "neutral": [
            "情绪周期不明，我永远等市场告诉我答案。",
            "心中无顶底，操作自随心——这次随心选择等。",
        ],
    },
    "chen_xq": {
        "bullish": [
            "龙头一线天，不上车就追不上了。",
            "分歧是机会一致是风险——现在有分歧，入场。",
            "反核按钮时刻，重仓加仓。",
        ],
        "bearish": [
            "超短最重要的是跟随情绪和主线——这票主线不对。",
            "亏出来的经验告诉我，这种位置不能追。",
        ],
        "neutral": ["等一线天的机会。"],
    },
    "hu_jl": {
        "bullish": ["多席位协同可以做，板块在热点上。", "欢乐豆玩法，这票可以进。"],
        "bearish": ["板块不热，不做。"],
        "neutral": ["等多席位信号。"],
    },
    "fang_xx": {
        "bullish": [
            "大成交量 + 趋势向上，格局锁仓。",
            "龙头股是我选股王冠上的明珠——这票有点像。",
        ],
        "bearish": [
            "日均成交不够大，不在趋势票范围内。",
            "不是我的菜。",
        ],
        "neutral": ["市值+成交量没到位。"],
    },
    "zuoshou": {
        "bullish": [
            "围着主线做，研究龙头研究涨停——这票合格。",
            "刚入市不要想着赚钱要想着悟道，但这票让我悟到了。",
        ],
        "bearish": ["主线上没看到它。", "熊市比的不是快而是稳——这票不稳。"],
        "neutral": ["稳定盈利前少投入资金多投入精力。"],
    },
    "xiao_ey": {
        "bullish": [
            "基本面 + 技术面共振，大盘主线也配合，可以重仓。",
            "股票基本上就是个势，这票有势。",
            "大盘、热点、个股、情绪、节奏、心态、舒适买点——七维达标。",
        ],
        "bearish": [
            "基本面不够硬，我这一派的特点是看基本面。",
            "对的路要坚持，错的路要停止——这票我走不下去。",
        ],
        "neutral": ["没到舒适买点。"],
    },
    "jiao_yy": {
        "bullish": [
            "做龙头要眼到手到心到——我到了。",
            "真正龙头都有渡劫期，等的就是这个确定性。",
        ],
        "bearish": ["只看龙头少看杂毛，这票不是龙头。"],
        "neutral": ["渡劫期未过，等。"],
    },
    "mao_lb": {
        "bullish": [
            "AI 主线大资金可以进，技术是三个月能学完的东西，决定存活的是觉悟。",
            "大资金信号到位。",
        ],
        "bearish": ["不在 AI 主线上，我不碰。", "觉悟告诉我这票做不了大资金。"],
        "neutral": ["AI 主线位置不明。"],
    },
    "xiao_xian": {
        "bullish": [
            "超预期就买买买。",
            "越到行情后期越往龙头转移，这票是龙头。",
        ],
        "bearish": [
            "低于预期就卖卖卖，这票指引一般。",
            "做跟风杂毛会被市场淘汰。",
        ],
        "neutral": [
            "慢就是快，重点是稳中求进。",
            "大回撤都是满仓一只股导致的，先观察。",
        ],
    },
    "lasa": {
        "bullish": ["散户集合体：这票开始追涨了。"],
        "bearish": ["散户接盘警告：我们出现一般是反向指标。"],
        "neutral": ["持仓周期 1-3 天，短线打游击。"],
    },
    "chengdu": {
        "bullish": ["盘中直线拉涨停，万手封单模式启动。"],
        "bearish": ["不是底部黑马，不值得点火。"],
        "neutral": ["等消息面发酵。"],
    },
    "sunan": {
        "bullish": ["低价小盘联动合适做差价，日日吃涨停。"],
        "bearish": ["市值过大，差价空间小。"],
        "neutral": ["群体作业，先看其他席位动向。"],
    },
    "ningbo_st": {
        "bullish": ["连板接力的典型信号。"],
        "bearish": ["没有连板潜力。"],
        "neutral": ["等连板确认。"],
    },
    "liuyi_zl": {
        "bullish": ["题材到了干就完了——大资金接力老龙。"],
        "bearish": ["不是我这一派的风格。"],
        "neutral": ["题材还没到位。"],
    },
    "liu_sh": {
        "bullish": ["低吸接力位置不错，打板手风格匹配。"],
        "bearish": ["顶板/秒板条件不够。"],
        "neutral": ["等低吸信号。"],
    },
    "gu_bl": {
        "bullish": ["大格局敢锁仓，这票可以引爆板块。"],
        "bearish": ["格局不够大，不是我的菜。"],
        "neutral": ["板块未启动，先等。"],
    },
    "bj_cj": {
        "bullish": [
            "首板才是最干净的状态，这票符合我的战法。",
            "9 点 25 涨幅榜有它，打首板。",
            "市值 20-80 亿 + 题材股 + 机构没进，正好是我的菜。",
        ],
        "bearish": [
            "机构持仓太高，故事不值钱了。",
            "不是首板，后面打连板我只打上午十点半前的放量板。",
        ],
        "neutral": ["大盘不对我就空仓等待。"],
    },
    "wang_zr": {
        "bullish": ["只操作强势的股票，这票强。", "熊市出英雄。"],
        "bearish": ["交易不活跃，坚决回避。", "涨停次日不能追买——80% 会回落。"],
        "neutral": ["专注地把该做的做好，这票我先放一放。"],
    },
    "xin_dd": {
        "bullish": [
            "困境反转 + 撬板模式，超预期就买买买。",
            "主线就是热门，鑫多多去哪哪里热。",
            "低位埋伏完毕，剩下就是吹票出货——不是，是价值发现😄",
        ],
        "bearish": [
            "低于预期就卖卖卖，这票指引差。",
            "不做高位接力，只做困境反转——这票不是困境。",
        ],
        "neutral": ["还没到埋伏位。"],
    },

    # ═══════════════ Group G · 量化 ═══════════════
    "simons": {
        "bullish": ["价格统计异常出现买入信号，模型说买就买。"],
        "bearish": ["均值回归信号显示超买，减仓。"],
        "neutral": ["模型无明确信号。"],
    },
    "thorp": {
        "bullish": ["凯利公式给出正仓位，EV > 0 就下注。"],
        "bearish": ["期望值为负，不碰。"],
        "neutral": ["数学不撒谎——EV 接近零，不动。"],
    },
    "shaw": {
        "bullish": ["多因子评分位于 top 20%，质量动量都强。"],
        "bearish": ["多因子评分在底部 20%，全面卖出。"],
        "neutral": ["因子分散，中性。"],
    },

    # ═══════════════ Group I · AI 卡位/瓶颈猎手 ═══════════════
    # Serenity (@aleabitoreddit) — 语料源：references/serenity-voice.md
    "serenity": {
        "bullish": [
            "{name} 卡在 {industry} 那个不可替代的节点上——No substrate, no device，这种东西就是一台印钞机，anon。重仓，Then go long。",
            "我反向拆了整条 {industry} 供应链，{name} 是那个 60%+ 份额的双寡头瓶颈，市值还 grossly mispriced。市场还没 rotation 到这，我先埋。",
            "别人盯着终端大票，我只买它们离不开的公司。{name} 就是 {industry} 的卡脖子海峡——不可替代、扩产慢、没人定价。满仓不解释。",
            "这是 bottleneck of a bottleneck。{name} 卡死 {industry} 的命门，下游所有人都得求它供货。Then go long，PT 我敢往上画。",
        ],
        "bearish": [
            "{name} 在 {industry} 里随便就能被替代，三家厂都能供——没有卡点，对我没任何意义。Pass。",
            "盯着 {name} 的 EPS 没用，它根本不在 {industry} 的瓶颈上，只是条可被绕过的普通环节。不碰。",
            "供给一点都不紧，{industry} 这块产能随时能放量，{name} 没有任何不可替代性。这种我从不长。",
            "{name} 是终端的热门大票，不是卡脖子节点。挤在 consensus 里的拥挤交易，我反手观望甚至看空。",
        ],
        "neutral": [
            "{name} 在 {industry} 可能是个潜在卡点，但还没硬验证。等客户 roadmap 和缺货信号，再决定要不要 go long。",
            "{name} 的瓶颈逻辑成立一半——份额够集中，但扩产能不能跟上还没数据。等下一份财报电话会里的 backlog 和 ASP。",
            "故事有了，定价还没错配到位。{name} 卡位待 confirm，等机构 rotation 信号——在那之前我先小仓 tracking。",
        ],
    },

    # ═══ v3.8.1 · 13 位 v3.7.0 新晋评委台词（体检发现缺失 → 群聊只能用 generic fallback）═══
    "andreessen": {
        "bullish": [
            "Software is eating {industry}，而 {name} 拿着餐刀。网络效应一旦锁定，这就是下一个十年的平台。It's time to build——and to buy。",
            "{name} 是 founder mode 在 {industry} 的活样本：增长在 hyper 段，TAM 大到给得起十倍叙事。Techno-optimism, fully loaded。",
        ],
        "bearish": [
            "{industry} 是原子世界的生意，不是比特的——没有软件杠杆、没有零边际成本，{name} 进不了我的 thesis。",
            "{name} 没有网络效应、没有平台锁定，只是个 feature 不是 company。Pass。",
        ],
        "neutral": [
            "{name} 摸到了软件化的边，但 founder 还没证明能把 {industry} 的 playbook 跑通。Watch list。",
        ],
    },
    "gurley": {
        "bullish": [
            "All revenue is not created equal——{name} 的毛利结构告诉我这是高质量收入，{industry} 的 magnitude of demand 是真的。",
            "{name} 像极了早年的 marketplace 赢家：单位经济为正、复购在涨、烧钱倍数可控。这种生意我在 Benchmark 见过结局。",
        ],
        "bearish": [
            "{name} 的 EV/Revenue 已经脱离地心引力。估值不是荣誉勋章，是负债——{industry} 风口越大，这种票摔得越疼。",
            "单位经济跑不平——每单都亏钱靠规模翻盘的故事，{industry} 里十个死九个。",
        ],
        "neutral": [
            "{name} 的需求强度还行，但 take rate 和留存还没到我下注的置信度。再等两个季度的 cohort 数据。",
        ],
    },
    "naval": {
        "bullish": [
            "{name} 有 permissionless leverage——代码和品牌在 {industry} 里替它打工。买入然后睡觉，复利自己会跑。",
            "Specific knowledge 没法被培训出来，{name} 在 {industry} 的位置就是这种知识的变现。Play long-term games。",
        ],
        "bearish": [
            "{name} 是用时间换钱的生意，没有杠杆、没有复利曲线。Seek wealth, not money——这票两个都给不了。",
            "零和游戏里没有赢家，只有幸存者。{industry} 这种内卷场我不进。",
        ],
        "neutral": [
            "{name} 的杠杆雏形有了，但还看不出十年后它是否还在。判断力比勤奋值钱——我先不动。",
        ],
    },
    "gerstner": {
        "bullish": [
            "{name} 在 AI capex 超级周期的正确一侧：营收在加速而不是匀速，Rule of 40 轻松过线。Time to lean in。",
            "我们在 Altimeter 给 {industry} 建了完整模型——{name} 是 category leader，贵但增长撑得起。Own the disruptors。",
        ],
        "bearish": [
            "{name} 增速在减档但估值还停在加速档，这种剪刀差是经典减仓信号。",
            "{industry} 不在 AI 资本开支的受益链上，{name} 拿不到这一轮的 beta。",
        ],
        "neutral": [
            "{name} 的 Rule of 40 在及格线附近晃，下季度 guidance 决定方向。Hold, don't add。",
        ],
    },
    "chamath": {
        "bullish": [
            "Let me tell you why this matters：{name} 的 TAM 是千亿级，而市场还在用线性思维给指数曲线定价。Generational opportunity。",
            "{industry} 正在被重构，{name} 是拿着蓝图的玩家——盈利路径清晰、稀释可控。I'm in。",
        ],
        "bearish": [
            "{name} 是个 story stock——营收撑不起叙事，全靠 PPT 和热度。我做过 SPAC，我认得这种味道。",
            "披露质量这么差的公司，{industry} 再热我也不碰。Transparency or pass。",
        ],
        "neutral": [
            "{name} 的 thesis 我买一半：赛道对，但执行还没证明。Small position, big patience。",
        ],
    },
    "burry": {
        "bullish": [
            "{name}：资产真实、现金流真实、没人看。我买的从来不是热闹，是被错杀的数学。",
            "市场对 {industry} 的恐慌制造了这个价格。I may be early, but I'm not wrong。",
        ],
        "bearish": [
            "{name} 的估值只有在'这次不一样'成立时才合理。剧透：从来没有不一样过——这是泡沫篮子里的票。",
            "内部人在卖、散户在买，{industry} 的故事讲到第三章了。我见过这部电影的结局。",
        ],
        "neutral": [
            "{name} 还不够便宜到让我无视 {industry} 的周期风险。Watch. Wait. Reread the filings。",
        ],
    },
    "chanos": {
        "bullish": [
            "难得：{name} 的现金流和报表利润对得上、审计干净。{industry} 里这种诚实生意我不做空——这本身就是褒奖。",
        ],
        "bearish": [
            "{name} 的经营现金流和净利润背离了两年——利润是观点，现金是事实。Kynikos 的狗已经在叫了。",
            "CEO 在媒体上越活跃，我越想看应收账款。{name} 是教科书级的 promotional company。",
        ],
        "neutral": [
            "{name} 的账面还挑不出硬伤，但 {industry} 的会计弹性太大，我保留怀疑的权利。",
        ],
    },
    "zhang_lei": {
        "bullish": [
            "{name} 是值得'做时间的朋友'的生意：长跑道、宽护城河、与创始人的长期主义对齐。高瓴的钱是十年起步的。",
            "{industry} 的复利机器不多，{name} 的 track record 已经自我验证。与伟大格局观者同行，剩下交给时间。",
        ],
        "bearish": [
            "{name} 赚的是周期的钱不是结构的钱——时间不是它的朋友，是它的债主。",
            "创始人已经离场，{name} 失去了长期对齐的锚。这不是高瓴的菜。",
        ],
        "neutral": [
            "{name} 的生意质量够进研究清单，但价格还没到'重仓做时间朋友'的安全边际。继续跟踪。",
        ],
    },
    "asness": {
        "bullish": [
            "{name} 在我的三因子上全亮：价值便宜、质量扎实、动量向上。这不是观点，是回归系数。",
            "Value and momentum agreeing is rare——{name} 是 {industry} 里那个统计上的甜点。Factor 信号说买。",
        ],
        "bearish": [
            "{name} 是典型的 lottery ticket：高波动、负质量、纯靠故事。学术文献对这种票的长期回报只有一个词：糟糕。",
            "贵 + 质量差 + 动量崩——三因子全反向，{name} 在我的 short leg 里。",
        ],
        "neutral": [
            "{name} 的因子信号互相打架：价值说买、动量说等。Sin a little——小仓或者不动。",
        ],
    },
    "jensen_huang": {
        "bullish": [
            "The more you buy, the more you save——{name} 在 AI 工厂的关键链路上，数据中心 Capex 的洪水正流向它。",
            "{industry} 的需求按光速摩尔定律在跑，{name} 的产能就是入场券。We're at the iPhone moment of AI。",
        ],
        "bearish": [
            "{name} 不在加速计算的世界里——通用计算时代的生意，在 AI 工厂时代只会被重构。",
            "{industry} 跟 AI 算力链没有交集，这不是我视野里的供应商。",
        ],
        "neutral": [
            "{name} 摸到了 AI 链的边，但还没进认证名单。供应链的门票要靠良率和交付说话。",
        ],
    },
    "musk": {
        "bullish": [
            "用第一性原理拆 {name}：物理上成立、成本曲线能压、量产在爬坡。Production is hard——but they're through the hell。",
            "{industry} 需要的是垂直整合的疯子，{name} 有这个基因。",
        ],
        "bearish": [
            "{name} 是 legacy 玩家在 {industry} 的缝缝补补——第一性原理下这个成本结构就不该存在。",
            "PPT 造车我见多了。{name} 没有量产证据，物理不会撒谎。",
        ],
        "neutral": [
            "{name} 的方向对，但 production hell 还没走完。等下一次产能爬坡数据。",
        ],
    },
    "altman": {
        "bullish": [
            "{name} 卡在 AGI 供应链的瓶颈上——scaling laws 还在工作，算力和能源的需求曲线只会更陡。",
            "{industry} 是智能时代的基建，{name} 的位置会被未来十年的 compute 需求反复重新定价。",
        ],
        "bearish": [
            "{name} 在纯应用层，下一代模型可能把它的护城河直接蒸发。Build with the model, not against it。",
            "{industry} 不在 AGI 的传导链上，这一轮浪潮跟它关系不大。",
        ],
        "neutral": [
            "{name} 的 AI 叙事成立，但 scaling 红利还没落到财报上。Cautiously optimistic。",
        ],
    },
    "saylor": {
        "bullish": [
            "{name} 持有的是会升值的资产，欠的是会贬值的法币——这是数字时代的资产负债表炼金术。There is no second best。",
            "法币每年融化，{name} 在 {industry} 里找到了对冲熵增的方式。Buy the dip, then buy more。",
        ],
        "bearish": [
            "{name} 的资产负债表全是会融化的法币资产，没有硬通货敞口。这是在用冰块储蓄。",
            "{industry} 跟数字资产没有任何交集，我的框架对它无话可说。",
        ],
        "neutral": [
            "{name} 有一点数字资产敞口但不纯粹。半个信徒不如不信——观望。",
        ],
    },
    # v3.9.0 · 股海贼王 · 台词全部改写自其淘股吧真实发言 (docs/ghzw-dossier.md 有原文出处)
    "ghzw": {
        "bullish": [
            "{name} 复盘三问全答得上：为啥涨停、在 {industry} 板块什么地位、在大盘什么地位。主线+地位+承接都齐了，平盘就干。",
            "逻辑硬的低位票爆发力足——{name} 就是这种，有联创那样的榜样在前，低位+硬逻辑我从不犹豫。",
            "把 {name} 当 {industry} 这个时代的情绪载体看。当你的认知能判断它走出三五倍的时候，为什么恐高，为什么不格局？",
            "弱转强快速板才是超预期，{name} 今天这个回封就是。接力做的就是这种确认，不是猜。",
        ],
        "bearish": [
            "{name} 不在主线上。我十年做了两千多只票，全是跟着主线轮动出来的——逆主线做票就是给市场送钱。",
            "盘口承接不行，弱转强没确认。{name} 这种走势我等盘面给答案，盘面没给，就不进。",
            "高位接力六分之一的概率，错了太影响心态。{name} 现在这个位置我不满仓搞这种票。",
            "没有涨停基因、龙虎榜也没人气，{name} 接力没有抓手。短线是体力活，别把力气花在没人的票上。",
        ],
        "neutral": [
            "{name} 题材沾边但地位不清楚——是总龙还是跟风板？竞争格局没出来之前，我观望到尾盘再做决定。",
            "{name} 的逻辑在我认知内，但今天消息出来盘面已经反应了。晚上复盘看逻辑还在不在，再决定接不接力。",
            "每波行情赚十五个点就该休息——现在我仓位已经在主线票上，{name} 这种二线的先放观察。",
        ],
    },
}


def get_comment(investor_id: str, signal: str, ctx: dict) -> str:
    """Return a random signature comment for the given investor + signal.
    Substitutes variables from ctx (roe, pe, name, industry, stage, growth, price).
    Falls back to a generic line if investor not registered.
    """
    import random
    entry = PERSONAS.get(investor_id)
    if not entry:
        return _GENERIC_FALLBACK.get(signal, _GENERIC_FALLBACK["neutral"])[0]
    lines = entry.get(signal) or _GENERIC_FALLBACK.get(signal, _GENERIC_FALLBACK["neutral"])
    line = random.choice(lines)
    # Format safely — missing keys fall back to '—'
    try:
        return line.format(**{
            "roe": ctx.get("roe", "—"),
            "pe": ctx.get("pe", "—"),
            "price": ctx.get("price", "—"),
            "name": ctx.get("name", "这只票"),
            "industry": ctx.get("industry", "该行业"),
            "growth": ctx.get("growth", "—"),
            "stage": ctx.get("stage", "—"),
        })
    except (KeyError, IndexError):
        return line


_GENERIC_FALLBACK = {
    "bullish": ["数据支持买入。"],
    "bearish": ["数据不支持。"],
    "neutral": ["先观察。"],
    "skip": ["不在能力圈范围内，不做评价。"],
}


def stats() -> dict:
    """Report coverage of PERSONAS — how many investors are registered."""
    return {
        "total": len(PERSONAS),
        "bullish_lines": sum(len(v.get("bullish", [])) for v in PERSONAS.values()),
        "bearish_lines": sum(len(v.get("bearish", [])) for v in PERSONAS.values()),
        "neutral_lines": sum(len(v.get("neutral", [])) for v in PERSONAS.values()),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(stats(), indent=2))

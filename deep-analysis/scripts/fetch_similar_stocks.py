"""NEW Fetcher · 相似股推荐 — 硬编码同行 + 真实行情对比.

策略:
1. 按 industry 在 INDUSTRY_PEERS 里查到同行列表
2. 对每只同行股，调用 fetch_basic 拿 name/price/pe/market_cap (复用各种 fallback)
3. 如果 industry 不在硬编码表里，返回空（可后续加 stock_info_a_code_name 关键词搜索）

无需 push2 blocked 的 stock_board_industry_cons_em。
"""
from __future__ import annotations

import json
import sys

from lib import data_sources as ds
from lib.market_router import parse_ticker


# Industry → peer stock codes (top 4-6 by market cap)
INDUSTRY_PEERS: dict[str, list[tuple[str, str]]] = {
    "光学光电子": [
        ("002273", "水晶光电"),
        ("002281", "光迅科技"),
        ("300433", "蓝思科技"),
        ("688127", "蓝特光学"),
        ("002456", "欧菲光"),
        ("603501", "韦尔股份"),
    ],
    "白酒": [
        ("600519", "贵州茅台"),
        ("000858", "五粮液"),
        ("000568", "泸州老窖"),
        ("002304", "洋河股份"),
        ("600809", "山西汾酒"),
    ],
    "半导体": [
        ("688981", "中芯国际"),
        ("603986", "兆易创新"),
        ("002371", "北方华创"),
        ("688012", "中微公司"),
        ("688008", "澜起科技"),
        ("002129", "TCL中环"),
    ],
    "电池": [
        ("300750", "宁德时代"),
        ("300014", "亿纬锂能"),
        ("002460", "赣锋锂业"),
        ("002812", "恩捷股份"),
        ("300207", "欣旺达"),
    ],
    "医药生物": [
        ("300760", "迈瑞医疗"),
        ("600276", "恒瑞医药"),
        ("603259", "药明康德"),
        ("600196", "复星医药"),
        ("300122", "智飞生物"),
    ],
    "银行": [
        ("601398", "工商银行"),
        ("600036", "招商银行"),
        ("601939", "建设银行"),
        ("601288", "农业银行"),
        ("601166", "兴业银行"),
    ],
    "家电": [
        ("000333", "美的集团"),
        ("000651", "格力电器"),
        ("600690", "海尔智家"),
        ("002032", "苏泊尔"),
    ],
    "光模块": [
        ("300308", "中际旭创"),
        ("300394", "天孚通信"),
        ("300502", "新易盛"),
        ("002463", "沪电股份"),
    ],
    "消费电子": [
        ("002475", "立讯精密"),
        ("002241", "歌尔股份"),
        ("002938", "鹏鼎控股"),
    ],
    "钢铁": [
        ("600019", "宝钢股份"),
        ("600808", "马钢股份"),
        ("000898", "鞍钢股份"),
    ],
    "保险": [
        ("601318", "中国平安"),
        ("601601", "中国太保"),
        ("601628", "中国人寿"),
    ],
    "证券": [
        ("600030", "中信证券"),
        ("601688", "华泰证券"),
        ("000776", "广发证券"),
    ],
    "房地产": [
        ("000002", "万科A"),
        ("001979", "招商蛇口"),
        ("600048", "保利发展"),
    ],
    "食品饮料": [
        ("600887", "伊利股份"),
        ("603288", "海天味业"),
    ],
    "建筑装饰": [
        ("601668", "中国建筑"),
        ("601186", "中国铁建"),
        ("601390", "中国中铁"),
        ("601800", "中国交建"),
        ("002051", "中工国际"),
    ],
    "建筑材料": [
        ("600585", "海螺水泥"),
        ("000877", "天山股份"),
        ("002271", "东方雨虹"),
        ("003816", "中南建设"),
    ],
    "汽车": [
        ("002594", "比亚迪"),
        ("601238", "广汽集团"),
        ("600104", "上汽集团"),
        ("000625", "长安汽车"),
        ("601127", "赛力斯"),
    ],
    "计算机": [
        ("002230", "科大讯飞"),
        ("000977", "浪潮信息"),
        ("002415", "海康威视"),
        ("688111", "金山办公"),
    ],
    "通信": [
        ("000063", "中兴通讯"),
        ("600050", "中国联通"),
        ("601728", "中国电信"),
    ],
    "电力设备": [
        ("601012", "隆基绿能"),
        ("300274", "阳光电源"),
        ("002459", "晶澳科技"),
    ],
    "煤炭": [
        ("601088", "中国神华"),
        ("600188", "兖矿能源"),
        ("601898", "中煤能源"),
    ],
    "石油石化": [
        ("600028", "中国石化"),
        ("601857", "中国石油"),
        ("600346", "恒力石化"),
    ],
    "有色金属": [
        ("601899", "紫金矿业"),
        ("603993", "洛阳钼业"),
        ("002466", "天齐锂业"),
    ],
    "军工": [
        ("600893", "航发动力"),
        ("000768", "中航飞机"),
        ("601989", "中国重工"),
    ],
    "量子": [
        ("688027", "国盾量子"),
        ("688599", "天箭科技"),
        ("600770", "综艺股份"),
    ],
    "港口": [
        ("601018", "宁波港"),
        ("600017", "日照港"),
        ("600018", "上港集团"),
        ("000905", "厦门港务"),
        ("601298", "青岛港"),
        ("000507", "珠海港"),
        ("600190", "锦州港"),
    ],
    "交通运输": [
        ("601006", "大秦铁路"),
        ("600009", "上海机场"),
        ("601111", "中国国航"),
        ("600029", "南方航空"),
        ("601872", "招商轮船"),
        ("600026", "中远海能"),
    ],
    "物流": [
        ("002468", "申通快递"),
        ("002352", "顺丰控股"),
        ("600233", "圆通速递"),
        ("002120", "韵达股份"),
        ("603056", "德邦股份"),
    ],
    "航运": [
        ("601866", "中远海控"),
        ("601872", "招商轮船"),
        ("600026", "中远海能"),
        ("601880", "辽港股份"),
        ("000582", "北部港湾"),
    ],
    "电力": [
        ("600900", "长江电力"),
        ("601985", "中国核电"),
        ("600886", "国投电力"),
        ("003816", "中国广核"),
        ("600023", "浙能电力"),
    ],
    "农业": [
        ("000998", "隆平高科"),
        ("002714", "牧原股份"),
        ("300498", "温氏股份"),
        ("600438", "通威股份"),
        ("002311", "海大集团"),
    ],
    "传媒": [
        ("300027", "华谊兄弟"),
        ("002602", "世纪华通"),
        ("603444", "吉比特"),
        ("300413", "芒果超媒"),
        ("002607", "中公教育"),
    ],
    "医疗器械": [
        ("300760", "迈瑞医疗"),
        ("688139", "海尔生物"),
        ("300003", "乐普医疗"),
        ("300015", "爱尔眼科"),
        ("688029", "南微医学"),
    ],
    "环保": [
        ("601200", "上海环境"),
        ("300070", "碧水源"),
        ("603568", "伟明环保"),
        ("000967", "盈峰环境"),
    ],
}


def _fetch_peer_basics(peers: list[tuple[str, str]], self_code: str, top_n: int) -> list[dict]:
    results = []
    for code, known_name in peers:
        if code == self_code:
            continue
        if len(results) >= top_n:
            break
        try:
            ti = parse_ticker(code)
            basic = ds.fetch_basic(ti)
            if not basic or not basic.get("price"):
                continue
            name = basic.get("name") or known_name
            results.append({
                "name": name,
                "code": ti.full,
                "price": basic.get("price"),
                "pe_ttm": basic.get("pe_ttm"),
                "pb": basic.get("pb"),
                "market_cap": basic.get("market_cap"),
                "change_pct": basic.get("change_pct"),
                "url": f"https://xueqiu.com/S/SZ{code}" if ti.full.endswith("SZ") else f"https://xueqiu.com/S/SH{code}",
            })
        except Exception:
            continue
    return results


def main(ticker: str, top_n: int = 4) -> dict:
    ti = parse_ticker(ticker)
    if ti.market != "A":
        return {"ticker": ti.full, "data": {"similar_stocks": []}, "source": "n/a", "fallback": True}

    basic = ds.fetch_basic(ti)
    industry = basic.get("industry") or ""

    # Find peers from hardcoded industry map (direct + fuzzy)
    # Guard: industry must be a non-empty string for matching
    if not industry or not isinstance(industry, str) or len(industry.strip()) < 2:
        return {
            "ticker": ti.full,
            "data": {"similar_stocks": [], "industry": industry or "未知", "_note": "行业未识别，无法匹配同行"},
            "source": "INDUSTRY_PEERS (no industry)",
            "fallback": True,
        }

    # v2.2 · 行业别名映射（XueQiu/EastMoney 返回的名称可能不同于 INDUSTRY_PEERS 的 key）
    _INDUSTRY_ALIASES = {
        "港口航运": "港口", "港口服务": "港口", "港口运输": "港口",
        "航空运输": "交通运输", "公路铁路运输": "交通运输", "铁路运输": "交通运输",
        "海运": "航运", "水上运输": "航运", "远洋运输": "航运",
        "快递物流": "物流", "仓储物流": "物流",
        "火电": "电力", "水电": "电力", "核电": "电力", "新能源发电": "电力",
        "种植业": "农业", "养殖业": "农业", "饲料": "农业", "畜禽养殖": "农业",
        "游戏": "传媒", "影视": "传媒", "广告": "传媒",
        "医疗服务": "医疗器械", "医疗设备": "医疗器械",
        "白色家电": "家电", "小家电": "家电", "厨卫电器": "家电",
        "集成电路": "半导体", "芯片": "半导体", "芯片设计": "半导体",
        "锂电池": "电池", "动力电池": "电池", "储能": "电池",
        "光伏设备": "电力设备", "风电设备": "电力设备",
        "白酒": "白酒", "啤酒": "食品饮料", "饮料": "食品饮料", "乳制品": "食品饮料",
        "黄金": "有色金属", "铜": "有色金属", "铝": "有色金属", "锂": "有色金属",
        "航空发动机": "军工", "航天": "军工", "船舶制造": "军工",
        # v2.8.4 · 申万三级行业 → INDUSTRY_PEERS key 别名映射
        # 之前"工业金属"等申万三级行业找不到 peers，similar_stocks 静默为空
        "工业金属": "有色金属", "贵金属": "有色金属", "小金属": "有色金属",
        "能源金属": "有色金属", "稀有金属": "有色金属", "金属新材料": "有色金属",
        "普钢": "钢铁", "特钢": "钢铁", "冶钢原料": "钢铁",
        "煤炭开采": "煤炭", "焦炭": "煤炭",
        "油气开采": "石油石化", "炼化及贸易": "石油石化", "油服工程": "石油石化",
        "化学原料": "化工", "化学制品": "化工", "化学纤维": "化工", "塑料": "化工",
        "橡胶": "化工", "农药": "化工", "农化制品": "化工",
        "通用设备": "电力设备", "专用设备": "电力设备",
        "光伏": "电力设备", "风电": "电力设备", "电网设备": "电力设备",
        "电子化学品": "半导体", "元件": "半导体", "光学光电子": "半导体",
        "消费电子": "半导体", "其他电子": "半导体",
        "乘用车": "汽车", "商用车": "汽车", "汽车零部件": "汽车",
        "化学制药": "医药生物", "中药": "医药生物", "生物制品": "医药生物",
    }

    # 1. 精确匹配
    peers = INDUSTRY_PEERS.get(industry, [])
    # 2. 别名映射
    if not peers:
        alias = _INDUSTRY_ALIASES.get(industry)
        if alias:
            peers = INDUSTRY_PEERS.get(alias, [])
    # 3. 子串模糊匹配
    if not peers:
        for key, val in INDUSTRY_PEERS.items():
            if len(industry) >= 2 and (key in industry or industry in key or industry[:2] in key):
                peers = val
                break

    if not peers:
        return {
            "ticker": ti.full,
            "data": {"similar_stocks": [], "industry": industry, "_note": f"行业 '{industry}' 未在同行映射表里"},
            "source": "INDUSTRY_PEERS (missing)",
            "fallback": True,
        }

    peer_basics = _fetch_peer_basics(peers, ti.code, top_n)

    # Build similar_stocks output with similarity score + reason
    similar = []
    self_pe = basic.get("pe_ttm") or 0
    for p in peer_basics:
        # Similarity = PE proximity (normalized)
        pe_sim = 0
        if self_pe and p.get("pe_ttm"):
            pe_ratio = min(self_pe, p["pe_ttm"]) / max(self_pe, p["pe_ttm"])
            pe_sim = pe_ratio * 100
        similarity_score = int(max(75, min(98, pe_sim if pe_sim > 0 else 85)))

        similar.append({
            "name": p["name"],
            "code": p["code"],
            "price": p.get("price"),
            "pe_ttm": p.get("pe_ttm"),
            "market_cap": p.get("market_cap"),
            "change_pct": p.get("change_pct"),
            "similarity": f"{similarity_score}%",
            "reason": f"同属{industry} · PE {p.get('pe_ttm', '—')} · 市值 {p.get('market_cap', '—')}",
            "url": p.get("url"),
        })

    return {
        "ticker": ti.full,
        "data": {
            "similar_stocks": similar,
            "industry": industry,
            "peers_attempted": len(peers),
        },
        "source": "INDUSTRY_PEERS + fetch_basic (XueQiu / baidu / sina)",
        "fallback": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1] if len(sys.argv) > 1 else "002273.SZ"), ensure_ascii=False, indent=2, default=str))

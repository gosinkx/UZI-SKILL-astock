"""Dimension 5 · 上下游产业链 — 产出 main_business_breakdown (viz 需要的饼图数据)."""
from __future__ import annotations

import json
import sys

import akshare as ak  # type: ignore
from lib.market_router import parse_ticker


def _float(v) -> float:
    try:
        s = str(v).replace("%", "").replace(",", "")
        return float(s) if s and s not in ("nan", "-") else 0.0
    except (ValueError, TypeError):
        return 0.0


def main(ticker: str) -> dict:
    ti = parse_ticker(ticker)
    main_business: list = []
    breakdown_top: list = []
    ths_zyjs: dict = {}

    if ti.market == "A":
        # Source A · 同花顺 主营介绍 (bypasses eastmoney push2)
        try:
            df = ak.stock_zyjs_ths(symbol=ti.code)
            if df is not None and not df.empty:
                row = df.iloc[0]
                ths_zyjs = {
                    "主营业务": str(row.get("主营业务", "")),
                    "产品类型": str(row.get("产品类型", "")),
                    "产品名称": str(row.get("产品名称", "")),
                    "经营范围": str(row.get("经营范围", ""))[:200],
                }
        except Exception as e:
            ths_zyjs = {"error": str(e)[:80]}

        try:
            # stock_zygc_em 需要带前缀的 symbol，例如 SZ002273
            sym_with_prefix = f"{'SZ' if ti.full.endswith('SZ') else 'SH'}{ti.code}"
            df = ak.stock_zygc_em(symbol=sym_with_prefix)
            if df is not None and not df.empty:
                main_business = df.head(50).to_dict("records")

                # 抽最新报告期 × 按"分产品" 聚合
                if "报告日期" in df.columns:
                    latest_date = df["报告日期"].iloc[0]
                    df_latest = df[df["报告日期"] == latest_date]
                else:
                    df_latest = df.head(20)

                # 优先"分产品"，其次"分行业"，最后全部
                product_col = None
                for kw in ["分产品", "分行业", "按产品", "主营构成"]:
                    if "分类" in df_latest.columns:
                        sub = df_latest[df_latest["分类"].astype(str).str.contains(kw, na=False)]
                        if not sub.empty:
                            df_latest = sub
                            product_col = kw
                            break

                # 聚合
                name_col = next((c for c in ["项目", "分项", "名称", "主营构成"] if c in df_latest.columns), None)
                value_col = next((c for c in ["主营收入-同比增长(%)", "收入-金额", "营业收入", "主营收入"] if c in df_latest.columns), None)
                pct_col = next((c for c in ["主营收入-收入比例(%)", "收入比例", "占比"] if c in df_latest.columns), None)

                if name_col and (value_col or pct_col):
                    items = []
                    for _, row in df_latest.iterrows():
                        name = str(row.get(name_col, ""))
                        if not name or name in ("nan", "合计", "总计"):
                            continue
                        if pct_col:
                            v = _float(row.get(pct_col))
                        else:
                            v = _float(row.get(value_col)) / 1e8
                        if v > 0:
                            items.append({"name": name[:12], "value": round(v, 1)})
                    items.sort(key=lambda x: -x["value"])
                    breakdown_top = items[:6]
        except Exception as e:
            main_business = [{"error": str(e)}]

    # v2.2 · 从主营业务 + 产品类型 + 经营范围推断上下游
    upstream = "—"
    downstream = "—"
    products = "—"
    if ths_zyjs and "error" not in ths_zyjs:
        biz = ths_zyjs.get("主营业务", "") or ""
        prod = ths_zyjs.get("产品类型", "") or ""
        scope = ths_zyjs.get("经营范围", "") or ""

        # 产品/服务
        if prod and prod not in ("nan", "—", ""):
            products = prod[:100]
        elif biz:
            products = biz[:100]

        # 下游：从主营业务反推客户方向
        if biz:
            downstream = biz[:80]

        # 上游：从产品类型和经营范围推断原材料/供应商方向
        # 常见上游关键词映射
        _UPSTREAM_HINTS = {
            "港口": "航运公司、进出口贸易商、物流企业",
            "航运": "造船厂、燃油供应商、港口服务",
            "建筑": "水泥/钢材/砂石供应商、劳务分包商",
            "房地产": "建材供应商、建筑承包商、设计院",
            "汽车": "零部件供应商、钢铁/铝材、电子元器件",
            "电池": "正极/负极/电解液/隔膜材料供应商",
            "半导体": "晶圆代工、光刻机、EDA 工具、材料",
            "医药": "原料药供应商、CRO/CDMO、包装材料",
            "白酒": "粮食采购、包装材料、物流",
            "光伏": "硅料/硅片/电池片供应商",
            "钢铁": "铁矿石/焦炭供应商",
            "煤炭": "采矿设备、运输物流",
            "银行": "央行/同业资金、存款客户",
            "保险": "再保险公司、精算/IT 服务商",
            "电力": "煤炭/天然气供应商、设备制造商",
            "食品": "农产品原料供应商、包装材料",
            "家电": "面板/压缩机/芯片供应商",
            "通信": "光纤光缆、基站设备、芯片供应商",
            "计算机": "芯片/存储/服务器供应商",
        }
        combined = f"{biz} {prod} {scope}"
        for hint_key, hint_val in _UPSTREAM_HINTS.items():
            if hint_key in combined:
                upstream = hint_val
                break

        # 如果没匹配到，尝试从经营范围提取
        if upstream == "—" and scope:
            upstream = f"(从经营范围推断) {scope[:80]}"

    return {
        "ticker": ti.full,
        "data": {
            "main_business_breakdown": breakdown_top,
            "main_business_raw": main_business[:20],
            "ths_zyjs": ths_zyjs,
            "products": products,
            "upstream": upstream,
            "downstream": downstream,
            "client_concentration": "—",
            "supplier_concentration": "—",
            "_note": "上下游基于主营/产品/经营范围推断，精确数据需年报附注",
        },
        "source": "akshare:stock_zygc_em + stock_zyjs_ths",
        "fallback": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1] if len(sys.argv) > 1 else "002273.SZ"), ensure_ascii=False, indent=2, default=str))

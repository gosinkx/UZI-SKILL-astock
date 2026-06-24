#!/usr/bin/env python3
"""v2.10.2 · 预热 cache 生成脚本 · 全公开数据，0 敏感信息.

目的:
  Codex + 首次安装机器慢的根因是 `.cache/_global/api_cache/` 为空导致
  所有 ddgs / 行业分类 / 基金 NAV 都得真实跑一遍。本脚本一次性跑完
  这些"所有用户都会用到的公开数据"，输出 prewarm/ 目录可打包分发。

用法:
    # 本地跑一次生成预热包
    python prewarm_cache.py

    # 输出: prewarm/api_cache/*.json
    # 打包: tar czf prewarm-v2.10.tar.gz prewarm/

用户侧使用:
    curl -L https://github.com/wbh604/UZI-Skill/releases/download/v2.10.2/prewarm-v2.10.tar.gz | tar xz
    mv prewarm/api_cache/* skills/deep-analysis/scripts/.cache/_global/api_cache/

安全保证（绝不打包）:
  - .env / MX_APIKEY / 任何 API 凭证
  - 用户雪球 cookie (~/.uzi-skill/playwright-xueqiu/)
  - 用户跑过的 .cache/<ticker>/  (可能暴露投资偏好)
  - 任何含用户本机绝对路径的内容
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

warnings.filterwarnings("ignore")
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

OUT_DIR = SCRIPT_DIR / "prewarm" / "api_cache"


def _ensure_out() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # 安全检查：确保输出目录不在 user home 下（防止意外把用户数据带走）
    out_str = str(OUT_DIR.resolve())
    assert "UZI-Skill" in out_str, f"安全检查失败: 输出路径可疑 {out_str}"


def _save(key: str, data) -> None:
    """保存一条 cache entry，格式匹配 lib.cache.cached 的写入格式."""
    p = OUT_DIR / f"{key}.json"
    payload = {"_cached_at": datetime.now().isoformat(timespec="seconds"), "data": data}
    p.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")


def warm_industry_taxonomy() -> int:
    """证监会行业分类 · 所有 A 股通用 · 日级更新."""
    print("\n[1/5] 证监会行业分类 · 近 7 日")
    import akshare as ak
    today = datetime.now()
    n = 0
    for i in range(1, 8):
        d = (today - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = ak.stock_industry_pe_ratio_cninfo(symbol="证监会行业分类", date=d)
            if df is None or df.empty:
                continue
            key = f"industry_pe__{d}"
            _save(key, df.to_dict("records"))
            n += 1
            print(f"    ✓ {d}: {len(df)} 行")
        except Exception as e:
            print(f"    ✗ {d}: {type(e).__name__}: {str(e)[:60]}")
    return n


def warm_stock_name_table() -> int:
    """A 股全量 code ↔ name 映射 · 中文名解析用."""
    print("\n[2/5] A 股全量 code ↔ name 表")
    import akshare as ak
    try:
        df = ak.stock_info_a_code_name()
        if df is not None and not df.empty:
            _save("stock_info_a_code_name", df.to_dict("records"))
            print(f"    ✓ 共 {len(df)} 只 A 股")
            return 1
    except Exception as e:
        print(f"    ✗ {type(e).__name__}: {str(e)[:80]}")
    return 0


def warm_qualitative_searches() -> int:
    """v2.10.2 · 高频 ddgs 定性查询，让 fetch_macro/policy/moat 首跑命中 cache.

    只预热**跨股通用**的查询（宏观/行业）· 不预热个股特定查询（那会带用户色彩）。
    """
    print("\n[3/5] 高频 ddgs 定性查询（权威域）")
    from lib.web_search import search_trusted

    year = datetime.now().year
    # 所有用户分析任何 A 股都会触发的"跨股通用"查询
    UNIVERSAL_QUERIES = [
        # 3_macro · 宏观
        ("3_macro", f"{year} 中国 利率 货币政策 降息 最新"),
        ("3_macro", f"{year} 美联储 利率周期 最新"),
        ("3_macro", f"{year} 人民币 汇率 走势"),
        # 13_policy · 常见行业政策
        ("13_policy", f"{year} 白酒 国家政策 扶持 利好"),
        ("13_policy", f"{year} 半导体 国产替代 政策"),
        ("13_policy", f"{year} 新能源 政策 利好"),
        ("13_policy", f"{year} 医药 集采 政策"),
        ("13_policy", f"{year} 有色金属 国家政策"),
        ("13_policy", f"{year} 工业金属 政策 扶持"),
        # 14_moat · 常见行业护城河关键词
        ("14_moat", f"白酒 上市公司 品牌壁垒 竞争优势"),
        ("14_moat", f"半导体 上市公司 专利 核心技术"),
        ("14_moat", f"新能源 上市公司 市场份额 龙头"),
    ]
    n = 0
    for dim_key, q in UNIVERSAL_QUERIES:
        try:
            # search_trusted 内部用 lib.cache.cached，写到 _global/api_cache
            results = search_trusted(q, dim_key=dim_key, max_results=4)
            if results and "error" not in (results[0] if results else {}):
                n += 1
                print(f"    ✓ [{dim_key}] {q[:50]}... ({len(results)} 条)")
        except Exception as e:
            print(f"    ✗ {q[:40]}: {type(e).__name__}")
    return n


def warm_common_fund_nav() -> int:
    """常见公募基金经理的 5Y NAV · 多股共享（一个基金可能被多只股票的分析引用）."""
    print("\n[4/5] Top 20 公募基金 5Y NAV")
    import akshare as ak
    # 代表性公募基金（张坤/谢治宇/朱少醒等 Top 大佬管理的几只）
    COMMON_FUNDS = [
        "005827",  # 易方达蓝筹精选（张坤）
        "163402",  # 兴全趋势（谢治宇）
        "519035",  # 富国天惠（朱少醒）
        "001856",  # 兴全合润
        "519732",  # 交银精选回报
        "110011",  # 易方达优质精选（萧楠）
        "001875",  # 前海开源中航军工
        "161725",  # 招商中证白酒指数
        "005669",  # 广发高端制造
        "004674",  # 鹏华优势
    ]
    n = 0
    for code in COMMON_FUNDS:
        try:
            df = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
            if df is not None and not df.empty:
                # 保留近 5 年
                cutoff = f"{datetime.now().year - 5}-01-01"
                date_col = "净值日期" if "净值日期" in df.columns else df.columns[0]
                df5 = df[df[date_col].astype(str) >= cutoff] if date_col else df
                key = f"fund_nav__{code}"
                _save(key, df5.tail(1500).to_dict("records"))
                n += 1
                print(f"    ✓ {code}: {len(df5)} 个 NAV 点")
        except Exception as e:
            print(f"    ✗ {code}: {type(e).__name__}: {str(e)[:60]}")
    return n


def warm_futures_main() -> int:
    """主要期货品种 12 个月历史 · 8_materials / 9_futures 所有金属/能源股通用."""
    print("\n[5/5] 主连期货价格（12 个月）")
    import akshare as ak
    SYMBOLS = ["AL0", "CU0", "ZN0", "NI0", "AU0", "AG0", "SN0", "PB0",
               "RB0", "I0", "J0", "JM0", "ZC0", "SC0", "MA0", "PP0", "V0"]
    n = 0
    for sym in SYMBOLS:
        try:
            df = ak.futures_main_sina(symbol=sym)
            if df is not None and not df.empty:
                key = f"futures_main__{sym}"
                _save(key, df.tail(260).to_dict("records"))
                n += 1
                print(f"    ✓ {sym}: {len(df)} 行")
        except Exception as e:
            print(f"    ✗ {sym}: {type(e).__name__}")
    return n


def sanity_check_output() -> None:
    """生成后扫一遍输出，确保没有敏感信息混入."""
    print("\n[SAFETY] 输出内容敏感性扫描")
    suspicious_patterns = [
        # 常见 API key 格式
        ("sk-", "OpenAI key 格式"),
        ("mkt_", "MX API key 格式"),
        ("pk_", "私钥格式"),
        # 个人路径
        ("/Users/", "macOS 个人路径"),
        ("/home/", "Linux 个人路径"),
        ("C:\\Users\\", "Windows 个人路径"),
        # 邮箱 / 电话
        ("@qq.com", "QQ 邮箱"),
        ("@163.com", "163 邮箱"),
        ("@gmail.com", "Gmail"),
    ]
    issues = []
    for f in OUT_DIR.glob("*.json"):
        content = f.read_text(encoding="utf-8", errors="replace")
        for pat, label in suspicious_patterns:
            if pat in content:
                issues.append(f"  {f.name}: 含 {label} ({pat!r})")
    if issues:
        print("  ⚠️ 发现潜在敏感内容：")
        for i in issues: print(i)
        print("  请人工审查后再打包分发")
    else:
        print("  ✓ 扫描通过，未发现敏感信息")


def main() -> int:
    _ensure_out()
    print(f"输出目录: {OUT_DIR}")
    print(f"开始预热 @ {datetime.now().isoformat(timespec='seconds')}\n")

    total = 0
    total += warm_industry_taxonomy()
    total += warm_stock_name_table()
    total += warm_qualitative_searches()
    total += warm_common_fund_nav()
    total += warm_futures_main()

    sanity_check_output()

    # 大小统计
    total_bytes = sum(f.stat().st_size for f in OUT_DIR.glob("*.json"))
    file_count = len(list(OUT_DIR.glob("*.json")))
    print(f"\n=== 完成 ===")
    print(f"生成 {file_count} 个 cache 文件 · 共 {total_bytes/1024:.1f} KB")
    print(f"→ 打包: tar czf prewarm-$(cat .version-bump.json | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"version\"])').tar.gz prewarm/")
    print(f"→ 用户下载后解压到: .cache/_global/api_cache/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

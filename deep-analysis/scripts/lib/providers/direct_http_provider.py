"""Direct HTTP provider · v2.10.3 · 脱离 akshare/yfinance 包装，直连网站抓行情.

**为什么**:
  1. akshare 内部全是爬虫，上游网站改版经常挂
  2. 直连腾讯/新浪/etnet 官方行情接口更稳，且国内友好
  3. 对 GFW 代理挂场景，直连的 HTTPS 比 akshare 走的 push2 更可靠

**覆盖**:
  - 腾讯 qt (qt.gtimg.cn)：A/H/U 三市场实时快照
  - 腾讯 ifzq (web.ifzq.gtimg.cn)：K 线历史
  - 新浪 hq (hq.sinajs.cn)：A/H/U 实时
  - etnet 港股页面：HTML 解析现价

**0 key · 国内直连稳定**（这些站点国内浏览器可见即可）

这是 Codex 提议 `fetch_web_quote.py` 的正式实现，做成 provider 框架的一员，
不是独立脚本。
"""
from __future__ import annotations

import re
from . import register, ProviderError

try:
    import requests
    _REQ_OK = True
except ImportError:
    requests = None
    _REQ_OK = False


_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"


class _DirectHttpProvider:
    """直连站点行情源 · 包含腾讯 qt / 新浪 hq / etnet 三个子源."""

    name = "direct_http"
    requires_key = False
    markets = ("A", "H", "U")

    def is_available(self) -> bool:
        return _REQ_OK

    # ═══════════════════════════════════════════════════════════════
    # 腾讯 qt.gtimg.cn · A/H/U 实时快照
    # ═══════════════════════════════════════════════════════════════
    def fetch_quote_tencent(self, code: str, market: str) -> dict:
        """
        腾讯 qt 实时行情，返回 {price, open, prev_close, high, low, volume, amount}.

        code format: A 股 6 位 (600519) / HK 5 位 (00700) / US 字母 (AAPL)
        market: "A" / "H" / "U"
        """
        if not _REQ_OK:
            raise ProviderError("requests 未安装")

        if market == "A":
            # sh600519 / sz000001
            prefix = "sh" if code.startswith(("6", "9", "5", "1")) else "sz"
            qt_code = f"{prefix}{code}"
        elif market == "H":
            # hk00700
            qt_code = f"hk{code.zfill(5)}"
        elif market == "U":
            # usAAPL.OQ / usAAPL.N（腾讯要求加交易所后缀，不知道默认试 .OQ）
            qt_code = f"us{code.upper()}"
        else:
            raise ProviderError(f"unsupported market: {market!r}")

        url = f"http://qt.gtimg.cn/q={qt_code}"
        try:
            r = requests.get(url, headers={"User-Agent": _UA}, timeout=8)
            r.encoding = "gbk"
            text = r.text.strip()
        except Exception as e:
            raise ProviderError(f"tencent qt: {type(e).__name__}: {e}")

        # 格式: v_sh600519="1~贵州茅台~600519~1500.0~1520.0~..."
        m = re.search(r'"([^"]+)"', text)
        if not m:
            raise ProviderError(f"tencent qt empty response: {text[:80]}")
        parts = m.group(1).split("~")
        if len(parts) < 33:
            raise ProviderError(f"tencent qt short response: {len(parts)} fields")

        # 字段顺序（A 股 market=51）: 状态 / 名称 / 代码 / 当前价 / 昨收 / 今开 / 成交量(手) / 外盘 / 内盘 / 买一 ...
        # 港股/美股字段略有不同，但前 6 个位置基本一致
        try:
            return {
                "name": parts[1],
                "code": parts[2],
                "price": float(parts[3] or 0),
                "prev_close": float(parts[4] or 0),
                "open": float(parts[5] or 0),
                "volume": float(parts[6] or 0),
                "high": float(parts[33] if len(parts) > 33 else 0) or None,
                "low": float(parts[34] if len(parts) > 34 else 0) or None,
                "amount": float(parts[37] if len(parts) > 37 else 0) or None,
                "source": f"tencent_qt:{qt_code}",
            }
        except (ValueError, IndexError) as e:
            raise ProviderError(f"tencent qt parse: {e}")

    # ═══════════════════════════════════════════════════════════════
    # 新浪 hq.sinajs.cn · A/H/U 实时快照
    # ═══════════════════════════════════════════════════════════════
    def fetch_quote_sina(self, code: str, market: str) -> dict:
        if not _REQ_OK:
            raise ProviderError("requests 未安装")

        if market == "A":
            prefix = "sh" if code.startswith(("6", "9", "5", "1")) else "sz"
            sina_code = f"{prefix}{code}"
        elif market == "H":
            # 新浪港股 hk00700
            sina_code = f"hk{code.zfill(5)}"
        elif market == "U":
            # 新浪美股 gb_ 前缀小写
            sina_code = f"gb_{code.lower()}"
        else:
            raise ProviderError(f"unsupported market: {market!r}")

        url = f"http://hq.sinajs.cn/list={sina_code}"
        try:
            r = requests.get(url, headers={
                "User-Agent": _UA,
                "Referer": "http://finance.sina.com.cn",
            }, timeout=8)
            r.encoding = "gbk"
            text = r.text.strip()
        except Exception as e:
            raise ProviderError(f"sina hq: {type(e).__name__}: {e}")

        # 格式: var hq_str_sh600519="贵州茅台,1520.00,1500.00,..."
        m = re.search(r'"([^"]+)"', text)
        if not m:
            raise ProviderError(f"sina hq empty: {text[:80]}")
        fields = m.group(1).split(",")
        if len(fields) < 6:
            raise ProviderError(f"sina hq too short")

        try:
            if market == "A":
                # 0:名称 1:开盘 2:昨收 3:当前 4:最高 5:最低 6:买一 7:卖一 8:成交量 9:成交额
                return {
                    "name": fields[0],
                    "code": code,
                    "open": float(fields[1] or 0),
                    "prev_close": float(fields[2] or 0),
                    "price": float(fields[3] or 0),
                    "high": float(fields[4] or 0),
                    "low": float(fields[5] or 0),
                    "volume": float(fields[8] or 0) if len(fields) > 8 else 0,
                    "amount": float(fields[9] or 0) if len(fields) > 9 else 0,
                    "source": f"sina_hq:{sina_code}",
                }
            elif market == "H":
                # 0:英文名 1:中文名 2:开盘 3:昨收 4:最高 5:最低 6:当前 ...
                return {
                    "name": fields[1] if len(fields) > 1 else "",
                    "code": code,
                    "open": float(fields[2] or 0),
                    "prev_close": float(fields[3] or 0),
                    "high": float(fields[4] or 0),
                    "low": float(fields[5] or 0),
                    "price": float(fields[6] or 0),
                    "source": f"sina_hq:{sina_code}",
                }
            else:  # U
                # 美股字段: name / price / change_pct / change / open / high / low / prev_close ...
                return {
                    "name": fields[0],
                    "code": code,
                    "price": float(fields[1] or 0),
                    "open": float(fields[5] or 0) if len(fields) > 5 else None,
                    "high": float(fields[6] or 0) if len(fields) > 6 else None,
                    "low": float(fields[7] or 0) if len(fields) > 7 else None,
                    "prev_close": float(fields[26] or 0) if len(fields) > 26 else None,
                    "source": f"sina_hq:{sina_code}",
                }
        except (ValueError, IndexError) as e:
            raise ProviderError(f"sina hq parse: {e}")

    # ═══════════════════════════════════════════════════════════════
    # etnet.com.hk · 港股页面级 fallback
    # ═══════════════════════════════════════════════════════════════
    def fetch_quote_etnet(self, code: str) -> dict:
        """etnet 港股页面解析。仅在腾讯/新浪都挂时用."""
        if not _REQ_OK:
            raise ProviderError("requests 未安装")

        code5 = code.zfill(5).lstrip("0") or "0"  # etnet 不要前导 0
        url = f"https://www.etnet.com.hk/www/tc/stocks/realtime/quote.php?code={code5}"
        try:
            r = requests.get(url, headers={"User-Agent": _UA}, timeout=10)
        except Exception as e:
            raise ProviderError(f"etnet: {type(e).__name__}: {e}")

        html = r.text
        # 现价抓取 (etnet 页面有 class 标记)
        # 简单正则抓关键字段
        def _find(pattern, default=None):
            m = re.search(pattern, html)
            return m.group(1) if m else default

        price_str = _find(r'realTimeQuote[^>]*>([\d.]+)', None) or \
                    _find(r'"lastPrice"[^>]*>([\d.]+)', None)
        if not price_str:
            raise ProviderError("etnet: price element not found")

        return {
            "code": code,
            "price": float(price_str),
            "source": f"etnet:{code5}",
            "_note": "页面级 fallback，字段不全",
        }

    # ═══════════════════════════════════════════════════════════════
    # 统一入口 · chain 式兜底
    # ═══════════════════════════════════════════════════════════════
    def fetch_quote(self, code: str, market: str) -> dict:
        """腾讯 → 新浪 → etnet（港股）三级兜底."""
        errors = []
        # 1. 腾讯
        try:
            return self.fetch_quote_tencent(code, market)
        except ProviderError as e:
            errors.append(str(e))
        # 2. 新浪
        try:
            return self.fetch_quote_sina(code, market)
        except ProviderError as e:
            errors.append(str(e))
        # 3. etnet（仅港股）
        if market == "H":
            try:
                return self.fetch_quote_etnet(code)
            except ProviderError as e:
                errors.append(str(e))
        raise ProviderError(f"direct_http all failed: {' | '.join(errors)}")


register(_DirectHttpProvider())

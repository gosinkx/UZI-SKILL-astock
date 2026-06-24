"""Regression for v3.6.2 · 社群反馈两点修复.

#68 (@xy2yp) · cninfo 翻页 854 长尾导致采集卡几小时
#69 (@FrankHuy) · install-hermes.sh 在 Linux 找不到 pip · akshare 装不上

测试覆盖：
1. _cninfo_direct_api 用 pageSize=30 pageNum=1 · 网络失败时静默返 [] · 不抛
2. _cninfo_disclosures · 直连 OK 时不调 akshare 慢路径
3. _cninfo_disclosures · UZI_AK_CNINFO_FALLBACK 未设时 · 直连失败也不调 akshare
4. install-hermes.sh · 含 Python 版本预检 (>=3.10)
5. install-hermes.sh · pip 探测级联 (venv → pip → pip3 → python -m pip)
6. install-hermes.sh · 完全找不到 pip 时给清晰错误指引 · 不静默 fail
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = REPO_ROOT / "skills" / "deep-analysis" / "scripts"
SCRIPT = REPO_ROOT / "install-hermes.sh"
sys.path.insert(0, str(SCRIPTS))


# ─── #1 · cninfo 直连 API ────────────────────────────────

def test_cninfo_direct_api_uses_page_size_30():
    """v3.6.2 关键：pageSize=30 · pageNum=1 · 永不翻全部页."""
    src = (SCRIPTS / "fetch_events.py").read_text(encoding="utf-8")
    assert "_cninfo_direct_api" in src
    assert '"pageSize": 30' in src or "page_size: int = 30" in src
    assert '"pageNum": 1' in src
    # 必须设硬超时 · 不能卡死
    assert "timeout=15" in src or "timeout: int = 15" in src


def test_cninfo_direct_api_returns_empty_on_network_failure():
    """网络异常 · 必须返 [] · 不抛 · 不阻塞 · 让 fallback 接手."""
    from fetch_events import _cninfo_direct_api

    with patch("requests.post") as mock_post:
        import requests
        mock_post.side_effect = requests.ConnectionError("simulated network down")
        rows = _cninfo_direct_api("000958")
        assert rows == []


def test_cninfo_direct_api_returns_empty_on_bad_json():
    """服务器返非 JSON · 必须返 [] · 不抛."""
    from fetch_events import _cninfo_direct_api

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("not json")
        mock_post.return_value = mock_resp
        rows = _cninfo_direct_api("000958")
        assert rows == []


def test_cninfo_direct_api_parses_valid_response():
    """正常返 30 条 · 解析 announcementTitle / announcementTime."""
    from fetch_events import _cninfo_direct_api

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "announcements": [
                {"announcementTitle": "年报", "announcementTime": 1717545600000,
                 "adjunctUrl": "/finalpage/2026-01-01/x.pdf"},
                {"announcementTitle": "公告 2", "announcementTime": 1717459200000,
                 "adjunctUrl": "/finalpage/2026-01-02/y.pdf"},
            ]
        }
        mock_post.return_value = mock_resp
        rows = _cninfo_direct_api("000958")
        assert len(rows) == 2
        assert rows[0]["title"] == "年报"
        assert rows[0]["type"] == "cninfo 公告"
        assert rows[0]["url"].startswith("http")


def test_cninfo_direct_api_routes_szse_vs_sse():
    """000xxx → szse · 600xxx → sse · 路由正确."""
    from fetch_events import _cninfo_direct_api
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"announcements": []}
        mock_post.return_value = mock_resp

        _cninfo_direct_api("000958")
        assert mock_post.call_args.kwargs["data"]["column"] == "szse"

        _cninfo_direct_api("600406")
        assert mock_post.call_args.kwargs["data"]["column"] == "sse"


# ─── #2 · _cninfo_disclosures fallback gate ──────────────

def test_disclosures_skips_akshare_when_direct_api_fails():
    """直连失败 + 未设 UZI_AK_CNINFO_FALLBACK · 不能掉入 akshare 慢路径."""
    os.environ.pop("UZI_AK_CNINFO_FALLBACK", None)
    from fetch_events import _cninfo_disclosures

    with patch("fetch_events._cninfo_direct_api", return_value=[]):
        with patch("akshare.stock_zh_a_disclosure_report_cninfo") as mock_ak:
            rows = _cninfo_disclosures("000958")
            assert rows == []
            # akshare 必须没被调到（否则又会触发 854 页长尾）
            mock_ak.assert_not_called()


def test_disclosures_uses_direct_api_when_available():
    """直连返非空 · 不调 akshare."""
    from fetch_events import _cninfo_disclosures

    fake_rows = [{"title": "X", "date": "2026-06-01", "type": "cninfo 公告", "url": ""}]
    with patch("fetch_events._cninfo_direct_api", return_value=fake_rows):
        with patch("akshare.stock_zh_a_disclosure_report_cninfo") as mock_ak:
            rows = _cninfo_disclosures("000958")
            assert rows == fake_rows
            mock_ak.assert_not_called()


def test_disclosures_uses_akshare_only_with_explicit_opt_in():
    """显式 UZI_AK_CNINFO_FALLBACK=1 才允许 akshare 慢路径."""
    os.environ["UZI_AK_CNINFO_FALLBACK"] = "1"
    try:
        from fetch_events import _cninfo_disclosures
        with patch("fetch_events._cninfo_direct_api", return_value=[]):
            with patch("akshare.stock_zh_a_disclosure_report_cninfo") as mock_ak:
                mock_df = MagicMock()
                mock_df.empty = True
                mock_ak.return_value = mock_df
                _cninfo_disclosures("000958")
                mock_ak.assert_called_once()
    finally:
        os.environ.pop("UZI_AK_CNINFO_FALLBACK", None)


# ─── #3 · install-hermes.sh Python + pip 探测 ────────────

def test_install_script_checks_python_version():
    body = SCRIPT.read_text(encoding="utf-8")
    assert "python3" in body
    # Python >= 3.10 检查 (akshare 1.14 要求)
    assert "3, 10" in body or "3.10" in body


def test_install_script_pip_cascade_detection():
    """探测顺序：venv → pip → pip3 → python -m pip."""
    body = SCRIPT.read_text(encoding="utf-8")
    # 必须含级联探测
    assert "venv/bin/pip" in body
    assert ".venv/bin/pip" in body
    # pip3 fallback (issue #69 关键)
    assert "pip3" in body
    # python -m pip 兜底
    assert "-m pip" in body


def test_install_script_no_silent_pip_failure():
    """完全找不到 pip 时 · 必须 exit 非 0 + 给清晰提示 · 不能跑下去."""
    body = SCRIPT.read_text(encoding="utf-8")
    # 错误信息必须含可操作建议
    assert "apt install python3-pip" in body or "yum install python3-pip" in body
    # 必须 exit non-zero
    assert "exit 4" in body or "exit 5" in body


def test_install_script_pip_install_failure_gives_actionable_hint():
    """pip install 失败时 · 提示镜像源 / 升级 pip · 不能光说 'failed'."""
    body = SCRIPT.read_text(encoding="utf-8")
    # 镜像源建议
    assert "tuna.tsinghua.edu.cn" in body
    # 升级 pip 建议
    assert "upgrade pip" in body

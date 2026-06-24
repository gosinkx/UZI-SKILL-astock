"""Regression for issue #76 · Hermes 不支持 /analyze-stock slash 命令.

#76 (@oliversegal)：Hermes 里跑 `/analyze-stock 600519.SH` → "Unknown command".
根因：`/analyze-stock` 是 Claude Code 插件命令 (commands/analyze-stock.md)，
Hermes 只注册 SKILL.md skill · 不注册 commands/ · 所以该 slash 命令不存在。
但 install-hermes.sh 的"下一步"和 INSTALL-HERMES.md 都教用户用 /analyze-stock，
误导 Hermes 用户。

修复：Hermes 文档改为教自然语言触发（"分析 600519.SH"），并明确标注
/analyze-stock 是 Claude Code 专属。

测试覆盖：
1. install-hermes.sh "下一步" 不再把 /analyze-stock 当触发命令
2. install-hermes.sh 含自然语言触发指引 + Hermes 不支持 slash 命令的提示
3. INSTALL-HERMES.md 验证/深度章节不再用 /analyze-stock 作触发示例
4. INSTALL-HERMES.md 有 #76 排错条目
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SCRIPT = REPO / "install-hermes.sh"
DOC = REPO / "INSTALL-HERMES.md"


def test_install_script_not_teach_analyze_stock_as_trigger():
    """install-hermes.sh '下一步' 不能再教 /analyze-stock <ticker>."""
    body = SCRIPT.read_text(encoding="utf-8")
    # 不应出现把 /analyze-stock + ticker 当触发命令的行
    assert "/analyze-stock 600519" not in body
    assert "/analyze-stock <ticker>" not in body


def test_install_script_teaches_natural_language():
    body = SCRIPT.read_text(encoding="utf-8")
    # 必须教自然语言触发
    assert "分析 600519" in body or "自然语言" in body
    # 必须提示 Hermes 不支持 /analyze-stock
    assert "Claude Code" in body and "analyze-stock" in body


def test_install_hermes_md_no_slash_command_trigger():
    """INSTALL-HERMES.md 不再用 /analyze-stock 作为触发示例."""
    doc = DOC.read_text(encoding="utf-8")
    for stale in ("/analyze-stock 600519.SH", "/analyze-stock 00700.HK",
                  "/analyze-stock AAPL", "/analyze-stock <ticker>"):
        assert stale not in doc, f"INSTALL-HERMES.md 仍含过时触发示例: {stale}"


def test_install_hermes_md_has_issue76_troubleshooting():
    doc = DOC.read_text(encoding="utf-8")
    assert "Unknown command" in doc
    assert "自然语言" in doc


def test_install_hermes_md_clarifies_slash_is_claude_code_only():
    doc = DOC.read_text(encoding="utf-8")
    # 说明 /analyze-stock 是 Claude Code 专属 · Hermes 不注册 commands/
    assert "Claude Code" in doc
    assert "commands/" in doc or "slash 命令" in doc

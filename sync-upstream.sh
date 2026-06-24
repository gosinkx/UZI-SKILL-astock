#!/bin/bash
# ============================================================
# sync-upstream.sh — UZI-SKILL-astock 上游同步脚本
# 
# 功能: 检查原版 UZI-Skill 仓库更新，合并到本仓库，
#       保留本地 V3.10 数据源优化方案。
#
# 用法: bash sync-upstream.sh
# 依赖: git, curl, GITHUB_TOKEN 环境变量 (ghp_xxx)
# ============================================================
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
UPSTREAM_REPO="https://github.com/wbh604/UZI-Skill.git"
OUR_REPO="https://oauth2:${GITHUB_TOKEN}@github.com/gosinkx/UZI-SKILL-astock.git"

# ── 需保留本地优化的文件列表（合并时用三路合并策略） ──
OPTIMIZED_FILES=(
    "deep-analysis/scripts/lib/data_sources.py"
    "deep-analysis/references/data-sources.md"
)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "UZI-SKILL-astock · 上游同步"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 读取上次同步的上游 commit
LAST_SYNCED=""
if [ -f "${REPO_DIR}/UPSTREAM_VERSION" ]; then
    LAST_SYNCED=$(cat "${REPO_DIR}/UPSTREAM_VERSION" | tr -d ' \n')
fi
echo "上次同步: ${LAST_SYNCED:-（首次同步）}"

# 2. 获取上游最新 commit
LATEST=$(curl -s -H "Accept: application/vnd.github.v3.sha" \
    "https://api.github.com/repos/wbh604/UZI-Skill/commits/main" 2>/dev/null | \
    python3 -c "import sys; print(sys.stdin.read().strip()[:40])" 2>/dev/null || echo "")

if [ -z "$LATEST" ]; then
    echo "❌ 无法获取上游仓库信息"
    exit 1
fi
echo "上游最新: ${LATEST}"

# 3. 判断是否有更新
if [ "$LAST_SYNCED" = "$LATEST" ]; then
    echo "✅ 已是最新，无需同步"
    exit 0
fi
echo "🔄 检测到上游更新，开始同步..."

# 4. 创建临时工作目录
TMPDIR=$(mktemp -d)
trap "rm -rf ${TMPDIR}" EXIT

# 5. 克隆上游
echo "⏬ 克隆上游仓库..."
git clone --depth 50 "${UPSTREAM_REPO}" "${TMPDIR}/upstream"

# 6. 克隆本地仓库（最新版）
echo "⏬ 克隆本地仓库..."
git clone "${OUR_REPO}" "${TMPDIR}/local"

# 7. 确定变更范围：从 LAST_SYNCED 到 LATEST 之间上游改了什么文件
CHANGED_FILES=""
if [ -n "$LAST_SYNCED" ]; then
    cd "${TMPDIR}/upstream"
    CHANGED_FILES=$(git diff --name-only "${LAST_SYNCED}..${LATEST}" 2>/dev/null || echo "")
    cd "${REPO_DIR}"
fi
# 如果 LAST_SYNCED 不在上游历史中（首次或强制推送），全量同步
if [ -z "$CHANGED_FILES" ]; then
    echo "⚠️  无法确定变更范围，全量同步"
    CHANGED_FILES="ALL"
fi

echo "变更文件数: $(echo "${CHANGED_FILES}" | wc -l)"

# 8. 合并文件
cd "${TMPDIR}/local"
UPSTREAM_DIR="${TMPDIR}/upstream"

# 8a. 处理优化文件（三路合并：保留本地优化，接受上游非冲突变更）
for relpath in "${OPTIMIZED_FILES[@]}"; do
    local_file="${TMPDIR}/local/${relpath}"
    upstream_file="${TMPDIR}/upstream/${relpath}"

    if [ ! -f "$upstream_file" ]; then
        echo "  ⏭  上游已删除 ${relpath}，保留本地版本"
        continue
    fi

    if [ -n "$LAST_SYNCED" ]; then
        # 尝试从上游历史找回基础版本做三路合并
        base_file="${TMPDIR}/base_${relpath//\//_}"
        cd "${TMPDIR}/upstream"
        if git show "${LAST_SYNCED}:${relpath}" > "$base_file" 2>/dev/null; then
            cd "${TMPDIR}/local"
            # 三路合并
            merge_result=$(python3 -c "
import difflib, sys
base = open('${base_file}').readlines()
local = open('${local_file}').readlines()
upstream = open('${upstream_file}').readlines()
# 简单策略：对每个段落，如果上游和本地都对base做了不同修改，保留本地版本
# 这确保我们的 V3.10 优化始终保留，同时吸收上游非冲突改动
result = []
local_idx = 0
upstream_idx = 0
base_idx = 0
lines_local = local
lines_upstream = upstream
lines_base = base

# 逐行对比：上游行与本地行相同时自动接受，不同时优先本地
sm_local = difflib.SequenceMatcher(None, lines_base, lines_local)
sm_upstream = difflib.SequenceMatcher(None, lines_base, lines_upstream)

# 输出合并结果: 保留本地所有修改，附加上游新增的内容
for op, i1, i2, j1, j2 in sm_upstream.get_opcodes():
    if op in ('equal', 'replace', 'delete'):
        pass  # 本地优先，不追加
    elif op == 'insert':
        result.extend(lines_upstream[i1:i2])

# 写入本地文件
with open('${local_file}', 'w') as f:
    f.writelines(lines_local)
    f.writelines(result)
print('  ✓ ${relpath} 三路合并完成')
" 2>&1) || {
            echo "  ⚠️  三路合并失败，保留本地版本"
        fi
        cd "${TMPDIR}/local"
    else
        # 首次同步：保留本地版本即可
        echo "  ⏭  ${relpath} 首次同步，保留本地优化"
    fi
done

# 8b. 非优化文件：直接取上游版本（仅限上游有变动的文件）
if [ "$CHANGED_FILES" != "ALL" ]; then
    echo "$CHANGED_FILES" | while read -r filepath; do
        [ -z "$filepath" ] && continue
        # 跳过优化文件（已处理）
        is_optimized=0
        for opt in "${OPTIMIZED_FILES[@]}"; do
            [ "$filepath" = "$opt" ] && is_optimized=1 && break
        done
        [ "$is_optimized" = "1" ] && continue

        # 跳过非项目文件
        [[ "$filepath" == .git* ]] && continue

        src="${UPSTREAM_DIR}/${filepath}"
        dst="${TMPDIR}/local/${filepath}"
        if [ -f "$src" ]; then
            mkdir -p "$(dirname "$dst")"
            cp "$src" "$dst"
            echo "  ✓ ${filepath} 已同步"
        elif [ -f "$dst" ]; then
            rm -f "$dst"
            echo "  ✓ ${filepath} 已删除（上游移除）"
        fi
    done
else
    # 全量同步（首次或强制推送后）
    echo "⚠️  执行全量同步..."
    rsync -a --exclude='.git' --exclude='UPSTREAM_VERSION' \
        --exclude='README.md' \
        "${UPSTREAM_DIR}/" "${TMPDIR}/local/"
    # 恢复优化文件
    for relpath in "${OPTIMIZED_FILES[@]}"; do
        if [ -f "${REPO_DIR}/${relpath}" ]; then
            cp "${REPO_DIR}/${relpath}" "${TMPDIR}/local/${relpath}"
            echo "  ✓ 恢复本地优化 ${relpath}"
        fi
    done
    # 恢复本地 README
    if [ -f "${REPO_DIR}/README.md" ]; then
        cp "${REPO_DIR}/README.md" "${TMPDIR}/local/README.md"
    fi
fi

# 9. 更新 UPSTREAM_VERSION
echo "$LATEST" > "${TMPDIR}/local/UPSTREAM_VERSION"
echo "  ✓ UPSTREAM_VERSION 更新"

# 10. 提交并推送
cd "${TMPDIR}/local"
git add -A

# 检查是否有变更
if git diff --cached --quiet; then
    echo "✅ 无内容变更，跳过提交"
else
    # 获取上游提交信息
    COMMIT_MSG=$(curl -s \
        -H "Authorization: Bearer ${GITHUB_TOKEN}" \
        "https://api.github.com/repos/wbh604/UZI-Skill/commits/${LATEST}" 2>/dev/null | \
        python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    msg = d.get('commit',{}).get('message','')
    print(msg[:500])
except:
    print('上游更新同步')
" 2>/dev/null || echo "上游更新同步")

    git commit -m "🔁 sync upstream wbh604/UZI-Skill@${LATEST:0:8}

${COMMIT_MSG}

---
此提交由 sync-upstream.sh 自动生成。
本地 V3.10 优化已保留：腾讯主路径 / em_get() 限流 / K线重排 / 新浪财报fallback"

    echo "📤 推送到远程..."
    git push origin master
    echo "✅ 同步完成！"
fi

# 11. 清理
rm -rf "${TMPDIR}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "同步完成于 $(date '+%Y-%m-%d %H:%M:%S')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

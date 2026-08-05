#!/usr/bin/env bash
# SF52 pr_creator 任务 setup 脚本
# 在 Dockerfile.task 构建阶段执行（root 权限）
# 职责：
#   1. 验证 Gitea binary 和 gh CLI 已就位（由 Dockerfile.task 的 step 3.3 安装）
#   2. 确保 /opt/gitea/ 权限正确（将由 step 6 的 chown 处理）
#
# 注意：Gitea 数据初始化在容器运行时（entrypoint step 0.5）完成
#       因为 Gitea 1.22+ 禁止以 root 运行

set -euo pipefail

echo "[SF52 setup] 验证 Gitea sidecar 环境..."

if [[ ! -x /opt/gitea/gitea ]]; then
    echo "[SF52 setup] ERROR: /opt/gitea/gitea 不存在，请检查 Dockerfile 构建（step 3.3）"
    exit 1
fi

echo "[SF52 setup] gitea: $(/opt/gitea/gitea --version 2>/dev/null | head -1 || echo 'found')"

if command -v gh >/dev/null 2>&1; then
    echo "[SF52 setup] gh: $(gh --version 2>/dev/null | head -1)"
else
    echo "[SF52 setup] WARN: gh CLI 未找到，请确认 step 3.3 安装成功"
fi

if ! command -v git >/dev/null 2>&1; then
    echo "[SF52 setup] 安装 git..."
    apt-get update -qq && apt-get install -y -q --no-install-recommends git && rm -rf /var/lib/apt/lists/*
fi
echo "[SF52 setup] git: $(git --version)"

# 确保 /opt/gitea/ 目录权限正确（agent 用户将在运行时写入）
chmod -R 755 /opt/gitea/ || true
mkdir -p /opt/gitea/data/log /opt/gitea/data/repositories /opt/gitea/custom/conf

echo "[SF52 setup] 完成. Gitea 将在容器启动时（entrypoint step 0.5）初始化."

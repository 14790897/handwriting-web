#!/usr/bin/env bash
# 冒烟：app.py 要能一直跑到被 timeout 杀掉才算启动正常。
# 提前退出（无论崩溃还是正常退出）都说明后端没在服务，CI 应当失败。
set -euo pipefail

TIMEOUT_SECONDS="${SMOKE_TIMEOUT_SECONDS:-60}"

set +e
timeout "${TIMEOUT_SECONDS}s" python app.py
status=$?
set -e

if [ "$status" -eq 124 ]; then
  echo "app.py 跑满 ${TIMEOUT_SECONDS}s 未退出，启动正常"
  exit 0
fi

echo "app.py 在 ${TIMEOUT_SECONDS}s 内就退出了（退出码 ${status}），后端没有在服务" >&2
exit 1

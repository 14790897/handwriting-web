#!/usr/bin/env bash
# 把桌面版产物挂到指定 Release 上，单个文件失败时退避重试。
#
# 为什么要重试：产物是 200-250 MB 的大文件，而 uploads.github.com 在「上传体
# 持续一段时间没有数据流动」时会直接回 HTTP 408。2026-10-03 的 v1.33.1 就是这么
# 挂的 —— 构建和桌面版 E2E 全绿，只有上传那一步报
#   HTTP 408: Upload body timed out due to inactivity (...HandwritingWeb-1.33.1-arm64.zip)
# 结果 Release 上只剩 Windows 的两个 exe，mac 包一个都没挂上（整个 gh 命令退出非零，
# 连先传的 dmg 也没留下）。
#
# 重试对 --clobber 是安全的：已传成功的同名资产会被覆盖，不会重复挂。
#
# 用法：bash scripts/upload-release-assets.sh <tag> <glob> [<glob>...]
#   bash scripts/upload-release-assets.sh v1.33.1 'desktop/build/installer/*.exe'
#
# 可调（主要给测试用）：UPLOAD_MAX_ATTEMPTS（默认 3）、UPLOAD_RETRY_DELAY（基础秒数，默认 30）
set -euo pipefail
shopt -s nullglob

tag="${1:-}"
if [ -z "$tag" ] || [ "$#" -lt 2 ]; then
  echo "用法: bash scripts/upload-release-assets.sh <tag> <glob> [<glob>...]" >&2
  exit 1
fi
shift

max_attempts="${UPLOAD_MAX_ATTEMPTS:-3}"
base_delay="${UPLOAD_RETRY_DELAY:-30}"

# 展开 glob。没匹配上的模式在 nullglob 下直接消失
files=()
for pattern in "$@"; do
  for file in $pattern; do
    files+=("$file")
  done
done

if [ ${#files[@]} -eq 0 ]; then
  echo "没有匹配到任何产物：$*" >&2
  exit 1
fi

echo "上传到 ${tag}："
printf '  %s\n' "${files[@]}"

# 一个文件一个文件地传：一次传多个时 gh 会整体失败，前面已经传成功的也白传；
# 分开传则每个文件各自重试，互不影响。
for file in "${files[@]}"; do
  attempt=1
  while :; do
    if gh release upload "$tag" "$file" --clobber; then
      echo "OK   $file"
      break
    fi
    if [ "$attempt" -ge "$max_attempts" ]; then
      echo "::error::$file 连续 ${max_attempts} 次上传失败，放弃" >&2
      exit 1
    fi
    delay=$((attempt * base_delay))
    echo "::warning::$file 第 ${attempt} 次上传失败，${delay}s 后重试" >&2
    sleep "$delay"
    attempt=$((attempt + 1))
  done
done

echo "全部产物已上传到 ${tag}"

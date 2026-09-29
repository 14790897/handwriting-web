#!/usr/bin/env bash
# 一键构建 Windows 桌面版。
#
#   bash desktop/build.sh              # 完整构建：前端 dist → 后端 exe → Electron 安装包
#   bash desktop/build.sh --skip-deps  # 跳过 npm ci / pip install（依赖已装好时更快）
#   bash desktop/build.sh --app-only   # 只出 Electron 目录版（不生成 NSIS 安装包）
#
# 产物：
#   desktop/build/backend/handwriting-backend/   后端 onedir（调试可直接跑 exe）
#   desktop/build/installer/                     安装包 / 便携版 exe
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESKTOP="$ROOT/desktop"

SKIP_DEPS=false
APP_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --skip-deps) SKIP_DEPS=true ;;
    --app-only) APP_ONLY=true ;;
    *) echo "未知参数: $arg" >&2; exit 1 ;;
  esac
done

# 优先用仓库根目录的 venv —— 系统 Python 的 fastapi/starlette 版本组合起不来。
# 在 git worktree 里构建时 venv 通常只在主工作区（git worktree list 的第一项），
# 与 e2e/playwright.config.js 的查找顺序保持一致。
find_python() {
  local roots=("$ROOT") main_root
  main_root="$(git -C "$ROOT" worktree list --porcelain 2>/dev/null | awk '/^worktree /{print $2; exit}')"
  if [ -n "$main_root" ] && [ "$main_root" != "$ROOT" ]; then
    roots+=("$main_root")
  fi
  local r
  for r in "${roots[@]}"; do
    if [ -x "$r/venv/Scripts/python.exe" ]; then echo "$r/venv/Scripts/python.exe"; return 0; fi
    if [ -x "$r/venv/bin/python" ]; then echo "$r/venv/bin/python"; return 0; fi
  done
  return 1
}

PYTHON="$(find_python)" || {
  echo "找不到 venv（已查找：$ROOT 及主工作区），请先按 AGENTS.md 在仓库根目录创建 venv 并安装 backend/requirements.txt" >&2
  exit 1
}

echo "==> 使用 Python: $PYTHON"
"$PYTHON" --version

if [ "$SKIP_DEPS" = false ]; then
  echo "==> 安装打包依赖"
  "$PYTHON" -m pip install --disable-pip-version-check -q -r "$DESKTOP/requirements-build.txt"
fi

echo "==> 构建前端"
cd "$ROOT/frontend"
if [ ! -d node_modules ] && [ "$SKIP_DEPS" = false ]; then
  npm ci --no-audit --no-fund
fi
npm run build

echo "==> 打包后端 (PyInstaller onedir)"
cd "$ROOT"
"$PYTHON" -m PyInstaller "$DESKTOP/backend.spec" \
  --noconfirm \
  --distpath "$DESKTOP/build/backend" \
  --workpath "$DESKTOP/build/pyinstaller-work"

echo "==> 生成应用图标"
# electron-builder 要求 Windows 图标 ≥256x256，仓库里的 logo.png 只有 200x200
"$PYTHON" - "$ROOT/logo.png" "$DESKTOP/build/icon.ico" <<'PY'
import sys
from PIL import Image

source, target = sys.argv[1], sys.argv[2]
base = Image.open(source).convert("RGBA").resize((256, 256), Image.LANCZOS)
base.save(target, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f"图标已写入 {target}")
PY

echo "==> 打包 Electron 应用"
cd "$DESKTOP"
if [ ! -d node_modules ]; then
  npm install --no-audit --no-fund
fi
if [ "$APP_ONLY" = true ]; then
  npm run pack
else
  npm run dist
fi

echo
echo "完成。产物："
ls -la "$DESKTOP/build/installer" 2>/dev/null || echo "  $DESKTOP/build/backend/handwriting-backend/"

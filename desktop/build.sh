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

# Windows runner 的控制台代码页不是 UTF-8（英文 runner 是 cp1252），Python 往 stdout
# 打中文会抛 UnicodeEncodeError —— 2026-09-29 的 Desktop Release Assets 就是栽在
# 生成图标那步的一句中文 print 上。统一让本次构建里的所有 Python（图标脚本、
# PyInstaller、spec 里的校验报错）都走 UTF-8，避免同一类问题再冒出来。
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

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

# 优先用 PYTHON 指定的解释器（CI 上没有 venv），否则找仓库根目录的 venv ——
# 系统 Python 的 fastapi/starlette 版本组合起不来。
# 在 git worktree 里构建时 venv 通常只在主工作区（git worktree list 的第一项），
# 与 e2e/playwright.config.js 的查找顺序保持一致。
find_python() {
  if [ -n "${PYTHON:-}" ]; then
    echo "$PYTHON"
    return 0
  fi
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
  echo "找不到 venv（已查找：$ROOT 及主工作区），请先按 AGENTS.md 在仓库根目录创建 venv 并安装 backend/requirements.txt，或用 PYTHON=<解释器> 指定" >&2
  exit 1
}

# --skip-deps 对前端和 desktop 一视同仁；有 lockfile 时用 npm ci 保证可复现
ensure_node_deps() {
  local dir="$1"
  if [ -d "$dir/node_modules" ]; then
    return 0
  fi
  if [ "$SKIP_DEPS" = true ]; then
    echo "!! $dir/node_modules 不存在，但已指定 --skip-deps，跳过安装" >&2
    return 0
  fi
  echo "==> 安装 $dir 的 npm 依赖"
  if [ -f "$dir/package-lock.json" ]; then
    (cd "$dir" && npm ci --no-audit --no-fund)
  else
    (cd "$dir" && npm install --no-audit --no-fund)
  fi
}

echo "==> 使用 Python: $PYTHON"
"$PYTHON" --version

if [ "$SKIP_DEPS" = false ]; then
  echo "==> 安装打包依赖"
  "$PYTHON" -m pip install --disable-pip-version-check -q -r "$DESKTOP/requirements-build.txt"
fi

echo "==> 构建前端"
ensure_node_deps "$ROOT/frontend"
cd "$ROOT/frontend"
npm run build

echo "==> 打包后端 (PyInstaller onedir)"
cd "$ROOT"
"$PYTHON" -m PyInstaller "$DESKTOP/backend.spec" \
  --noconfirm \
  --distpath "$DESKTOP/build/backend" \
  --workpath "$DESKTOP/build/pyinstaller-work"

echo "==> 生成应用图标"
# 图标源必须是站点自己的图标（frontend/public 里 PWA 用的那张 512x512）。
# 2026-10-03 修：之前用的是仓库根的 logo.png —— 那是旧的 Vue 风格 V，和网站图标
# 根本不是一回事，桌面版装出来图标是错的。
# 站点自带的 favicon.ico 最大只有 48x48，而 electron-builder 要求 Windows 图标
# ≥256x256，所以这里自己合成多尺寸。
ICON_SRC="$ROOT/frontend/public/web-app-manifest-512x512.png"
if [ ! -f "$ICON_SRC" ]; then
  echo "找不到站点图标 $ICON_SRC，无法生成应用图标" >&2
  exit 1
fi
"$PYTHON" - "$ICON_SRC" "$DESKTOP/build/icon.ico" <<'PY'
import sys
from PIL import Image

source, target = sys.argv[1], sys.argv[2]
base = Image.open(source).convert("RGBA").resize((256, 256), Image.LANCZOS)
base.save(target, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
# 这里刻意用 ASCII：上面的 PYTHONIOENCODING 已经兜住了，但这一步没有理由让
# 构建栽在一条日志上（CI 上一版就是死在这句的中文上）
print("icon written to %s" % target)
PY

echo "==> 打包 Electron 应用"
ensure_node_deps "$DESKTOP"
cd "$DESKTOP"
if [ "$APP_ONLY" = true ]; then
  npm run pack
else
  npm run dist
fi

echo
echo "完成。产物："
ls -la "$DESKTOP/build/installer" 2>/dev/null || echo "  $DESKTOP/build/backend/handwriting-backend/"

#!/usr/bin/env bash
# 一键构建桌面版（按当前平台出 Windows 或 macOS 包）。
#
#   bash desktop/build.sh              # 完整构建：前端 dist → 后端可执行文件 → 桌面安装包
#   bash desktop/build.sh --skip-deps  # 跳过 npm ci / pip install（依赖已装好时更快）
#   bash desktop/build.sh --app-only   # 只出 Electron 目录版（不生成 NSIS / DMG）
#
# 产物：
#   desktop/build/backend/handwriting-backend/      后端 onedir（调试可直接跑里面的可执行文件）
#   desktop/build/installer/                        安装包 / 便携版 / .app
#
# 注意：PyInstaller 不能交叉编译，后端的架构由构建机的架构决定，所以 macOS 包只能
# 在对应架构的 mac 上出（CI 里是 macos-14，arm64）。
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
# ≥256x256，所以这里自己合成多尺寸。macOS 的 .icns 同样从这张 512 合成。
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

# .icns：只有 macOS 需要，也只在 macOS 上生成得出来 —— Pillow 的 ICNS 写出仅限
# darwin，且 iconutil 是系统自带的。非 macOS 上直接跳过（那个平台也构建不了 mac 目标）。
if [ "$(uname -s)" = "Darwin" ]; then
  ICONSET="$DESKTOP/build/icon.iconset"
  rm -rf "$ICONSET"
  "$PYTHON" - "$ICON_SRC" "$ICONSET" <<'PY'
import os
import sys

from PIL import Image

source, iconset = sys.argv[1], sys.argv[2]
os.makedirs(iconset, exist_ok=True)
base = Image.open(source).convert("RGBA")
# iconutil 只认这套固定文件名：icon_<n>x<n>.png 是 1x，@2x 是两倍像素的那张。
# 源图只有 512，所以 512x512@2x（1024px）是放大出来的 —— 除了「显示简介」那种
# 极端场景用不到，留着只为凑齐 iconutil 期望的完整图标集。
for size in (16, 32, 128, 256, 512):
    for scale, suffix in ((1, ""), (2, "@2x")):
        pixels = size * scale
        base.resize((pixels, pixels), Image.LANCZOS).save(
            os.path.join(iconset, "icon_%dx%d%s.png" % (size, size, suffix))
        )
print("iconset written to %s" % iconset)
PY
  iconutil -c icns "$ICONSET" -o "$DESKTOP/build/icon.icns"
  rm -rf "$ICONSET"
fi

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

# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：把 FastAPI 后端 + 前端构建产物 + 字体打成 onedir 目录。

构建：bash desktop/build.sh   （等价于 pyinstaller desktop/backend.spec --noconfirm）
产物：desktop/build/backend/handwriting-backend/
"""

from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIST = ROOT / "frontend" / "dist"

if not (FRONTEND_DIST / "index.html").is_file():
    raise SystemExit("缺少 frontend/dist/index.html，请先在 frontend/ 执行 npm run build")

# ── 校验 handright 的发行包属主 ──────────────────────────────────────
# PyPI 上 handright（上游原版）与本项目用的 handrightbeta 模块名相同，都装进
# site-packages/handright/；两个都在时会互相覆盖成一个杂交目录，渲染效果静默改变。
# 而下面的 hiddenimports 只写模块名、不区分发行包 —— 装错了照样能构建成功，
# 所以必须在构建期挡住。
import importlib.metadata as metadata

import handright

_owners = sorted(metadata.packages_distributions().get("handright", []))
if _owners != ["handrightbeta"]:
    raise SystemExit(
        "handright 的发行包属主应为且仅为 handrightbeta，实际为 %r。\n"
        "PyPI 上的 handright 是上游原版，与本项目用的 fork 模块名相同，"
        "装错会静默改变手写渲染效果。清理后重装：\n"
        "  pip uninstall -y handright handrightbeta && pip install -r backend/requirements.txt"
        % (_owners,)
    )

_dist_root = Path(metadata.distribution("handrightbeta").locate_file("")).resolve()
_resolved = Path(handright.__file__).resolve()
if not _resolved.is_relative_to(_dist_root):
    raise SystemExit(
        "import handright 解析到 %s，不在 handrightbeta 的安装目录 %s 下，"
        "多半是仓库或 sys.path 上有同名模块抢先。" % (_resolved, _dist_root)
    )

# 随包分发的只读资源：字体（同步到用户可写目录）、前端静态文件、版本号
datas = [
    (str(BACKEND_DIR / "font_assets"), "font_assets"),
    (str(FRONTEND_DIST), "dist"),
]
# app.py 读 __file__ 同级目录下的 VERSION 作为版本号兜底（桌面版通常走 Electron 传的环境变量）
if (BACKEND_DIR / "VERSION").is_file():
    datas.append((str(BACKEND_DIR / "VERSION"), "."))

hiddenimports = [
    # 发行名是 handrightbeta，但 import 名是 handright
    "handright",
    # uvicorn 默认按字符串动态解析这些实现，静态分析看不到
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.loops.asyncio",
    "uvicorn.lifespan.on",
    # limits 用 __import__ 按名字找存储/策略实现
    "limits.storage",
    "limits.strategies",
    "slowapi",
    "slowapi.extension",
    "slowapi.middleware",
    # 本地模块（identify 在导入期拉起 cv2/sklearn）
    "identify",
    "pdf",
    "task_store",
    "task_types",
    "schedule_clean",
]

excludes = [
    "tkinter",
    "matplotlib",
    "pytest",
    "IPython",
    "notebook",
    "pandas",
    "PyQt5",
    "PySide2",
    "PySide6",
    "setuptools._distutils",
]

a = Analysis(
    [str(BACKEND_DIR / "desktop_main.py")],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="handwriting-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # Electron 要读 stdout 里的端口握手，窗口由 windowsHide 隐藏
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="handwriting-backend",
)

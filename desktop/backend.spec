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

# 随包分发的只读资源：字体（同步到用户可写目录）与前端静态文件
datas = [
    (str(BACKEND_DIR / "font_assets"), "font_assets"),
    (str(FRONTEND_DIST), "dist"),
]

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

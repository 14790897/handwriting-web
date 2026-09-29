"""桌面版（Electron + PyInstaller）后端入口。

与 `python app.py` 的区别：
1. 数据目录不在包内 —— 打包后 `__file__` 落在只读的安装目录（onedir）
   或退出即删的临时目录（onefile），因此把 tasks.db / temp / logs / font_assets
   统一切到可写目录，并在导入 app 之前用环境变量告知。
2. 只监听 127.0.0.1 的随机空闲端口，启动后把端口打到 stdout 供 Electron 解析。
3. 关闭上报到线上项目的 Sentry、跳过 pandoc 自动下载、放开 CPU 占用守卫
   （桌面机上用户随时可能跑满 CPU，默认 90% 的阈值会误报 429）。

用法（开发）：
    cd backend && python desktop_main.py
"""

import json
import os
import socket
import sys
import threading
import time

import psutil

# onefile 打包下子进程会重复执行入口，必须先冻结支持
import multiprocessing

multiprocessing.freeze_support()

from pathlib import Path

APP_NAME = "HandwritingWeb"


def bundle_dir() -> Path:
    """随包分发的只读资源目录（font_assets、dist）。"""
    if getattr(sys, "frozen", False):
        # PyInstaller 6.x onedir：_MEIPASS 指向 <app>/_internal
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    """可写的用户数据目录。Electron 通过 HANDWRITING_DATA_DIR 指定，独立运行时回退到 LOCALAPPDATA。"""
    override = os.getenv("HANDWRITING_DATA_DIR")
    if override:
        return Path(override)
    base = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
    return Path(base) / APP_NAME


def bind_listener(preferred: int = 57610) -> socket.socket:
    """绑定并 listen 127.0.0.1 上的一个端口，返回已就绪的 socket。

    只绑一次、把 socket 直接交给 uvicorn：如果先探测再关闭、让 uvicorn 自己 bind，
    两次绑定之间端口可能被别人抢走，uvicorn 会 bind 失败直接退出。
    不设 SO_REUSEADDR —— Windows 上它会允许别的进程抢占同一端口。
    """
    for port in list(range(preferred, preferred + 100)) + [0]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            sock.close()
            continue
        sock.listen(128)
        return sock
    raise RuntimeError(f"{preferred}-{preferred + 99} 内没有可用端口")


def prepare_environment() -> Path:
    """建好目录、设好环境变量，必须在 import app 之前调用。"""
    bundle = bundle_dir()
    data = data_dir()
    data.mkdir(parents=True, exist_ok=True)

    # app.py 用相对路径写这些目录，chdir 之后全部落到数据目录
    for name in ("temp", "logs", "output", "textfileprocess", "imagefileprocess", "font_assets"):
        (data / name).mkdir(parents=True, exist_ok=True)
    os.chdir(data)

    dist = bundle / "dist"
    os.environ.setdefault("HANDWRITING_DATA_DIR", str(data))
    os.environ.setdefault("FONT_ASSETS_BUNDLED_DIR", str(bundle / "font_assets"))
    os.environ.setdefault("FONT_ASSETS_DIR", str(data / "font_assets"))
    os.environ.setdefault("LOG_DIR", str(data / "logs"))
    os.environ.setdefault("HANDWRITING_DIST_DIR", str(dist) if dist.is_dir() else "")
    os.environ.setdefault("DESKTOP_MODE", "true")
    # 关掉上报到上游项目的 Sentry（空串即不初始化）
    os.environ.setdefault("SENTRY_DSN", "")
    # 桌面机上 CPU 常年高占用，默认 90% 阈值会导致随机 429
    os.environ.setdefault("CPU_USAGE_LIMIT", "100")
    return data


def watch_parent(parent_pid: int):
    """父进程（Electron）退出后自杀，避免留下孤儿后端。

    注意：不要改成读 stdin 判断父进程存活。在 Windows 的无控制台 frozen 进程里
    阻塞读 stdin 会让整个进程卡死在启动阶段（实测：app 永远起不来、无任何输出）。
    """
    try:
        expected_create_time = psutil.Process(parent_pid).create_time()
    except psutil.Error:
        return

    while True:
        time.sleep(3)
        try:
            if psutil.Process(parent_pid).create_time() != expected_create_time:
                os._exit(0)  # PID 已被复用，说明原父进程早已退出
        except psutil.Error:
            os._exit(0)


def start_parent_watchdog():
    parent_pid = os.getenv("HANDWRITING_PARENT_PID", "")
    if not parent_pid.isdigit():
        return
    threading.Thread(target=watch_parent, args=(int(parent_pid),), daemon=True).start()


def emit_ready(port: int):
    payload = json.dumps({"type": "ready", "port": port}, ensure_ascii=False)
    sys.stdout.write(f"HANDWRITING_BACKEND {payload}\n")
    sys.stdout.flush()


def main():
    # 打包后 stdout/stderr 是管道或重定向文件，Windows 默认按 ANSI 代码页编码，
    # 中文日志会抛 UnicodeEncodeError（后台线程里就等于静默失败）。Electron 会传
    # PYTHONUTF8，这里再兜一层，保证直接双击 exe 时也不会崩。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    prepare_environment()

    # 先真正把端口绑好、再 import app：app.py 要在导入期用它配 CORS 白名单，
    # 而且只绑这一次、把 socket 交给 uvicorn，避免「探测 → 关闭 → 再绑定」
    # 中间被别的进程抢走端口
    listener = bind_listener()
    port = listener.getsockname()[1]
    os.environ["HANDWRITING_ALLOWED_ORIGIN"] = f"http://127.0.0.1:{port}"

    # 导入放在环境变量就绪之后：app.py 在导入期读取这些配置并建目录
    import uvicorn

    from app import app, cleanup_marked_directories

    cleanup_marked_directories()

    # 此时 socket 已在 listen，报给 Electron 的端口一定可用
    emit_ready(port)

    # 放到导入完成之后启动：万一创建线程与 frozen 导入存在交互，也不该拖住启动
    start_parent_watchdog()

    # 明确指定 loop/http/ws 实现，避免 uvicorn 运行时按字符串动态导入，
    # PyInstaller 的静态分析看不到那些模块。
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        loop="asyncio",
        http="h11",
        ws="websockets",
        log_level="info",
        access_log=False,
    )
    uvicorn.Server(config).run(sockets=[listener])


if __name__ == "__main__":
    main()

import base64
import time
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, Form, File, UploadFile, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response, StreamingResponse
from typing import Union, Optional, Any
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from handright import Template, handwrite
# from threading import Thread
from PIL import Image, ImageFont, ImageDraw
from dotenv import load_dotenv
import psutil

load_dotenv()
import os
import gc

import io
import logging
from datetime import timedelta
from werkzeug.utils import secure_filename
from threading import Lock
from uuid import uuid4

# 文件模块
from docx import Document
import PyPDF2
import tempfile
import shutil
from pdf import generate_pdf

# 图片处理模块
from identify import identify_distance


# 安全文件删除函数
def safe_remove_directory(directory_path, max_retries=5):
    """安全删除目录，带重试机制和更强的文件处理"""
    if not os.path.exists(directory_path):
        return True

    for attempt in range(max_retries):
        try:
            # 强制垃圾回收，释放可能的文件句柄
            gc.collect()
            # 等待更长时间让系统释放文件句柄
            time.sleep(0.2 * (attempt + 1))  # 递增等待时间

            # 递归删除所有文件和子目录
            deleted_files = []
            failed_files = []

            for root, dirs, files in os.walk(directory_path, topdown=False):
                # 删除文件
                for file in files:
                    file_path = os.path.join(root, file)
                    if safe_remove_single_file(file_path, max_retries=2):
                        deleted_files.append(file_path)
                    else:
                        failed_files.append(file_path)

                # 删除空目录
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    try:
                        if os.path.exists(dir_path) and not os.listdir(dir_path):
                            os.rmdir(dir_path)
                    except Exception as dir_e:
                        logger.warning(
                            f"Failed to delete subdirectory {dir_path}: {dir_e}"
                        )

            # 如果有文件删除失败，记录但继续尝试删除目录
            if failed_files:
                logger.warning(
                    f"Failed to delete {len(failed_files)} files: {failed_files[:3]}..."
                )

            # 最后尝试删除根目录
            if os.path.exists(directory_path):
                try:
                    os.rmdir(directory_path)
                    logger.info(
                        f"Successfully deleted temp directory: {directory_path}"
                    )
                    return True
                except OSError as e:
                    if e.errno == 145:  # 目录不为空
                        # 列出剩余文件
                        remaining_files = []
                        try:
                            for root, dirs, files in os.walk(directory_path):
                                remaining_files.extend(
                                    [os.path.join(root, f) for f in files]
                                )
                        except:
                            pass
                        logger.warning(
                            f"Directory not empty, remaining files: {remaining_files[:5]}"
                        )
                    raise

        except Exception as e:
            logger.warning(
                f"Attempt {attempt + 1} to delete {directory_path} failed: {e}"
            )
            if attempt < max_retries - 1:
                time.sleep(1.0 * (attempt + 1))  # 递增等待时间
            else:
                logger.error(
                    f"Failed to delete temp directory after {max_retries} attempts: {directory_path}"
                )
                # 最后尝试：标记目录为稍后清理
                try:
                    cleanup_marker = os.path.join(directory_path, ".cleanup_later")
                    with open(cleanup_marker, "w") as f:
                        f.write(f"Failed to delete at {time.time()}")
                    logger.info(f"Marked directory for later cleanup: {directory_path}")
                except:
                    pass
    return False


def safe_remove_single_file(file_path, max_retries=3):
    """安全删除单个文件"""
    if not os.path.exists(file_path):
        return True

    for attempt in range(max_retries):
        try:
            # 确保文件不是只读
            os.chmod(file_path, 0o777)

            # 强制垃圾回收
            gc.collect()
            time.sleep(0.1)

            # 尝试删除文件
            os.remove(file_path)
            return True

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.3 * (attempt + 1))
            else:
                logger.warning(f"Failed to delete file {file_path}: {e}")
    return False


def safe_remove_file(file_path, max_retries=3):
    """安全删除文件，带重试机制"""
    result = safe_remove_single_file(file_path, max_retries)
    if result:
        logger.info(f"Successfully deleted file: {file_path}")
    else:
        logger.error(f"Failed to delete file after {max_retries} attempts: {file_path}")
    return result


def safe_save_and_close_image(image, image_path):
    """安全保存并关闭图片，确保文件句柄被释放"""
    try:
        # 保存图片
        image.save(image_path)

        # 如果图片对象有 close 方法，调用它
        # if hasattr(image, "close"):
        #     image.close()

        # # 强制垃圾回收
        # gc.collect()

        # # 等待一小段时间确保文件句柄被释放
        # time.sleep(0.1)

        return True
    except Exception as e:
        logger.error(f"Failed to save image {image_path}: {e}")
        return False


def cleanup_marked_directories():
    """清理项目内标记为稍后清理的目录"""
    project_temp_base = "./temp"

    # 确保项目临时目录存在
    os.makedirs(project_temp_base, exist_ok=True)

    try:
        for item in os.listdir(project_temp_base):
            item_path = os.path.join(project_temp_base, item)
            if os.path.isdir(item_path) and item.startswith("tmp"):
                cleanup_marker = os.path.join(item_path, ".cleanup_later")
                if os.path.exists(cleanup_marker):
                    try:
                        # 检查标记时间，如果超过1小时则尝试清理
                        with open(cleanup_marker, "r") as f:
                            content = f.read()
                            if "Failed to delete at" in content:
                                timestamp = float(
                                    content.split("Failed to delete at ")[1]
                                )
                                if time.time() - timestamp > 3600:  # 1小时后
                                    logger.info(
                                        f"Attempting to cleanup marked directory: {item_path}"
                                    )
                                    if safe_remove_directory(item_path, max_retries=2):
                                        logger.info(
                                            f"Successfully cleaned up marked directory: {item_path}"
                                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to cleanup marked directory {item_path}: {e}"
                        )
    except Exception as e:
        logger.warning(f"Error during cleanup of marked directories: {e}")


# sentry 错误报告7.7
import sentry_sdk
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration

# 限制请求速率 7.9
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 装饰器 7.15
from functools import wraps
from task_types import (
    GenerationTask,
    GenerateHandwritingParams,
    form_dependency_from_model,
)
from task_store import (
    set_task as set_generation_task,
    get_task as get_generation_task,
    pop_task as pop_generation_task,
    cleanup_expired as cleanup_expired_generation_tasks,
    get_queue_metrics as get_generation_queue_metrics,
    get_active_task_count as get_generation_active_task_count,
    read_result_file,
    generation_task_ttl_seconds,
)

# 定时清理文件 10.28
import schedule_clean

# 获取环境变量
mysql_host = os.getenv("MYSQL_HOST", "db")
enable_user_auth = os.getenv("ENABLE_USER_AUTH", "false")
# 获取当前路径
current_path = os.getcwd()
# 创建一个子文件夹用于存储输出的图片
output_path = os.path.join(current_path, "output")
# 如果子文件夹不存在，就创建它
if not os.path.exists(output_path):
    os.makedirs(output_path)
directory = ["./textfileprocess", "imagefileprocess"]
for directory in directory:
    if not os.path.exists(directory):
        os.makedirs(directory)

font_assets_dir = os.getenv("FONT_ASSETS_DIR", "./font_assets")
font_assets_bundled_dir = os.getenv("FONT_ASSETS_BUNDLED_DIR", "./font_assets")

def sync_font_assets(source_dir, target_dir):
    if os.path.abspath(source_dir) == os.path.abspath(target_dir):
        return
    if not os.path.isdir(source_dir) or not os.path.isdir(target_dir):
        return
    for filename in os.listdir(source_dir):
        if not filename.lower().endswith(".ttf"):
            continue
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)
        if os.path.isfile(source_path) and not os.path.exists(target_path):
            shutil.copy2(source_path, target_path)

os.makedirs(font_assets_dir, exist_ok=True)
sync_font_assets(font_assets_bundled_dir, font_assets_dir)

font_file_names = [
    f
    for f in os.listdir(font_assets_dir)
    if os.path.isfile(os.path.join(font_assets_dir, f)) and f.endswith(".ttf")
]
# sentry部分 7.7
sentry_sdk.init(
    dsn="https://ed22d5c0e3584faeb4ae0f67d19f68aa@o4505255803551744.ingest.sentry.io/4505485583253504",
    integrations=[
        StarletteIntegration(middleware_type="asgi"),
        FastApiIntegration(),
    ],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)

# 启动计划任务线程, 定时清理
schedule_clean.start_schedule_thread()

# 创建一个logger
logger = logging.getLogger(__name__)

# 设置日志级别
logger.setLevel(logging.DEBUG)

# 创建 console handler，并设置级别为 DEBUG
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# 创建 file handler，并设置级别为 DEBUG
fh = logging.FileHandler("logs/app.log")
fh.setLevel(logging.DEBUG)

# 创建 formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 把 formatter 添加到 ch 和 fh
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# 把 ch 和 fh 添加到 logger
logger.addHandler(ch)
logger.addHandler(fh)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置Flask app的logger级别
# app.logger.setLevel(logging.DEBUG)


SECRET_KEY = "437d75c5af744b76607fe862cf8a5a368519aca486d62c5fa69ba42c16809z88"
# app.config["SECRET_KEY"] = SECRET_KEY
# app.config["SESSION_COOKIE_SECURE"] = True
# app.config["SESSION_COOKIE_SAMESITE"] = "None"
# app.config["MAX_CONTENT_LENGTH"] = 128 * 1024 * 1024
# app.permanent_session_lifetime = timedelta(minutes=5000000)
# app.config["SESSION_TYPE"] = "filesystem"  # 设置session存储方式为文件
# Session(app)  # 初始化扩展，传入应用程序实例
limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per 5 minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# 创建一个新的白色图片，并添加间隔的线条作为背景
def create_notebook_image(
    width,
    height,
    line_spacing,
    top_margin,
    bottom_margin,
    left_margin,
    right_margin,
    font_size,
    isUnderlined,
):
    image = Image.new("RGB", (width, height), "white")

    if isUnderlined == "true":
        draw = ImageDraw.Draw(image)
        # todo  这个距离的原理不清楚7.15
        y = top_margin + line_spacing  # 开始的y坐标设为顶部边距加字体大小
        # bottom_margin -= line_spacing
        while (
            y < height - bottom_margin
        ):  # 当y坐标小于（图片高度-底部边距）时，继续画线
            draw.line((left_margin, y, width - right_margin, y), fill="black")
            y += line_spacing  # 每次循环，y坐标增加行间距
        # draw.line((left_margin, y, width - right_margin, y), fill="black")
    return image


def read_docx(file_path):
    document = Document(file_path)
    text = " ".join([paragraph.text for paragraph in document.paragraphs])
    return text


import pypandoc
try:
    # 1. 尝试获取 Pandoc 版本
    # 如果系统里已经安装了（比如你在 Dockerfile 里用 apt-get 装了），这里会成功
    version = pypandoc.get_pandoc_version()
    print(f"Pandoc found: {version}")

except OSError:
    # 2. 如果报错说找不到，说明没装，开始自动下载
    print("Pandoc not found. Downloading...")
    pypandoc.download_pandoc()
    print("Pandoc downloaded successfully.")

def convert_docx_to_text(docx_file_path):
    # 转换文件为纯文本格式，并返回转换后的文本内容
    text = pypandoc.convert_file(docx_file_path, 'plain')
    return text
    # return None


def read_pdf(file_path):
    text = ""
    with open(file_path, "rb") as pdf_file_obj:
        pdf_reader = PyPDF2.PdfReader(pdf_file_obj)
        for page_num in range(len(pdf_reader.pages)):
            page_obj = pdf_reader.pages[page_num]
            text += page_obj.extract_text()
    return text


def handle_exceptions(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except Exception as e:
            logger.info("An error occurred during the request: %s", e)
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    return decorated_function


# WebSocket 推送（仍需内存存储，仅同进程有效）
task_websocket_connections: dict[str, set[WebSocket]] = {}
task_websocket_connections_lock = asyncio.Lock()

# 同时执行的上限——控制 generate_handwriting_impl 的真正并发数
# 超出部分在 semaphore 处排队等待，避免 CPU 密集任务互相挤占
MAX_CONCURRENT_EXECUTIONS = 2
_generation_semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXECUTIONS)


def build_task_status_payload(
    task_id: str, task: Optional[GenerationTask] = None
) -> Optional[dict[str, Any]]:
    if task is None:
        task = get_generation_task(task_id)
    if task is None:
        return None
    queue_metrics = get_generation_queue_metrics(task_id)
    return {
        "status": "success",
        "task_id": task_id,
        "task_status": task.get("status"),
        "task_stage": task.get("stage"),
        "task_message": task.get("message"),
        "task_progress": task.get("progress"),
        "created_at": task.get("created_at"),
        "updated_at": task.get("updated_at"),
        "error_message": task.get("error_message"),
        "queue_pending_count": queue_metrics.get("queue_pending_count"),
        "queue_ahead_count": queue_metrics.get("queue_ahead_count"),
        "processing_count": queue_metrics.get("processing_count"),
        "active_task_count": queue_metrics.get("active_task_count"),
    }


async def register_task_websocket(task_id, websocket):
    async with task_websocket_connections_lock:
        if task_id not in task_websocket_connections:
            task_websocket_connections[task_id] = set()
        task_websocket_connections[task_id].add(websocket)


async def unregister_task_websocket(task_id, websocket):
    async with task_websocket_connections_lock:
        sockets = task_websocket_connections.get(task_id)
        if sockets is None:
            return
        sockets.discard(websocket)
        if len(sockets) == 0:
            task_websocket_connections.pop(task_id, None)


async def push_task_status_update(task_id):
    task = get_generation_task(task_id)
    if task is None:
        return
    payload = build_task_status_payload(task_id, task=task)
    if payload is None:
        return
    async with task_websocket_connections_lock:
        sockets = list(task_websocket_connections.get(task_id, set()))
    if len(sockets) == 0:
        return

    dead_sockets = []
    for socket in sockets:
        try:
            await socket.send_json(payload)
        except Exception:
            dead_sockets.append(socket)

    if dead_sockets:
        async with task_websocket_connections_lock:
            current_sockets = task_websocket_connections.get(task_id, set())
            for socket in dead_sockets:
                current_sockets.discard(socket)
            if len(current_sockets) == 0 and task_id in task_websocket_connections:
                task_websocket_connections.pop(task_id, None)












def model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)


async def generate_handwriting_impl(
    base_url: str,
    params: GenerateHandwritingParams,
    background_image: Union[UploadFile, str, bytes] = File(None),
    font_file: Union[UploadFile, str, bytes] = File(None),
    progress_hook=None,
):
    def report_progress(stage, message, progress):
        if progress_hook is not None:
            progress_hook(stage=stage, message=message, progress=progress)

    report_progress("validating", "正在校验参数", 5)
    # 归一化：前端可能发字符串 "null"，需要转成 Python None
    if isinstance(background_image, str):
        background_image = None
    if isinstance(font_file, str):
        font_file = None
    # 把所有 form 字段收拢成 data dict，方便后续代码不大改
    data = model_to_dict(params)

    report_progress("system_check", "正在检查服务器负载", 10)
    cpu_usage = psutil.cpu_percent(interval=1)  # 获取 CPU 使用率，1 秒采样间隔
    if cpu_usage > 90:
        # 如果 CPU 使用率超过 90%，返回提醒
        return JSONResponse(
            {
                "status": "waiting",
                "message": f"CPU usage is too high. Please wait and try again. current cpu_usage: {cpu_usage}%",
            },
            status_code=429,
        )  # HTTP 429: Too Many Requests
    # logger.info("已经进入generate_handwriting")
    if enable_user_auth.lower() == "true":
        # session auth 已移除，如需恢复请使用 JWT 或 cookie
        pass
    # try:
    # 先获取 form 数据
    if len(data["text"]) > 10000 and (
        base_url == "https://handwrite.14790897.xyz/"
        or base_url == "https://handwrite.sixiangjia.de/"
    ):
        # 请自己构建应用来运行而不是使用这个网页
        return JSONResponse(
            {
                "status": "error",
                "message": "The text is too long to process. If you want to use this service, please build your own application.",
            },
            status_code=500,
        )
    required_form_fields = [
        "text",
        "font_size",
        "line_spacing",
        "fill",
        "left_margin",
        "top_margin",
        "right_margin",
        "bottom_margin",
        "word_spacing",
        "line_spacing_sigma",
        "font_size_sigma",
        "word_spacing_sigma",
        "perturb_x_sigma",
        "perturb_y_sigma",
        "perturb_theta_sigma",
        "preview",
    ]
    # "height","width",

    for field in required_form_fields:
        if field not in data:
            return JSONResponse(
                {
                    "status": "fail",
                    "message": f"Missing required field: {field}",
                },
                status_code=400,
            )
        else:
            logger.info(f"{field}: {data[field]}")  # 打印具体的 form 字段值
            # 如果存在height和width，就创建一个新的背景图     todo
            # height=int(data["height"]),
            # width=int(data["width"]),

    # 如果用户提供了宽度和高度，创建一个新的笔记本背景图像
    if "width" in data and "height" in data:
        report_progress("prepare_background", "正在创建背景图", 20)
        line_spacing = int(data.get("line_spacing", 30))
        top_margin = int(data.get("top_margin", 0))
        bottom_margin = int(data.get("bottom_margin", 0))
        left_margin = int(data.get("left_margin", 0))
        right_margin = int(data.get("right_margin", 0))
        width = int(data["width"])
        height = int(data["height"])
        font_size = int(data.get("font_size", 0))
        isUnderlined = data.get("isUnderlined", False)
        background_image_obj = create_notebook_image(
            width,
            height,
            line_spacing,
            top_margin,
            bottom_margin,
            left_margin,
            right_margin,
            font_size,
            isUnderlined,
        )

    else:
        # 否则使用用户上传的背景图像
        report_progress("prepare_background", "正在读取背景图", 20)
        if background_image is None:
            return JSONResponse(
                {
                    "status": "fail",
                    "message": "Missing required field: background_image",
                },
                status_code=400,
            )
        if isinstance(background_image, (bytes, bytearray)):
            image_data = io.BytesIO(background_image)
        else:
            image_data = io.BytesIO(await background_image.read())

        # 使用 PIL 打开图像
        try:
            background_image_obj = Image.open(image_data)

            # 如果图像包含 Alpha 通道（模式为 'RGBA' 或 'LA'），则去除 Alpha 通道
            if background_image_obj.mode in ("RGBA", "LA"):
                # 将图像转换为 'RGB' 模式
                background_image_obj = background_image_obj.convert("RGB")

        except IOError:
            return JSONResponse(
                {"status": "error", "message": "Invalid image format"}, status_code=400
            )

    text_to_generate = data["text"]

    # Conditionally adjust spacing for English text based on user setting
    if data.get("enableEnglishSpacing", "false").lower() == "true":
        # Only apply to English words, leave Chinese text unchanged
        import re

        def replace_english_spaces(text):
            """Replace single spaces with double spaces only for English text, preserving all other whitespace"""
            # Pattern to identify English characters (including common punctuation, hyphens, underscores)
            english_pattern = r'^[a-zA-Z0-9.,!?;:\'\"()\-_]+$'

            # Split by lines to preserve newlines
            lines = text.split('\n')
            processed_lines = []

            for line in lines:
                # Only process spaces within each line, preserve tabs and other whitespace
                # Split only on spaces (not all whitespace)
                parts = line.split(' ')
                if len(parts) <= 1:
                    # No spaces in this line, keep as is
                    processed_lines.append(line)
                    continue

                result = []
                for i, part in enumerate(parts):
                    result.append(part)

                    # If this isn't the last part, check if we should add double space
                    if i < len(parts) - 1:
                        current_is_english = bool(re.match(english_pattern, part)) if part.strip() else False
                        next_is_english = bool(re.match(english_pattern, parts[i + 1])) if parts[i + 1].strip() else False

                        # Add double space only if both current and next parts are English
                        if current_is_english and next_is_english:
                            result.append('  ')  # Double space
                        else:
                            result.append(' ')   # Single space

                processed_lines.append(''.join(result))

            # Rejoin with newlines to preserve line structure
            return '\n'.join(processed_lines)

        text_to_generate = replace_english_spaces(text_to_generate)

    # if data["preview"] == "true":
    #     # 截短字符，只生成一面
    #     preview_length = 300  # 可以调整为所需的预览长度
    #     text_to_generate = text_to_generate[:preview_length]

    # 从表单中获取字体文件并处理 7.4
    if font_file is not None:
        report_progress("prepare_font", "正在加载字体文件", 30)
        if isinstance(font_file, (bytes, bytearray)):
            font_bytes = font_file
        else:
            font_bytes = await font_file.read()
        font = ImageFont.truetype(io.BytesIO(font_bytes), size=int(data["font_size"]))
    else:
        report_progress("prepare_font", "正在读取系统字体", 30)
        font_option = data["font_option"]
        logger.info(f"font_option: {font_option}")
        logger.info(f"font_file_names: {font_file_names}")
        if font_option in font_file_names:
            # 确定字体文件的完整路径
            font_path = os.path.join(font_assets_dir, font_option)
            logger.info(f"font_path: {font_path}")
            # 打开字体文件并读取其内容为字节
            with open(font_path, "rb") as f:
                font_content = f.read()
            # 通过 io.BytesIO 创建一个 BytesIO 对象，然后使用 ImageFont.truetype 从字节中加载字体
            font = ImageFont.truetype(
                io.BytesIO(font_content), size=int(data["font_size"])
            )
        else:
            return JSONResponse(
                {
                    "status": "fail",
                    "message": "Missing  fontfile.",
                },
                status_code=400,
            )

    template = Template(
        background=background_image_obj,
        font=font,
        line_spacing=int(data["line_spacing"]),  # + int(data["font_size"])
        # fill=ast.literal_eval(data["fill"])[:3],  # Ignore the alpha value
        # fill=(0),#如果feel是只有一个颜色的话那么在改变墨水的时候会导致R变化而GB不变化,颜色会变红 9.17
        left_margin=int(data["left_margin"]),
        top_margin=int(data["top_margin"]),
        right_margin=int(data["right_margin"]) - int(data["word_spacing"]) * 2,
        bottom_margin=int(data["bottom_margin"]),
        word_spacing=int(data["word_spacing"]),
        line_spacing_sigma=int(data["line_spacing_sigma"]),  # 行间距随机扰动
        font_size_sigma=int(data["font_size_sigma"]),  # 字体大小随机扰动
        word_spacing_sigma=int(data["word_spacing_sigma"]),  # 字间距随机扰动
        end_chars="，。",  # 防止特定字符因排版算法的自动换行而出现在行首
        perturb_x_sigma=int(data["perturb_x_sigma"]),  # 笔画横向偏移随机扰动
        perturb_y_sigma=int(data["perturb_y_sigma"]),  # 笔画纵向偏移随机扰动
        perturb_theta_sigma=float(data["perturb_theta_sigma"]),  # 笔画旋转偏移随机扰动
        strikethrough_probability=float(
            data["strikethrough_probability"]
        ),  # 删除线概率
        strikethrough_length_sigma=float(
            data["strikethrough_length_sigma"]
        ),  # 删除线长度随机扰动
        strikethrough_width_sigma=float(
            data["strikethrough_width_sigma"]
        ),  # 删除线宽度随机扰动
        strikethrough_angle_sigma=float(
            data["strikethrough_angle_sigma"]
        ),  # 删除线角度随机扰动
        strikethrough_width=float(data["strikethrough_width"]),  # 删除线宽度
        ink_depth_sigma=float(data["ink_depth_sigma"]),  # 墨水深度随机扰动
    )

    # 创建一个BytesIO对象，用于保存.zip文件的内容
    logger.info(f"data[pdf_save]: {data['pdf_save']}")
    if not data["pdf_save"] == "true":
        report_progress("rendering", "正在生成手写图像", 45)
        images = await run_in_threadpool(handwrite, text_to_generate, template)
        logger.info("handwrite initial images generated successfully")
        # 创建项目内的临时目录，避免使用系统临时目录
        project_temp_base = "./temp"
        os.makedirs(project_temp_base, exist_ok=True)
        temp_dir = tempfile.mkdtemp(dir=project_temp_base)
        unique_filename = "images_" + str(time.time())
        zip_path = f"./temp/{unique_filename}.zip"
        # 预览模式：检查是否为完整预览模式（本地开发）或单页预览模式（生产环境）
        is_preview = data["preview"] == "true"
        full_preview = data.get("full_preview", "true") if is_preview else None
        if is_preview:
            logger.info(f"Preview mode enabled, full_preview: {full_preview}")

        try:
            preview_images_base64 = []
            try:
                total_images = len(images)
                if total_images <= 0:
                    total_images = 1
            except TypeError:
                total_images = None
            for i, im in enumerate(images):
                if total_images is None:
                    # 兼容 handwrite 返回 map/generator 等无长度可迭代对象
                    dynamic_progress = min(90, 60 + min(i, 30))
                    report_progress("rendering", f"正在处理第 {i + 1} 页", dynamic_progress)
                else:
                    dynamic_progress = min(90, 60 + int((i / total_images) * 25))
                    report_progress("rendering", f"正在处理第 {i + 1}/{total_images} 页", dynamic_progress)
                # 保存每张图像到临时目录
                image_path = os.path.join(temp_dir, f"{i}.png")

                # 使用安全保存函数
                if safe_save_and_close_image(im, image_path):
                    logger.info(f"Image {i} saved successfully")
                else:
                    logger.error(f"Failed to save image {i}")

                del im  # 释放内存

                if is_preview:
                    # 预览模式：读取文件内容到内存
                    with open(image_path, "rb") as f:
                        image_data = f.read()

                    if full_preview == "false":
                        # 单页预览模式（生产环境）：只返回第一张图片，立即返回
                        safe_remove_directory(temp_dir)
                        report_progress("finalizing", "正在返回预览结果", 100)
                        return Response(
                            content=image_data,
                            media_type="image/png",
                        )

                    # 完整预览模式（本地开发）：将图片转换为Base64字符串
                    base64_str = base64.b64encode(image_data).decode('utf-8')
                    preview_images_base64.append(base64_str)

            if is_preview:
                # 完整预览模式：返回包含所有图片Base64字符串的JSON
                # 立即清理整个临时目录
                safe_remove_directory(temp_dir)
                report_progress("finalizing", "正在返回预览结果", 100)

                return JSONResponse(
                    {"status": "success", "images": preview_images_base64}
                )

            if not is_preview:
                report_progress("packaging", "正在打包ZIP文件", 92)
                # 创建ZIP文件
                shutil.make_archive(zip_path[:-4], "zip", temp_dir)

                # 读取ZIP文件到内存，然后立即删除文件
                try:
                    with open(zip_path, "rb") as f:
                        zip_data = f.read()

                    # 立即删除ZIP文件
                    safe_remove_file(zip_path)

                    # 从内存发送文件
                    report_progress("finalizing", "正在返回ZIP结果", 100)
                    response = Response(
                        content=zip_data,
                        media_type="application/zip",
                        headers={
                            "Content-Disposition": "attachment; filename=images.zip"
                        },
                    )
                except Exception as e:
                    logger.error(f"Failed to read ZIP file: {e}")
                    # 降级到直接读文件发送
                    with open(zip_path, "rb") as f:
                        zip_data = f.read()
                    report_progress("finalizing", "正在返回ZIP结果", 100)
                    response = Response(
                        content=zip_data,
                        media_type="application/zip",
                        headers={
                            "Content-Disposition": "attachment; filename=images.zip"
                        },
                    )
            return response
        finally:
            # 使用改进的安全删除函数
            safe_remove_directory(temp_dir)
            # ZIP文件已在上面删除，这里只是保险
    else:
        logger.info("PDF generate")
        temp_pdf_file_path = None  # 初始化变量
        report_progress("rendering", "正在生成手写图像", 45)
        images = await run_in_threadpool(handwrite, text_to_generate, template)
        try:
            report_progress("packaging", "正在导出PDF文件", 92)
            temp_pdf_file_path = await run_in_threadpool(generate_pdf, images=images)
            # 将文件路径存储在请求上下文中，以便稍后可以访问它
            # request.temp_file_path = temp_pdf_file_path  # FastAPI Request 无此属性
            with open(temp_pdf_file_path, "rb") as f:
                pdf_data = f.read()
            report_progress("finalizing", "正在返回PDF结果", 100)
            return Response(
                content=pdf_data,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=images.pdf"},
            )
        finally:
            # 清理生成的临时 PDF 文件
            if temp_pdf_file_path is not None and os.path.exists(temp_pdf_file_path):
                safe_remove_file(temp_pdf_file_path)
        # 2.9.2026 之前这里忘记删除temp_pdf_file_path, 根据记载是两年前就存在的问题，不知道最近为什么频繁出现
        #     if temp_pdf_file_path is not None:  # 检查变量是否已赋值
        #         for _ in range(5):  # 尝试5次
        #             try:
        #                 os.remove(temp_pdf_file_path)  # 尝试删除文件
        #                 break  # 如果成功删除，跳出循环
        #             except Exception as e:  # 捕获并处理删除文件时可能出现的异常
        #                 logger.error(f"Failed to remove temporary PDF file: {e}")
        #                 time.sleep(1)
        # unique_filename = "images_" + str(time.time()) + ".zip"

        # # 如果用户选择了保存为PDF，将所有图片合并为一个PDF文件
        # pdf_bytes = handwrite(text_to_generate, template, export_pdf=True, file_path=unique_filename)
        # logger.info("pdf generated successfully")
        # # 返回PDF文件
        # # mysql_operation(pdf_io)
        # return send_file(
        #     pdf_bytes,
        #     # attachment_filename="images.pdf",
        #     download_name="images.pdf",
        #     mimetype="application/pdf",
        #     as_attachment=True,
        # )


async def run_generation_task(task_id, base_url, payload):
    set_generation_task(
        task_id,
        status="processing",
        stage="started",
        message="任务已开始",
        progress=1,
    )
    await push_task_status_update(task_id)
    try:
        def progress_notify(**kwargs):
            set_generation_task(task_id, **kwargs)
            asyncio.create_task(push_task_status_update(task_id))

        async with _generation_semaphore:
            # 拿到信号量后，将阶段更新为"正在执行" 由于这里是协程，所以并不会占据很多资源 4.17.2026
            set_generation_task(task_id, stage="executing", message="正在生成中")
            await push_task_status_update(task_id)

            response = await generate_handwriting_impl(
                base_url=base_url,
                progress_hook=progress_notify,
                **payload,
            )
        response_body = response.body if response.body is not None else b""
        response_headers = {}
        if "content-disposition" in response.headers:
            response_headers["Content-Disposition"] = response.headers[
                "content-disposition"
            ]
        set_generation_task(
            task_id,
            status="completed",
            response_status_code=response.status_code,
            response_content_type=response.headers.get("content-type")
            or response.media_type
            or "application/octet-stream",
            response_headers=response_headers,
            response_body=response_body,
            stage="completed",
            message="任务处理完成",
            progress=100,
        )
        await push_task_status_update(task_id)
    except Exception as e:
        logger.exception("Generation task failed, task_id=%s", task_id)
        set_generation_task(
            task_id,
            status="failed",
            error_message=str(e),
            stage="failed",
            message="任务处理失败",
        )
        await push_task_status_update(task_id)


@app.post("/api/generate_handwriting")
@limiter.limit("200 per 5 minute")
@handle_exceptions  # 错误捕获的装饰器7.15
async def generate_handwriting(
    request: Request,
    background_tasks: BackgroundTasks,
    params: GenerateHandwritingParams = Depends(form_dependency_from_model(GenerateHandwritingParams)),
    background_image: Union[UploadFile, str] = File(None),
    font_file: Union[UploadFile, str] = File(None),
):
    cleanup_expired_generation_tasks()

    # ── 并发上限检查 ────────────────────────────────────────────────────
    MAX_ACTIVE_TASKS = 8  # pending + processing 总数上限，根据服务器配置调整
    # 队列满时给用户的建议等待时间（秒），固定值比瞎算可靠
    ESTIMATED_WAIT_SECONDS = 60

    active_count = get_generation_active_task_count()
    if active_count >= MAX_ACTIVE_TASKS:
        return JSONResponse(
            {
                "status": "queue_full",
                "message": "当前服务器队列已满，请稍后再试",
                "active_task_count": active_count,
                "max_active_tasks": MAX_ACTIVE_TASKS,
                "estimated_wait_seconds": ESTIMATED_WAIT_SECONDS,
            },
            status_code=503,
        )
    # ────────────────────────────────────────────────────────────────────

    background_image_bytes = None
    if isinstance(background_image, UploadFile):
        background_image_bytes = await background_image.read()

    font_file_bytes = None
    if isinstance(font_file, UploadFile):
        font_file_bytes = await font_file.read()

    payload = {
        "params": params,
        "background_image": background_image_bytes,
        "font_file": font_file_bytes,
    }

    task_id = uuid4().hex
    now = time.time()
    set_generation_task(
        task_id,
        status="pending",
        stage="queued",
        message="任务排队中",
        progress=0,
        created_at=now,
        updated_at=now,
        response_status_code=None,
        response_content_type=None,
        response_headers={},
        error_message=None,
    )
    background_tasks.add_task(run_generation_task, task_id, str(request.base_url), payload)

    return JSONResponse({"status": "accepted", "task_id": task_id})


@app.websocket("/api/generate_handwriting/ws/{task_id}")
async def generate_handwriting_task_websocket(websocket: WebSocket, task_id: str):
    await websocket.accept()
    await register_task_websocket(task_id, websocket)
    try:
        task = get_generation_task(task_id)
        if task is None:
            await websocket.send_json(
                {"status": "error", "message": "Task not found", "task_id": task_id}
            )
            return
        await websocket.send_json(build_task_status_payload(task_id, task=task))

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await unregister_task_websocket(task_id, websocket)


@app.get("/api/generate_handwriting/task/{task_id}")
@limiter.limit("600 per 5 minute")
@handle_exceptions
async def get_generate_handwriting_task_status(request: Request, task_id: str):
    cleanup_expired_generation_tasks()
    task = get_generation_task(task_id)
    if task is None:
        return JSONResponse(
            {"status": "error", "message": "Task not found"},
            status_code=404,
        )
    return JSONResponse(build_task_status_payload(task_id, task=task))


@app.get("/api/generate_handwriting/task/{task_id}/result")
@limiter.limit("600 per 5 minute")
@handle_exceptions
async def get_generate_handwriting_task_result(request: Request, task_id: str):
    cleanup_expired_generation_tasks()
    task = get_generation_task(task_id)
    if task is None:
        return JSONResponse(
            {"status": "error", "message": "Task not found"},
            status_code=404,
        )

    task_status = task.get("status")
    if task_status in ("pending", "processing"):
        return JSONResponse(
            {"status": "processing", "message": "Task is still running"},
            status_code=409,
        )
    if task_status == "failed":
        pop_generation_task(task_id)
        return JSONResponse(
            {"status": "error", "message": task.get("error_message", "Task failed")},
            status_code=500,
        )

    # 从磁盘文件读取响应体
    result_file_path = task.get("result_file_path")
    response_body = read_result_file(result_file_path) if result_file_path else b""
    if response_body is None:
        response_body = b""

    response = Response(
        content=response_body,
        media_type=task.get("response_content_type") or "application/octet-stream",
        status_code=task.get("response_status_code") or 200,
        headers=task.get("response_headers") or {},
    )
    pop_generation_task(task_id)
    return response


# @app.after_request
# def cleanup(response):
#     # 从请求上下文中获取文件路径
#     temp_file_path = getattr(request, 'temp_file_path', None)
#     if temp_file_path is not None:
#         # 尝试删除文件
#         try:
#             os.remove(temp_file_path)
#         except Exception as e:
#             app.logger.error(f"Failed to remove temporary PDF file: {e}")
#     # 返回原始响应
#     return response


@app.post("/api/textfileprocess")
@limiter.limit("200 per 5 minute")
async def textfileprocess(request: Request, file: UploadFile = File(...)):
    if file is None or file.filename == "":
        return JSONResponse({"error": "No file part in the request"}, status_code=400)

    if file and (
        file.filename.endswith(".docx")
        or file.filename.endswith(".pdf")
        or file.filename.endswith(".doc")
        or file.filename.endswith(".txt")
        or file.filename.endswith(".rtf")
    ):
        filename = secure_filename(file.filename)
        filepath = os.path.join(".", "textfileprocess", filename)  # 临时目录
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        text = "读取失败"  # Default value for text
        try:
            if file.filename.endswith(".docx"):
                text = convert_docx_to_text(filepath)
            elif file.filename.endswith(".pdf"):
                text = read_pdf(filepath)
            elif file.filename.endswith(".txt") or file.filename.endswith(".rtf"):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            elif file.filename.endswith(".doc"):
                text = "doc文件暂不支持"
        except Exception as e:
            return JSONResponse(
                {"error": f"Error reading file: {str(e)}"}, status_code=500
            )

        # 删除临时文件
        safe_remove_file(filepath)

        return JSONResponse({"text": text})

    return JSONResponse({"error": "Invalid file type"}, status_code=400)


@app.post("/api/imagefileprocess")
@limiter.limit("200 per 5 minute")
async def imagefileprocess(request: Request, file: UploadFile = File(...)):
    if file is None or file.filename == "":
        return JSONResponse({"error": "No file part in the request"}, status_code=400)

    if file and (
        file.filename.endswith(".jpf")
        or file.filename.endswith(".png")
        or file.filename.endswith(".jpg")
        or file.filename.endswith(".jpeg")
    ):
        filename = secure_filename(file.filename)
        filepath = os.path.join("./imagefileprocess", filename)
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        (
            avg_l_whitespace,
            avg_r_whitespace,
            avg_t_whitespace,
            avg_b_whitespace,
            avg_distance,
        ) = identify_distance(filepath)
        safe_remove_file(filepath)
        return JSONResponse(
            {
                "marginLeft": avg_l_whitespace,
                "marginRight": avg_r_whitespace,
                "marginTop": avg_t_whitespace,
                "marginBottom": avg_b_whitespace,
                "lineSpacing": avg_distance,
            }
        )
    else:
        return JSONResponse({"error": "Invalid file type"}, status_code=400)


def get_filenames_in_dir(directory):
    return [
        f
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and f.endswith(".ttf")
    ]


@app.get("/api/fonts_info")
def get_fonts_info():
    filenames = get_filenames_in_dir(font_assets_dir)
    logger.info(f"filenames: {filenames}")
    if filenames == []:
        return JSONResponse({"error": "fontfile not found"}, status_code=400)
    return JSONResponse(filenames)


def mysql_operation(image_data):
    # cursor = current_app.cnx.cursor()
    # username = session["username"]
    username = None  # session 已移除
    # 先检查用户是否已存在
    # cursor.execute("SELECT * FROM user_images WHERE username=%s", (username,))
    # result = cursor.fetchone()

    # 根据查询结果来判断应该插入新纪录还是更新旧纪录
    # if result is None:
    #     # 如果用户不存在，插入新纪录
    #     sql = "INSERT INTO user_images (username, image) VALUES (%s, %s)"
    #     params = (username, image_data)
    # else:
    #     # 如果用户已存在，更新旧纪录
    #     sql = "UPDATE user_images SET image=%s WHERE username=%s"
    #     params = (image_data, username)
    try:
        pass
        # 执行 SQL 语句
        # 提交到数据库执行
        # cursor.execute(sql, params)
        # current_app.cnx.commit()
    except Exception as e:
        # 发生错误时回滚
        # current_app.cnx.rollback()
        logger.info(f"An error occurred: {e}")


# @app.route("/api/login", methods=["POST"])
# def login():
#     data = request.get_json()
#     username = data.get("username")
#     password = data.get("password")
#     logger.info(f"Received username: {username}")  # 打印接收到的用户名
#     logger.info(f"Received password: {password}")  # 打印接收到的密码
#     try:
#         cursor = current_app.cnx.cursor()
#         cursor.execute(
#             f"SELECT password FROM user_images WHERE username=%s", (username,)
#         )
#         result = cursor.fetchone()
#     except Exception as e:
#         logger.error(f"An error occurred: {e}")
#         return jsonify({"error": "An error occurred"}), 500

#     if result and result[0] == password:
#         session["username"] = username
#         session.permanent = True
#         logger.info(f"Login success for user: {username}")
#         return {"status": "success"}, 200
#     else:
#         logger.error(f"Login failed for user: {username}")
#         return {
#             "status": "failed",
#             "error": "Login failed. Check your username and password.",
#         }, 401


# @app.route("/api/register", methods=["POST"])
# def register():
#     data = request.get_json()
#     username = data.get("username")
#     password = data.get("password")
#     try:
#         cursor = current_app.cnx.cursor()
#         cursor.execute(f"SELECT * FROM user_images WHERE username=%s", (username,))
#         result = cursor.fetchone()
#     except Exception as e:
#         logger.error(f"An error occurred: {e}")
#         return jsonify({"error": "An error occurred"}), 500

#     if not result:
#         try:
#             cursor.execute(
#                 f"INSERT INTO user_images (username, password) VALUES (%s, %s)",
#                 (username, password),
#             )
#             current_app.cnx.commit()
#             session["username"] = username
#             logger.info(f"User: {username} registered successfully.")
#             return jsonify(
#                 {
#                     "status": "success",
#                     "message": "Account created successfully. You can now log in.",
#                 }
#             )
#         except mysql.connector.Error as err:
#             logger.error(f"Failed to insert user: {username} into DB. Error: {err}")
#             return (
#                 jsonify(
#                     {
#                         "status": "fail",
#                         "message": "Error occurred during registration.",
#                     }
#                 ),
#                 500,
#             )
#     else:
#         logger.error(f"Username: {username} already exists.")
#         return (
#             jsonify(
#                 {
#                     "status": "fail",
#                     "message": "Username already exists. Choose a different one.",
#                 }
#             ),
#             400,
#         )


# 捕获所有未捕获的异常，返回给前端，只能用于生产环境7.12
# @app.errorhandler(Exception)
# def handle_exception(e):
#     # Pass the error to Flask's default error handling.
#       tb = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
#     response = {
#
#             "type": type(e).__name__,  # The type of the exception
#             "message": str(e),  # The message of the exception
#
#     }
#     return jsonify(response), 500


# @app.before_request
# def before_request():
#     if enable_user_auth.lower() == "true":
#         current_app.cnx = mysql.connector.connect(
#             host=mysql_host, user="myuser", password="mypassword", database="mydatabase"
#         )
#     else:
#         pass


@app.middleware("http")
async def after_request(request: Request, call_next):
    response = await call_next(request)
    if enable_user_auth.lower() == "true":
        # if hasattr(current_app, "cnx"):
        #     current_app.cnx.close()
        # 仅用于调试 7.13
        # session.clear()
        return response
    else:
        print(response)
        return response


if __name__ == "__main__":
    import uvicorn

    # 启动时清理之前标记的目录
    cleanup_marked_directories()
    uvicorn.run(app, host="0.0.0.0", port=5005)


# poetry
def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5005)

    # good luck 6/16/2023
    # thank you 2/14/2025


"""    
数据库初始化操作

CREATE TABLE user_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE, 
    password VARCHAR(255), 
    image BLOB,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


数据库结构
mysql -u root -p进入数据库
USE your_database;数据库中的一个库
describe user_images;表：
"""

import time
from flask import Flask, request, jsonify, send_file, session, current_app
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
from flask_cors import CORS
from datetime import timedelta
from flask_session import Session  # 导入扩展
from werkzeug.utils import secure_filename

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
from sentry_sdk.integrations.flask import FlaskIntegration

# 限制请求速率 7.9
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 装饰器 7.15
from functools import wraps

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
directory = "./font_assets"
font_file_names = [
    f
    for f in os.listdir(directory)
    if os.path.isfile(os.path.join(directory, f)) and f.endswith(".ttf")
]
# sentry部分 7.7
sentry_sdk.init(
    dsn="https://ed22d5c0e3584faeb4ae0f67d19f68aa@o4505255803551744.ingest.sentry.io/4505485583253504",
    integrations=[
        FlaskIntegration(),
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

app = Flask(__name__)
CORS(app)  # , origins='*', supports_credentials=True)

# 设置Flask app的logger级别
app.logger.setLevel(logging.DEBUG)


SECRET_KEY = "437d75c5af744b76607fe862cf8a5a368519aca486d62c5fa69ba42c16809z88"
app.config["SECRET_KEY"] = SECRET_KEY
# app.config["SESSION_COOKIE_SECURE"] = True
# app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024 * 1024
app.permanent_session_lifetime = timedelta(minutes=5000000)
app.config["SESSION_TYPE"] = "filesystem"  # 设置session存储方式为文件
Session(app)  # 初始化扩展，传入应用程序实例
limiter = Limiter(
    app=app, key_func=get_remote_address, default_limits=["1000 per 5 minute"]
)


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


# import pypandoc
# pypandoc.download_pandoc()


def convert_docx_to_text(docx_file_path):
    # 转换文件为纯文本格式，并返回转换后的文本内容
    # text = pypandoc.convert_file(docx_file_path, 'plain')
    # return text
    return None


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
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.info("An error occurred during the request: %s", e)
            return jsonify({"status": "error", "message": str(e)}), 500

    return decorated_function


@app.route("/api/generate_handwriting", methods=["POST"])
@limiter.limit("200 per 5 minute")
@handle_exceptions  # 错误捕获的装饰器7.15
def generate_handwriting():
    cpu_usage = psutil.cpu_percent(interval=1)  # 获取 CPU 使用率，1 秒采样间隔
    if cpu_usage > 90:
        # 如果 CPU 使用率超过 90%，返回提醒
        return (
            jsonify(
                {
                    "status": "waiting",
                    "message": f"CPU usage is too high. Please wait and try again. current cpu_usage: {cpu_usage}%",
                }
            ),
            429,
        )  # HTTP 429: Too Many Requests
    # logger.info("已经进入generate_handwriting")
    if enable_user_auth.lower() == "true":
        if "username" not in session:
            return jsonify({"status": "error", "message": "You haven't login."}), 500
    # try:
    # 先获取 form 数据
    data = request.form
    if len(data["text"]) > 10000 and (
        request.base_url == "https://handwrite.14790897.xyz"
        or request.base_url == "https://handwrite.paperai.life"
    ):
        # 请自己构建应用来运行而不是使用这个网页
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "The text is too long to process. If you want to use this service, please build your own application.",
                }
            ),  
            500,
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
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": f"Missing required field: {field}",
                    }
                ),
                400,
            )
        else:
            logger.info(f"{field}: {data[field]}")  # 打印具体的 form 字段值
            # 如果存在height和width，就创建一个新的背景图     todo
            # height=int(data["height"]),
            # width=int(data["width"]),

    # 如果用户提供了宽度和高度，创建一个新的笔记本背景图像
    if "width" in data and "height" in data:
        line_spacing = int(data.get("line_spacing", 30))
        top_margin = int(data.get("top_margin", 0))
        bottom_margin = int(data.get("bottom_margin", 0))
        left_margin = int(data.get("left_margin", 0))
        right_margin = int(data.get("right_margin", 0))
        width = int(data["width"])
        height = int(data["height"])
        font_size = int(data.get("font_size", 0))
        isUnderlined = data.get("isUnderlined", False)
        background_image = create_notebook_image(
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
        background_image = request.files.get("background_image")
        if background_image is None:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": "Missing required field: background_image",
                    }
                ),
                400,
            )
        image_data = io.BytesIO(background_image.read())

        # 使用 PIL 打开图像
        try:
            background_image = Image.open(image_data)

            # 如果图像包含 Alpha 通道（模式为 'RGBA' 或 'LA'），则去除 Alpha 通道
            if background_image.mode in ("RGBA", "LA"):
                # 将图像转换为 'RGB' 模式
                background_image = background_image.convert("RGB")

        except IOError:
            return jsonify({"status": "error", "message": "Invalid image format"}), 400

    text_to_generate = data["text"]
    # if data["preview"] == "true":
    #     # 截短字符，只生成一面
    #     preview_length = 300  # 可以调整为所需的预览长度
    #     text_to_generate = text_to_generate[:preview_length]

    # 从表单中获取字体文件并处理 7.4
    if "font_file" in request.files:
        font = request.files["font_file"].read()
        font = ImageFont.truetype(io.BytesIO(font), size=int(data["font_size"]))
    else:
        font_option = data["font_option"]
        logger.info(f"font_option: {font_option}")
        logger.info(f"font_file_names: {font_file_names}")
        if font_option in font_file_names:
            # 确定字体文件的完整路径
            font_path = os.path.join("font_assets", font_option)
            logger.info(f"font_path: {font_path}")
            # 打开字体文件并读取其内容为字节
            with open(font_path, "rb") as f:
                font_content = f.read()
            # 通过 io.BytesIO 创建一个 BytesIO 对象，然后使用 ImageFont.truetype 从字节中加载字体
            font = ImageFont.truetype(
                io.BytesIO(font_content), size=int(data["font_size"])
            )
        else:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": "Missing  fontfile.",
                    }
                ),
                400,
            )

    template = Template(
        background=background_image,
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
        images = handwrite(text_to_generate, template)
        logger.info("handwrite initial images generated successfully")
        # 创建项目内的临时目录，避免使用系统临时目录
        project_temp_base = "./temp"
        os.makedirs(project_temp_base, exist_ok=True)
        temp_dir = tempfile.mkdtemp(dir=project_temp_base)
        unique_filename = "images_" + str(time.time())
        zip_path = f"./temp/{unique_filename}.zip"
        try:
            for i, im in enumerate(images):
                # 保存每张图像到临时目录
                image_path = os.path.join(temp_dir, f"{i}.png")

                # 使用安全保存函数
                if safe_save_and_close_image(im, image_path):
                    logger.info(f"Image {i} saved successfully")
                else:
                    logger.error(f"Failed to save image {i}")

                del im  # 释放内存

                if data["preview"] == "true":
                    # 预览模式：读取文件内容到内存，然后清理临时目录

                    with open(image_path, "rb") as f:
                        image_data = f.read()

                    # 立即清理整个临时目录
                    # safe_remove_directory(temp_dir)

                    # 从内存发送文件
                    return send_file(
                        io.BytesIO(image_data),
                        mimetype="image/png",
                        as_attachment=False,
                    )

            if not data["preview"] == "true":
                # 创建ZIP文件
                shutil.make_archive(zip_path[:-4], "zip", temp_dir)

                # 读取ZIP文件到内存，然后立即删除文件
                try:
                    with open(zip_path, "rb") as f:
                        zip_data = f.read()

                    # 立即删除ZIP文件
                    safe_remove_file(zip_path)

                    # 从内存发送文件
                    response = send_file(
                        io.BytesIO(zip_data),
                        download_name="images.zip",
                        mimetype="application/zip",
                        as_attachment=True,
                    )
                except Exception as e:
                    logger.error(f"Failed to read ZIP file: {e}")
                    # 降级到直接发送文件
                    response = send_file(
                        zip_path,
                        download_name="images.zip",
                        mimetype="application/zip",
                        as_attachment=True,
                    )
            return response
        finally:
            # 使用改进的安全删除函数
            safe_remove_directory(temp_dir)
            # ZIP文件已在上面删除，这里只是保险
    else:
        logger.info("PDF generate")
        temp_pdf_file_path = None  # 初始化变量
        images = handwrite(text_to_generate, template)
        try:
            temp_pdf_file_path = generate_pdf(images=images)
            # 将文件路径存储在请求上下文中，以便稍后可以访问它
            request.temp_file_path = temp_pdf_file_path
            return send_file(
                temp_pdf_file_path,
                download_name="images.pdf",
                mimetype="application/pdf",
                as_attachment=True,
                conditional=True,
            )
        finally:
            pass
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


@app.route("/api/textfileprocess", methods=["POST"])
@limiter.limit("200 per 5 minute")
def textfileprocess():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file part in the request"}), 400

    if file and (
        file.filename.endswith(".docx")
        or file.filename.endswith(".pdf")
        or file.filename.endswith(".doc")
        or file.filename.endswith(".txt")
        or file.filename.endswith(".rtf")
    ):
        filename = secure_filename(file.filename)
        filepath = os.path.join(".", "textfileprocess", filename)  # 临时目录
        file.save(filepath)
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
            return jsonify({"error": f"Error reading file: {str(e)}"}), 500

        # 删除临时文件
        safe_remove_file(filepath)

        return jsonify({"text": text})

    return jsonify({"error": "Invalid file type"}), 400


@app.route("/api/imagefileprocess", methods=["POST"])
@limiter.limit("200 per 5 minute")
def imagefileprocess():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file part in the request"}), 400

    if file and (
        file.filename.endswith(".jpf")
        or file.filename.endswith(".png")
        or file.filename.endswith(".jpg")
        or file.filename.endswith(".jpeg")
    ):
        filename = secure_filename(file.filename)
        filepath = os.path.join("./imagefileprocess", filename)
        file.save(filepath)
        (
            avg_l_whitespace,
            avg_r_whitespace,
            avg_t_whitespace,
            avg_b_whitespace,
            avg_distance,
        ) = identify_distance(filepath)
        safe_remove_file(filepath)
        return jsonify(
            {
                "marginLeft": avg_l_whitespace,
                "marginRight": avg_r_whitespace,
                "marginTop": avg_t_whitespace,
                "marginBottom": avg_b_whitespace,
                "lineSpacing": avg_distance,
            }
        )
    else:
        return jsonify({"error": "Invalid file type"}), 400


def get_filenames_in_dir(directory):
    return [
        f
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and f.endswith(".ttf")
    ]


@app.route("/api/fonts_info", methods=["GET"])
def get_fonts_info():
    filenames = get_filenames_in_dir("./font_assets")
    logger.info(f"filenames: {filenames}")
    if filenames == []:
        return jsonify({"error": "fontfile not found"}), 400
    return jsonify(filenames)


def mysql_operation(image_data):
    cursor = current_app.cnx.cursor()
    username = session["username"]
    # 先检查用户是否已存在
    cursor.execute("SELECT * FROM user_images WHERE username=%s", (username,))
    result = cursor.fetchone()

    # 根据查询结果来判断应该插入新纪录还是更新旧纪录
    if result is None:
        # 如果用户不存在，插入新纪录
        sql = "INSERT INTO user_images (username, image) VALUES (%s, %s)"
        params = (username, image_data)
    else:
        # 如果用户已存在，更新旧纪录
        sql = "UPDATE user_images SET image=%s WHERE username=%s"
        params = (image_data, username)
    try:
        pass
        # 执行 SQL 语句
        # 提交到数据库执行
        cursor.execute(sql, params)
        current_app.cnx.commit()
    except Exception as e:
        # 发生错误时回滚
        current_app.cnx.rollback()
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


@app.after_request
def after_request(response):
    if enable_user_auth.lower() == "true":
        if hasattr(current_app, "cnx"):
            current_app.cnx.close()
        # 仅用于调试 7.13
        # session.clear()
        return response
    else:
        print(response)
        return response


if __name__ == "__main__":
    # 启动时清理之前标记的目录
    cleanup_marked_directories()
    app.run(debug=True, host="0.0.0.0", port=5000)


# poetry
def main():
    app.run(debug=True, host="0.0.0.0", port=5000)

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

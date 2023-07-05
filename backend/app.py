from flask import Flask, request, jsonify, send_file, session, current_app
from handright import Template, handwrite
from PIL import Image, ImageFont
from threading import Thread
from PIL import Image, ImageFont, ImageQt, ImageDraw
from dotenv import load_dotenv

load_dotenv()
import os

# import MySQLdb
import mysql.connector
from flask import g
import zipfile
import ast, io
import logging
from flask_cors import CORS
from datetime import timedelta
from flask_session import Session  # 导入扩展
from werkzeug.utils import secure_filename
#文件模块
from docx import Document
import PyPDF2



# 创建一个logger
logger = logging.getLogger(__name__)

# 设置日志级别
logger.setLevel(logging.DEBUG)

# 创建 console handler，并设置级别为 DEBUG
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# 创建 file handler，并设置级别为 DEBUG
fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)

# 创建 formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 把 formatter 添加到 ch 和 fh
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# 把 ch 和 fh 添加到 logger
logger.addHandler(ch)
logger.addHandler(fh)

app = Flask(__name__)
CORS(app)#, origins='*', supports_credentials=True)

# 设置Flask app的logger级别
app.logger.setLevel(logging.DEBUG)


SECRET_KEY = "437d75c5af744b76607fe862cf8a5a368519aca486d62c5fa69ba42c16809z88"
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024 * 1024
app.permanent_session_lifetime = timedelta(minutes=5000000)
app.config['SESSION_TYPE'] = 'filesystem'  # 设置session存储方式为文件
Session(app)  # 初始化扩展，传入应用程序实例


# 创建一个新的白色图片，并添加间隔的线条作为背景
def create_notebook_image(width, height, line_spacing, top_margin, bottom_margin, left_margin, right_margin, font_size):
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    y = top_margin + font_size + line_spacing # 开始的y坐标设为顶部边距加字体大小
    while y < height - bottom_margin:  # 当y坐标小于（图片高度-底部边距）时，继续画线
        draw.line((left_margin, y, width - right_margin, y), fill="black")
        y += line_spacing  # 每次循环，y坐标增加行间距
    return image


def read_docx(file_path):
    document = Document(file_path)
    text = ' '.join([paragraph.text for paragraph in document.paragraphs])
    return text

def read_pdf(file_path):
    pdf_file_obj = open(file_path, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)
    text = ''
    for page_num in range(pdf_reader.numPages):
        page_obj = pdf_reader.getPage(page_num)
        text += page_obj.extractText()
    pdf_file_obj.close()
    return text

@app.route("/api/generate_handwriting", methods=["POST"])
def generate_handwriting():
    logger.info('已经进入generate_handwriting')
    if "username" not in session:
        return jsonify({"status": "error", "message": "You haven't login." }), 500
    # try:
    # 先获取 form 数据
    data = request.form
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
          #"height","width",

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
            #如果存在height和width，就创建一个新的背景图     todo  
            #height=int(data["height"]),
            #width=int(data["width"]),

    # 然后获取文件数据
    # files = request.files
    # required_file_fields = [ "font_file"]

    # for field in required_file_fields:
    #     if field not in files:
    #         return (
    #             jsonify(
    #                 {
    #                     "status": "fail",
    #                     "message": f"Missing required file field: {field}",
    #                 }
    #             ),
    #             400,
    #         )
    #     else:
    #         # 文件字段无法直接打印具体值，只能确认其存在
    #         logger.info(f"{field} exists in the files")
    
     # 如果用户提供了宽度和高度，创建一个新的笔记本背景图像
    if 'width' in data and 'height' in data:
        line_spacing = int(data.get('line_spacing', 30))
        top_margin = int(data.get('top_margin', 0))
        bottom_margin = int(data.get('bottom_margin', 0))
        left_margin = int(data.get('left_margin', 0))
        right_margin = int(data.get('right_margin', 0))
        width = int(data['width'])
        height = int(data['height'])
        font_size = int(data.get("font_size", 0))
        background_image = create_notebook_image(width, height, line_spacing, top_margin, bottom_margin, left_margin, right_margin, font_size)


    else:
        # 否则使用用户上传的背景图像
        background_image = request.files.get('background_image')
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
        background_image = Image.open(io.BytesIO(background_image.read()))
        
    text_to_generate = data["text"]
    if data["preview"] == "true":
        # 截短字符，只生成一面
        preview_length = 400  # 可以调整为所需的预览长度
        text_to_generate = text_to_generate[:preview_length]

    # 从表单中获取字体文件并处理 7.4
    if 'font_file' in request.files:
        font = request.files["font_file"].read()
        font = ImageFont.truetype(io.BytesIO(font), size=int(data["font_size"]))
    else:
        font_option = data['font_option']
        logger.info(f"font_option: {font_option}")
        logger.info(f"font_file_names: {font_file_names}")
        if font_option in font_file_names:
            # 确定字体文件的完整路径
            font_path = os.path.join('font_assets', font_option)
            logger.info(f"font_path: {font_path}")
            # 打开字体文件并读取其内容为字节
            with open(font_path, 'rb') as f:
                font_content = f.read()
            #通过 io.BytesIO 创建一个 BytesIO 对象，然后使用 ImageFont.truetype 从字节中加载字体
            font = ImageFont.truetype(io.BytesIO(font_content), size=int(data["font_size"]))
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
        line_spacing=int(data["line_spacing"]),# + int(data["font_size"])
        # fill=ast.literal_eval(data["fill"])[:3],  # Ignore the alpha value
        fill=(0),
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
    )
    images = handwrite(text_to_generate, template)
    logger.info("images generated successfully")

    # 创建一个BytesIO对象，用于保存.zip文件的内容
    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, "w") as zipf:
        # 遍历生成的所有图片
        for i, im in enumerate(images):
            # 使用os模块来连接路径和文件名
            # image_path = os.path.join(output_path, f"{i}.png")
            # im.save(image_path)
            # 将每张图片保存为一个BytesIO对象
            img_io = io.BytesIO()
            im.save(img_io, "PNG")
            img_io.seek(0)
            if data["preview"]=='true':
                # mysql_operation(img_io)
                logger.info('预览图片已返回')
                return send_file(io.BytesIO(img_io.getvalue()), mimetype="image/png")
            else:
                # 将图片BytesIO对象添加到.zip文件中
                zipf.writestr(f"{i}.png", img_io.getvalue())
    # 将BytesIO对象的位置重置到开始
    zip_io.seek(0)
    if not data["preview"]=='true':
        # 返回.zip文件
        # mysql_operation(zip_io)
        logger.info('zip文件已返回')
        return send_file(
            zip_io,
            # attachment_filename="images.zip",
            download_name="images.zip",
            mimetype="application/zip",
            as_attachment=True,
        )
    # except Exception as e:
    #     logger.info("An error occurred during the request: %s", e)
    #     return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route("/api/textfileprocess", methods=["POST"])
def textfileprocess():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file part in the request'}), 400

    if file and (file.filename.endswith('.docx') or file.filename.endswith('.pdf') or file.filename.endswith('.doc') or file.filename.endswith('.txt') or file.filename.endswith('.rtf')):
        filename = secure_filename(file.filename)
        filepath = os.path.join('./textfileprocess', filename)  # 你的临时目录
        file.save(filepath)

        if file.filename.endswith('.docx'):
            text = read_docx(filepath)        
        elif file.filename.endswith('.pdf'):
            text = read_pdf(filepath)
        elif file.filename.endswith('.txt') or file.filename.endswith('.rtf'):
            with open(filepath, 'r') as f:
                text = f.read()

        # 删除临时文件
        os.remove(filepath)

        return jsonify({'text': text})

    return jsonify({'error': 'Invalid file type'}), 400

def get_filenames_in_dir(directory):
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

@app.route("/api/fonts_info", methods=["GET"])
def get_fonts_info():
    filenames  = get_filenames_in_dir('./font_assets')
    if filenames == []:
        return jsonify('not found')
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
            
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    logger.info(f"Received username: {username}")  # 打印接收到的用户名
    logger.info(f"Received password: {password}")  # 打印接收到的密码
    cursor = current_app.cnx.cursor()
    cursor.execute(f"SELECT password FROM user_images WHERE username=%s", (username,))
    result = cursor.fetchone()

    if result and result[0] == password:
        session["username"] = username
        session.permanent = True
        logger.info(f"Login success for user: {username}")
        return {"status": "success"}, 200
    else:
        logger.error(f"Login failed for user: {username}")
        return {
            "status": "failed",
            "message": "Login failed. Check your username and password.",
        }, 401


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    cursor = current_app.cnx.cursor()
    cursor.execute(f"SELECT * FROM user_images WHERE username=%s", (username,))
    result = cursor.fetchone()


    if not result:
        try:
            cursor.execute(
                f"INSERT INTO user_images (username, password) VALUES (%s, %s)",
                (username, password),
            )
            current_app.cnx.commit()
            session["username"] = username
            logger.info(f"User: {username} registered successfully.")
            return jsonify(
                {
                    "status": "success",
                    "message": "Account created successfully. You can now log in.",
                }
            )
        except mysql.connector.Error as err:
            logger.error(f"Failed to insert user: {username} into DB. Error: {err}")
            return (
                jsonify(
                    {
                        "status": "fail",
                        "message": "Error occurred during registration.",
                    }
                ),
                500,
            )
    else:
        logger.error(f"Username: {username} already exists.")
        return (
            jsonify(
                {
                    "status": "fail",
                    "message": "Username already exists. Choose a different one.",
                }
            ),
            400,
        )


@app.before_request
def before_request():
    current_app.cnx = mysql.connector.connect(
        host="localhost", user="myuser", password="mypassword", database="your_database"
    )

    # current_app.cnx  = mysql.connector.connect(
    #     user='root',
    #     password=os.getenv('MYSQL_ROOT_PASSWORD'),
    #     host='127.0.0.1',
    #     database=os.getenv('MYSQL_DATABASE'))


@app.after_request
def after_request(response):
    current_app.cnx.close()
    return response


if __name__ == "__main__":
     # 获取当前路径
    current_path = os.getcwd()
    # 创建一个子文件夹用于存储输出的图片
    output_path = os.path.join(current_path, 'output')
    # 如果子文件夹不存在，就创建它
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    directory = './textfileprocess'
    if not os.path.exists(directory):
        os.makedirs(directory)
    directory = './font_assets'
    font_file_names = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    app.run(debug=True, host="0.0.0.0", port=5000)
    # good luck 6/16/2023
'''    
数据库初始化操作
'''
"""
CREATE TABLE user_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE, 
    image BLOB,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

"""
'''
数据库结构
mysql -u root -p进入数据库
USE your_database;数据库中的一个库
describe user_images;表：
'''
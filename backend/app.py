from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageFont
from handright import Template, handwrite
from threading import Thread
from PIL import Image, ImageFont, ImageQt
from dotenv import load_dotenv
load_dotenv()
import os
# import MySQLdb
import mysql.connector
from flask import g
import zipfile
import ast, io
import logging

# 创建一个logger
logger = logging.getLogger(__name__)

# 设置日志级别
logger.setLevel(logging.DEBUG)  # 这会设置日志级别为DEBUG

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

SECRET_KEY='437d75c5af744b76607fe862cf8a5a368519aca486d62c5fa69ba42c16809z88'
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024

@app.route('/api/generate_handwriting', methods=['POST'])
def generate_handwriting():
    try:
        data = request.form
        required_fields = ['text', 'font_size', 'line_spacing', 'fill', 'left_margin', 'top_margin', 
                           'right_margin', 'bottom_margin', 'word_spacing', 'line_spacing_sigma', 
                           'font_size_sigma', 'word_spacing_sigma', 'perturb_x_sigma', 'perturb_y_sigma', 
                           'perturb_theta_sigma', 'preview']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'fail', 'message': f'Missing required field: {field}'}), 400

        data = request.form
        print('request.form', data)
        print('request.files', request.files)
        text_to_generate = data['text']
        if data['preview'] == 'true':
            #截短字符，只生成一面
            preview_length = 400  # 可以调整为所需的预览长度
            text_to_generate = text_to_generate[:preview_length]
        background_image = request.files['background_image'].read()
        background_image = Image.open(io.BytesIO(background_image))
        font = request.files['font_path'].read()
        font = ImageFont.truetype(io.BytesIO(font), size=int(data['font_size']))

        template = Template(
            background=background_image,
            font=font,
            line_spacing=int(data['line_spacing']) + int(data['font_size']),
            fill = ast.literal_eval(data['fill'])[:3],  # Ignore the alpha value
            # fill=(int(data['red']), int(data['green']), int(data['blue'])),  # 字体“颜色”
            left_margin=int(data['left_margin']),
            top_margin=int(data['top_margin']),
            right_margin=int(data['right_margin']) - int(data['word_spacing']) * 2,
            bottom_margin=int(data['bottom_margin']),
            word_spacing=int(data['word_spacing']),
            line_spacing_sigma=int(data['line_spacing_sigma']),  # 行间距随机扰动
            font_size_sigma=int(data['font_size_sigma']),  # 字体大小随机扰动
            word_spacing_sigma=int(data['word_spacing_sigma']),  # 字间距随机扰动
            end_chars="，。",  # 防止特定字符因排版算法的自动换行而出现在行首
            perturb_x_sigma=int(data['perturb_x_sigma']),  # 笔画横向偏移随机扰动
            perturb_y_sigma=int(data['perturb_y_sigma']),  # 笔画纵向偏移随机扰动
            perturb_theta_sigma=float(data['perturb_theta_sigma']),  # 笔画旋转偏移随机扰动
        )
        images = handwrite(text_to_generate, template)
        cursor = g.cnx.cursor()

        # 创建一个BytesIO对象，用于保存.zip文件的内容
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, 'w') as zipf:
            # 遍历生成的所有图片
            for i, im in enumerate(images):
                im.save("./output/{}.png".format(i))
                # 将每张图片保存为一个BytesIO对象
                img_io = io.BytesIO()
                im.save(img_io, 'PNG')
                img_io.seek(0)
                if not data['preview']:
                    # 将图片BytesIO对象添加到.zip文件中
                    zipf.writestr(f"{i}.png", img_io.getvalue())

                # 保存图片到数据库
                username = session['username']
                sql = f"INSERT INTO user_images (username, image) VALUES (%s, %s)"
                image_data = img_io.getvalue()
                params = (username, image_data)
                try:
                    # 执行 SQL 语句
                    cursor.execute(sql, params)
                    # 提交到数据库执行
                    g.cnx.commit()
                except:
                    # 发生错误时回滚
                    g.cnx.rollback()

                if data['preview']:
                    return send_file(io.BytesIO(image_data), mimetype='image/png')

        # 将BytesIO对象的位置重置到开始
        zip_io.seek(0)
        if not data['preview']:
            # 返回.zip文件
            return send_file(zip_io,
                            attachment_filename='images.zip',
                            mimetype='application/zip',
                            as_attachment=True)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    logger.info(f"Received username: {username}")  # 打印接收到的用户名
    logger.info(f"Received password: {password}")  # 打印接收到的密码
    if r.exists(username) and r.get(username) == password:
        session.permanent = True
        session['username'] = username
        print('session/login', session)
        return {'status': 'success'}, 200
    else:
        return {'status': 'failed', 'message': 'Login failed. Check your username and password.'}, 401
    
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not r.exists(username):
        r.set(username, password)
        session['username'] = username
        return jsonify({'status': 'success', 'message': 'Account created successfully. You can now log in.'})
    else:
        return jsonify({'status': 'fail', 'message': 'Username already exists. Choose a different one.'})
    
@app.before_request
def before_request():
    g.cnx = mysql.connector.connect(
  host="localhost",
  user="myuser",
  password="mypassword",
)

    # g.cnx  = mysql.connector.connect(
    #     user='root', 
    #     password=os.getenv('MYSQL_ROOT_PASSWORD'),
    #     host='127.0.0.1',
    #     database=os.getenv('MYSQL_DATABASE'))
    
@app.after_request
def after_request(response):
    g.cnx.close()
    return response


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    # good luck 6/16/2023

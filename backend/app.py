from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageFont
from handright import Template, handwrite
from threading import Thread
from PIL import Image, ImageFont, ImageQt
from dotenv import load_dotenv
load_dotenv()
import os
import MySQLdb
from flask import g
import zipfile
import ast, io

app = Flask(__name__)

SECRET_KEY='437d75c5af744b76607fe862cf8a5a368519aca486d62c5fa69ba42c16809z88'
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

@app.route('/api/generate_handwriting', methods=['POST'])
def generate_handwriting():
    data = request.form
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
        fill_rgba = ast.literal_eval(data['fill']),
        fill = fill_rgba[:3],  # Ignore the alpha value
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
    cursor = g.db.cursor()

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
                g.db.commit()
            except:
                # 发生错误时回滚
                g.db.rollback()

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
    g.db  = MySQLdb.connect(
    host= os.getenv("HOST"),
    user=os.getenv("USERNAME"),
    passwd= os.getenv("PASSWORD"),
    db= os.getenv("DATABASE"),
    autocommit = True,
    ssl_mode = "VERIFY_IDENTITY",
    ssl      = {
    "ca": "/etc/ssl/certs/ca-certificates.crt"   #dokcer使用： ca": "/etc/ssl/cert.pem"  
    }
    )

@app.after_request
def after_request(response):
    g.db.close()
    return response


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    # good luck 6/16/2023

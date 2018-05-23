#!/usr/bin/env python
# __author__ = lvhuiyang

import os
import base64
from io import BytesIO
from uuid import uuid4

from celery import Celery
from flask import Flask, request
from redis import ConnectionPool, Redis
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

pool = ConnectionPool(host='localhost', port=6379, decode_responses=True)
client = Redis(connection_pool=pool)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "")


def make_uuid():
    return str(uuid4()).replace('-', '')


@celery.task
def handler(uuid, text):
    """
    图片处理函数
    :param uuid: 唯一id
    :param text: 输入的文字
    :return:
    """
    output = BytesIO()

    # im -> PIL 打开图片的实例对象
    im = Image.open("./source.jpeg")

    # font -> 字体对象，使用`华文细黑.ttf`是因为中文报错
    font = ImageFont.truetype(font="./华文细黑.ttf", size=40)

    # draw -> 画笔对象，并进行书写
    draw = ImageDraw.Draw(im)
    draw.text(xy=(40, 800), text=text, fill=(0, 0, 0, 0), font=font)

    # 保存，并以 base64 存储
    im.save(output, format="JPEG")
    im_data = output.getvalue()
    client.set(uuid, base64.b64encode(im_data))
    return True


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return '请在终端输入 <strong style="color: blue">' \
               'curl --data "text=要展示的文字（<21字符）&token=qc_token" ' \
               'sticker.lvhuiyang.cn </strong> 生成对应文字表情包\n'
    text = request.form.get('text')
    token = request.form.get('token')
    if text and token == ACCESS_TOKEN:
        if len(text) > 21:
            return 'text 长度超出 21 个字符\n'

        text_uuid = client.get(text)
        if text_uuid:
            return '生成地址: {}meme/{}/ \n'.format(request.url, text_uuid)
        else:
            new_uuid = make_uuid()
            client.set(text, new_uuid)
            client.set(new_uuid, "0")
            handler.delay(new_uuid, text)
            return '生成地址: {}meme/{}/ \n'.format(request.url, new_uuid)
    return '参数不正确. \n'


@app.route("/meme/<string:key>/", methods=['GET'])
def meme(key):
    value = client.get(key)

    if value is None:
        return '访问地址不存在或者已经过期.'
    elif value == "0":
        return '当你看到当前页面的时候说明图片正在生成，请等待几秒尝试刷新.'
    else:
        img_value = "data:image/jpeg;base64," + value
        return '<img src="{}" width="300"/>'.format(img_value)


if __name__ == '__main__':
    app.run(debug=True)

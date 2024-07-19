import base64
import os

from PIL import Image, ImageDraw, ImageFont
from typing import Tuple


def image_edition(
        image: Image.Image,
        text: str,
        font_family_path: str,
        font_size: int,
        color: Tuple[int, int, int],
        background_color: Tuple[int, int, int]
):
    """
    在图片下方嵌入文字
    :param image:
    :param text:增加在图片下方的文字
    :param font_family_path:字体文件的路径
    :param font_size:文字的大小
    :param color:文字颜色
    :param background_color:背景颜色
    :return:编辑完成的图片
    """
    imageHeight = image.height
    imageWidth = image.width
    imageWithChar = Image.new(
        'RGB',
        (imageWidth, imageHeight + font_size + 10),
        background_color)  # 新建图片，高度比原图增加font_size + 10，padding上下各5像素，放识别目标文字
    imageWithChar.paste(image, (0, 0))
    imageWithChar_drawable = ImageDraw.Draw(imageWithChar)
    font = ImageFont.truetype(font_family_path, font_size)
    imageWithChar_drawable.text(
        (5, imageHeight + 5),
        text,
        color,
        font
    )   # 横向x，纵向y，零点在左上角，position指定文字的左上角
    return imageWithChar


def image2base64(image: Image.Image):
    count = 0
    file_name = 'temp.jpg'
    if os.path.exists(file_name):
        count += 1
        file_name = 'temp{}.jpg'.format('_' + count)
    image.save(file_name)
    with open(file_name, 'rb') as file:
        image_base64 = base64.b64encode(file.read()).decode()
    os.remove(file_name)
    return image_base64

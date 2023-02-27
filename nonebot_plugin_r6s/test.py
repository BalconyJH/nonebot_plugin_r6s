from PIL import Image, ImageDraw, ImageFont
from textwrap import TextWrapper
from pathlib import Path

image = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
draw = ImageDraw.Draw(image)
RESOURCE_PATH = Path(__file__).parent
FONT = RESOURCE_PATH / "fonts" / "sarasa-mono-sc-nerd.ttc"
font_sizes = [46, 40, 32, 30, 24, 28, 24, 20]


class Font:
    def __init__(self, font_file, size: int):
        self.font = ImageFont.truetype(font_file, size)

    def __call__(self):
        return self.font


# 使用列表推导式生成字体对象
font_objects = {
    f"font_{size}": ImageFont.truetype(str(FONT), size) for size in font_sizes
}

# 通过名称访问相应的字体对象
font_46 = font_objects["font_46"]
font_40 = font_objects["font_40"]
font_32 = font_objects["font_32"]
font_30 = font_objects["font_30"]
font_24 = font_objects["font_24"]
font_28 = font_objects["font_28"]
font_20 = font_objects["font_20"]


text = """\
场均击杀最高段位当前段位助攻
胜率胜场负场游戏局数
爆头击倒破坏K/D"""

# 创建画布和字体
image = Image.new('RGB', (500, 500), color=(255, 255, 255))
draw = ImageDraw.Draw(image)

# 将文本拆分为行和单词
lines = text.split('\n')
words = [line.split() for line in lines]

# 计算文本的宽度和高度
line_height = font_20.getsize(lines[0])[1] + 70  # 行高为字体高度加上70
max_word_widths = [max(font_20.getsize(word)[0] for word in line) for line in words]
x_offsets = [sum(max_word_widths[:i]) + i * 20 for i in range(len(max_word_widths))]
y = 10

# 在画布上绘制文本
for i, line in enumerate(words):
    x = x_offsets[i]
    for word in line:
        draw.text((x, y), word, (150, 150, 150), font=font_20)
        x += max_word_widths[i] + 20
    y += line_height


image.show()

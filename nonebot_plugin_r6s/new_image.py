import asyncio
from io import BytesIO
from pathlib import Path
import time
from PIL.Image import Image
from PIL import Image as IMG
from PIL import ImageDraw, ImageFont, ImageOps, ImageFilter
import httpx
from typing import List, Union
import cProfile

from nonebot import logger

start_time = time.time()
AUTH = ("1749739643927884", "753a3649075db01a1100aade02713531")
proxies = {
    "http://": "http://localhost:10809",
    "https://": "http://localhost:10809",
}
RESOURCE_PATH = Path(__file__).parent
DEFAULT_AVATAR = RESOURCE_PATH / "imgs" / "default_avatar.png"
CACHE_PATH = RESOURCE_PATH / "cache"
FONT = RESOURCE_PATH / "fonts" / "sarasa-mono-sc-nerd.ttc"
font_sizes = [46, 40, 32, 30, 24, 28, 24, 20]


# class Font:
#     def __init__(self, font_file, size: int):
#         self.font = ImageFont.truetype(font_file, size)
#
#     def __call__(self):
#         return self.font
#
#
# # 使用列表推导式生成字体对象
# font_objects = {
#     f"font_{size}": ImageFont.truetype(str(FONT), size) for size in font_sizes
# }
#
# # 通过名称访问相应的字体对象
# font_46 = font_objects["font_46"]
# font_40 = font_objects["font_40"]
# font_32 = font_objects["font_32"]
# font_30 = font_objects["font_30"]
# font_24 = font_objects["font_24"]
# font_28 = font_objects["font_28"]
# font_20 = font_objects["font_20"]


def horizontal_linear_gradient(start_color, end_color, width, height) -> Image:
    """
    说明:
        生成线性渐变图片
    params:
        start_color: 起始颜色 (r, g, b)
        end_color: 结束颜色 (r, g, b)
        width: 图片宽度 (px)
        height: 图片高度 (px)
    """

    gradient_image = IMG.new("RGB", (width, height))
    step_r = (end_color[0] - start_color[0]) / width
    step_g = (end_color[1] - start_color[1]) / width
    step_b = (end_color[2] - start_color[2]) / width
    for per_pixel_of_width in range(width):
        bar_r = int(start_color[0] + step_r * per_pixel_of_width)
        bar_g = int(start_color[1] + step_g * per_pixel_of_width)
        bar_b = int(start_color[2] + step_b * per_pixel_of_width)
        for per_pixel_of_height in range(height):
            gradient_image.putpixel(
                (per_pixel_of_width, per_pixel_of_height), (bar_r, bar_g, bar_b)
            )
    return gradient_image


def sec_to_minsec(sec):
    minutes, _ = divmod(int(sec), 60)
    hours, minutes = divmod(int(minutes), 60)
    one_min = "%.2f" % (minutes / 60)
    return f"{hours:1d}.{one_min[2]}H"


# def smooth_image(image: Image, radius: float) -> Image:
#     """
#     平滑图片，消除锯齿效果
#     """
#     kernel_size = int(radius * 2) + 1
#     kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
#     image_array = np.array(image)
#     r = np.convolve(kernel, image_array[:, :, 0].flatten(), mode='same').reshape(image_array.shape[:2])
#     g = np.convolve(kernel, image_array[:, :, 1].flatten(), mode='same').reshape(image_array.shape[:2])
#     b = np.convolve(kernel, image_array[:, :, 2].flatten(), mode='same').reshape(image_array.shape[:2])
#     smoothed_array = np.stack([r, g, b], axis=-1)
#     smoothed_array = np.clip(smoothed_array, 0, 255).astype(np.uint8)
#     return IMG.fromarray(smoothed_array)


def circle_corner(img: Image, radii: List[int]) -> Image:
    """
    说明:
        图片圆角处理
    params:
        img: 图片
        radii: 圆角半径 (px) recommended: 20
    """
    if len(radii) == 1:
        radii *= 4
    elif radii is None:
        radii = [20] * 4

    alpha = IMG.new("L", img.size, 255)

    for i, corner in enumerate(
        [
            "upper_left_corner",
            "upper_right_corner",
            "lower_left_corner",
            "lower_right_corner",
        ]
    ):
        radius = radii[i]
        circle = IMG.new("L", (radius * 2, radius * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)

        if corner == "lower_left_corner":
            alpha.paste(
                circle.crop((0, radius, radius, radius * 2)), (0, img.height - radius)
            )
        elif corner == "lower_right_corner":
            alpha.paste(
                circle.crop((radius, radius, radius * 2, radius * 2)),
                (img.width - radius, img.height - radius),
            )
        elif corner == "upper_left_corner":
            alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
        elif corner == "upper_right_corner":
            alpha.paste(
                circle.crop((radius, 0, radius * 2, radius)), (img.width - radius, 0)
            )
    img = img.convert("RGBA")
    img.putalpha(alpha)
    img.filter(ImageFilter.SMOOTH_MORE)
    return img


def division_zero(a, b):
    return a / b if b else 0


def inverted_image(image):
    if image.mode != "RGBA":
        return ImageOps.invert(image)
    r, g, b, a = image.split()
    rgb_image = IMG.merge("RGB", (r, g, b))
    _inverted_image = ImageOps.invert(rgb_image)
    r2, g2, b2 = _inverted_image.split()
    return IMG.merge("RGBA", (r2, g2, b2, a))


async def get_pic(type: str, name: str):
    """
    获取图像。

    参数：
    type (str): 图像的类型，应为"operators"或"weapons"。
    name (str): 图像的名称或标识符。

    返回：
    Image: 图像的PIL.Image对象，如果获取失败返回None。

    示例：
    >>> get_pic("weapons", "ak47")
    <PIL.Image.Image image mode=RGBA size=...>
    """
    PICPATH = RESOURCE_PATH.joinpath(type, f"{name}.png")
    if PICPATH.exists():
        with PICPATH.open(mode="rb") as f:
            return IMG.open(f).convert("RGBA")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            if type == "operators":
                url = f"https://api.statsdb.net/r6/assets/operators/{name}/figure/small"
            elif type == "weapons":
                url = f"https://api.statsdb.net/r6/assets/weapons/{name}"
            else:
                return "Error"

            r = await client.get(url, timeout=10)
            r.raise_for_status()
        except (httpx.HTTPError, httpx.RequestError):
            print(f"Failed to download {type} image: {name}")
            return "Error"

    with PICPATH.open(mode="wb") as f:
        f.write(r.content)

    return IMG.open(BytesIO(r.content)).convert("RGBA")


def init_basic_info_image():
    """
    初始化背景图。
    """
    # 底图
    background = horizontal_linear_gradient((80, 80, 80), (40, 40, 40), 800, 635)
    draw = ImageDraw.Draw(background)

    # 战绩板背景
    record_background = IMG.new("RGB", (720, 380), (26, 27, 31))
    circle_record_background = circle_corner(record_background, [12])
    background.paste(circle_record_background, (40, 215), circle_record_background)

    # 预设内容
    draw.text((80, 250), "全局统计", "white", font_30)
    text_info = """\
    场均击杀          击杀              死亡              助攻
    胜率              胜场              负场              游戏局数
    爆头              击倒              破坏              K/D"""
    draw.text((85, 310), text_info, (150, 150, 150), font_20, spacing=70)

    # 默认头像
    default_avatar = IMG.open(DEFAULT_AVATAR)
    default_avatar.thumbnail((128, 128))
    background.paste(circle_corner(default_avatar, [20]), (40, 40), default_avatar)

    background.save(CACHE_PATH.joinpath("background.png"))


async def draw_r6(nick_name: str):
    # 背景图
    # background = horizontal_linear_gradient((80, 80,80), (40,40,40), 800, 635)
    # draw = ImageDraw.Draw(background)
    # # 战绩板背景
    # record_background = IMG.new("RGB", (720, 380), (26, 27, 31))
    # circle_record_background = circle_corner(record_background, [12])
    # background.paste(circle_record_background, (40, 215), circle_record_background)
    # # 预设内容
    # draw.text((80, 250), "全局统计", "white", font_30)
    # text_info = """\
    # 场均击杀          击杀              死亡              助攻
    # 胜率              胜场              负场              游戏局数
    # 爆头              击倒              破坏              K/D"""
    # draw.text((85, 310), text_info, (150, 150, 150), font_20, spacing=70)
    # 用户基本信息

    # for _ in range(3):
    #     try:
    #         async with httpx.AsyncClient() as client:
    #             avatar = await client.get(data["payload"]["user"]["avatar"], timeout=15)
    #         if avatar.status_code == 200:
    #             avatar = IMG.open(BytesIO(avatar.content))
    #             avatar.thumbnail((128, 128))
    #             circle_avatar = circle_corner(avatar, [20])
    #             background.paste(circle_avatar, (40, 40), circle_avatar)
    #             break
    #         if avatar.status_code == 429:
    #             logger.warning("达到api limit")
    #         else:
    #             # logger.error(f"头像下载失败：{nick_name}")
    #             continue
    #     except httpx.HTTPError:
    #         default_avatar = IMG.open(RESOURCE_PATH.joinpath("default_avatar.png"))
    #         avatar.thumbnail((128, 128))
    #         circle_avatar = circle_corner(avatar, [20])
    #         background.paste(circle_avatar, (40, 40), circle_avatar)
    #         print(f"头像下载失败：{nick_name}")
    draw.text(
        (220, 50),
        data["payload"]["user"]["nickname"],
        "white",
        font_46,
    )
    level = data["payload"]["stats"]["progression"]["level"]
    time = sec_to_minsec(data["payload"]["stats"]["general"]["timeplayed"])
    mmr = data["payload"]["stats"]["seasonal"]["ranked"]["mmr"]
    draw.text(
        (222, 115),
        f"Level {level}   Playtime {time}   MMR {mmr}",
        (200, 200, 200),
        font_28,
    )
    # # 战绩板
    # record_background = IMG.new("RGB", (720, 380), (26, 27, 31))
    # circle_record_background = circle_corner(record_background, [12])
    # background.paste(circle_record_background, (40, 215), circle_record_background)
    draw.text((80, 250), "全局统计", "white", font_30)
    text_info = """\
    场均击杀          击杀              死亡              助攻
    胜率              胜场              负场              游戏局数
    爆头              击倒              破坏              K/D"""
    draw.text((85, 310), text_info, (150, 150, 150), font_20, spacing=70)

    kpm = "%.2f" % division_zero(
        data["payload"]["stats"]["general"]["kills"],
        data["payload"]["stats"]["general"]["matchesplayed"],
    )
    draw.text((180 * 1 - 96, 340), kpm, "white", font_32)
    draw.text(
        (180 * 2 - 94, 340),
        str(data["payload"]["stats"]["general"]["kills"]),
        "white",
        font_32,
    )
    draw.text(
        (180 * 3 - 95, 340),
        str(data["payload"]["stats"]["general"]["deaths"]),
        "white",
        font_32,
    )
    draw.text(
        (180 * 4 - 94, 340),
        str(data["payload"]["stats"]["general"]["assists"]),
        "white",
        font_32,
    )

    wl = "%.2f%%" % (
        data["payload"]["stats"]["general"]["wins"]
        / data["payload"]["stats"]["general"]["matchesplayed"]
        * 100
    )
    draw.text((180 * 1 - 96, 432), wl, "white", font_32)
    draw.text(
        (180 * 2 - 94, 432),
        str(data["payload"]["stats"]["general"]["wins"]),
        "white",
        font_32,
    )
    draw.text(
        (180 * 3 - 95, 432),
        str(data["payload"]["stats"]["general"]["losses"]),
        "white",
        font_32,
    )
    draw.text(
        (180 * 4 - 94, 432),
        str(data["payload"]["stats"]["general"]["matchesplayed"]),
        "white",
        font_32,
    )

    kd = "%.2f" % division_zero(
        data["payload"]["stats"]["general"]["kills"],
        data["payload"]["stats"]["general"]["deaths"],
    )
    draw.text(
        (180 * 1 - 96, 520),
        str(data["payload"]["stats"]["general"]["headshots"]),
        "white",
        font_32,
    )
    draw.text(
        (180 * 2 - 94, 520),
        str(data["payload"]["stats"]["general"]["dbno"]),
        "white",
        font_32,
    )
    draw.text(
        (180 * 3 - 95, 520),
        str(data["payload"]["stats"]["general"]["gadgetdestroy"]),
        "white",
        font_32,
    )
    draw.text((180 * 4 - 94, 520), kd, "white", font_32)

    # # 常用干员
    # most_played = sorted(
    #     data["payload"]["stats"]["operators"].copy(),
    #     key=lambda l1: l1["timeplayed"],
    #     reverse=True,
    # )[0]
    # best_kd = sorted(
    #     data["payload"]["stats"]["operators"].copy(),
    #     key=lambda l2: (division_zero(l2["kills"], l2["deaths"]), l2["timeplayed"]),
    #     reverse=True,
    # )[0]
    # best_wl = sorted(
    #     data["payload"]["stats"]["operators"].copy(),
    #     key=lambda l3: (division_zero(l3["wins"], l3["losses"]), l3["timeplayed"]),
    #     reverse=True,
    # )[0]

    # operator_box1 = IMG.new("RGB", (215, 450), (72, 140, 222))
    # operator_box2 = IMG.new("RGB", (215, 450), (66, 127, 109))
    # operator_box3 = IMG.new("RGB", (215, 450), (212, 134, 30))
    # operator_figure1 = await get_pic("operators", most_played["id"])
    # operator_figure2 = await get_pic("operators", best_kd["id"])
    # operator_figure3 = await get_pic("operators", best_wl["id"])
    # if operator_figure1 == "Error":
    #     operator_figure1 = IMG.open("assets/operators/unknown.png")
    # if operator_figure2 == "Error":
    #     operator_figure2 = IMG.open("assets/operators/unknown.png")
    # if operator_figure3 == "Error":
    #     operator_figure3 = IMG.open("assets/operators/unknown.png")
    # operator_figure1.thumbnail((600, 850))
    # operator_figure2.thumbnail((600, 850))
    # operator_figure3.thumbnail((600, 850))
    # operator_box1.paste(operator_figure1, (-145, 75), operator_figure1)
    # operator_box2.paste(operator_figure2, (-145, 75), operator_figure2)
    # operator_box3.paste(operator_figure3, (-145, 75), operator_figure3)
    # circle_operator_box1 = circle_corner(operator_box1, [12])
    # circle_operator_box2 = circle_corner(operator_box2, [12])
    # circle_operator_box3 = circle_corner(operator_box3, [12])
    # background.paste(circle_operator_box1, (40, 635), circle_operator_box1)
    # background.paste(circle_operator_box2, (294, 635), circle_operator_box2)
    # background.paste(circle_operator_box3, (545, 635), circle_operator_box3)

    # draw.text((65, 652), "时长最长", "white", font_40)
    # draw.text((319, 652), "最佳战绩", "white", font_40)
    # draw.text((571, 652), "最佳胜率", "white", font_40)

    # draw.text((66, 705), most_played["id"].upper(), "white", font_24)
    # draw.text((320, 705), best_kd["id"].upper(), "white", font_24)
    # draw.text((572, 705), best_wl["id"].upper(), "white", font_24)

    # draw.text((65, 737), sec_to_minsec(most_played["timeplayed"]), "white", font_32)
    # draw.text(
    #     (319, 737),
    #     str(
    #         "%.2f"
    #         % division_zero(
    #             best_kd["kills"], best_kd["deaths"] if best_kd["deaths"] != 0 else 1
    #         )
    #     ),
    #     "white",
    #     font_32,
    # )
    # draw.text(
    #     (571, 737),
    #     str("%.2f%%" % (division_zero(best_wl["wins"], best_wl["roundsplayed"]) * 100)),
    #     "white",
    #     font_32,
    # )

    # 常用武器
    weapon_background = IMG.new("RGB", (720, 330), (26, 27, 31))
    circle_weapon_background = circle_corner(weapon_background, [12])
    background.paste(circle_weapon_background, (40, 1130), circle_weapon_background)
    draw.text((80, 1165), "最常用的武器", "white", font_30)

    weapons = sorted(
        data["payload"]["stats"]["weaponDetails"].copy(),
        key=lambda lilt: lilt["kills"],
        reverse=True,
    )[0]
    weapons_image = await get_pic("weapons", weapons["key"])
    if weapons_image == "Error":
        weapons_image = IMG.open("assets/weapons/unknown.png")
    weapons_image_inverted = inverted_image(weapons_image)
    background.paste(
        weapons_image_inverted,
        (550 - (weapons_image.size[0] // 2), 1265 - (weapons_image.size[1] // 2)),
        weapons_image_inverted,
    )

    weapon_name_x, _ = font_40.getsize(weapons["name"])
    draw.text((330 - weapon_name_x, 1235), weapons["name"], "white", font_40)

    weapon_kd = "%.2f" % division_zero(
        weapons["kills"], weapons["deaths"] if weapons["deaths"] != 0 else 1
    )
    draw.text((170, 1345), "击杀            爆头            K/D", (150, 150, 150), font_24)
    draw.text((172, 1380), str(weapons["kills"]), "white", font_32)
    draw.text((364, 1380), str(weapons["headshots"]), "white", font_32)
    draw.text((554, 1380), str(weapon_kd), "white", font_32)

    bio = BytesIO()
    background.save(bio, "JPEG")

    return background.show()


def main():
    loop = asyncio.get_event_loop()
    task = draw_r6(nick_name="GChen.Rainbow.5")
    loop.run_until_complete(task)
    end_time = time.time()
    print(f"{(end_time - start_time): .2f}")


# 性能测试方法
# if __name__ == "__main__":
#     cProfile.run("main()")

if __name__ == "__main__":
    main()

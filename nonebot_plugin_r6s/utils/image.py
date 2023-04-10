# import time
import base64
import contextlib
from io import BytesIO
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from PIL.ImageDraw import ImageDraw as ImageDraw

from .player import Player, CRStat, rank, SeasonRanks

RESOURCE_PATH = Path(__file__).parent

ImageS_PATH = Path(__file__).parent / "Images"
GEN_WAN_MIN = ImageFont.truetype(
    str(Path(__file__).parent / "fonts" / "GenYoMin-M.ttc"), 60
)
GEN_WAN_MIN_S = ImageFont.truetype(
    str(Path(__file__).parent / "fonts" / "GenYoMin-M.ttc"), 40
)
DEFAULT_AVATAR = RESOURCE_PATH / "Images" / "default_avatar.png"
CACHE_PATH = RESOURCE_PATH / "cache"
FONT = RESOURCE_PATH / "fonts" / "font.ttc"
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


def rank_Image_path(rank: int) -> str:
    return str((ImageS_PATH / "ranks" / f"r{rank}.png").resolve())


def operator_Image_path(operator: str) -> str:
    return str((ImageS_PATH / "operators" / f"{operator}.png").resolve())


def avatar_Image_path() -> str:
    return str((ImageS_PATH / "avatar" / "default_146_146.png").resolve())


def paste_with_alpha(image: Image, Image: Image, pos: tuple) -> None:
    Image_alpha = Image.split()[3]
    image.paste(Image, pos, Image_alpha)


def encode_b64(Image: Image) -> str:
    Image_io = BytesIO()
    Image.save(Image_io, "PNG")
    return base64.b64encode(Image_io.getvalue()).decode()


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

    gradient_image = Image.new("RGB", (width, height))
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


def circle_corner(image: Image, radii: List[int]) -> Image:
    """
    说明:
        图片圆角处理
    params:
        Image: 图片
        radii: 圆角半径 (px) recommended: 20
    """
    if len(radii) == 1:
        radii *= 4
    elif radii is None:
        radii = [20] * 4

    alpha = image.new("L", image.size, 255)

    for i, corner in enumerate(
            [
                "upper_left_corner",
                "upper_right_corner",
                "lower_left_corner",
                "lower_right_corner",
            ]
    ):
        radius = radii[i]
        circle = image.new("L", (radius * 2, radius * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)

        if corner == "lower_left_corner":
            alpha.paste(
                circle.crop((0, radius, radius, radius * 2)), (0, image.height - radius)
            )
        elif corner == "lower_right_corner":
            alpha.paste(
                circle.crop((radius, radius, radius * 2, radius * 2)),
                (image.width - radius, image.height - radius),
            )
        elif corner == "upper_left_corner":
            alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
        elif corner == "upper_right_corner":
            alpha.paste(
                circle.crop((radius, 0, radius * 2, radius)), (image.width - radius, 0)
            )
    image = image.convert("RGBA")
    image.putalpha(alpha)
    image.filter(ImageFilter.SMOOTH_MORE)
    return Image


def init_basic_info_image():
    """
    初始化背景图。
    """
    # 底图
    background = horizontal_linear_gradient((80, 80, 80), (40, 40, 40), 800, 635)
    draw = ImageDraw.Draw(background)

    # 战绩板背景
    record_background = Image.new("RGB", (720, 380), (26, 27, 31))
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
    default_avatar = Image.open(DEFAULT_AVATAR)
    default_avatar.thumbnail((128, 128))
    background.paste(circle_corner(default_avatar, [20]), (40, 40), default_avatar)

    background.save(CACHE_PATH.joinpath("background.png"))


async def draw_head(image: Image, player: Player, title: str) -> ImageDraw:
    with contextlib.suppress(ConnectionError):
        avatar_image = await player.get_avatar()
    if avatar_image is not None:
        avatar_data = BytesIO(avatar_image)
        avatar = Image.open(avatar_data).convert("RGBA").resize((110, 110))
    else:
        avatar = Image.open(avatar_Image_path()).resize((110, 110))

    paste_with_alpha(Image, avatar, (40, 40))
    draw = ImageDraw.Draw(image)
    draw.text((200, 20), player.username, fill="black", font=GEN_WAN_MIN)
    draw.text((200, 100), title, fill="black", font=GEN_WAN_MIN)
    return draw


async def base_image(player: Player) -> Image:
    image = Image.new("RGBA", (800, 420), color="white")
    draw = await draw_head(image, player, "基础信息")

    ranked_mmr = "-" if player.ranked_stat is None else player.ranked_stat.mmr
    ranked_time = (
        "-" if player.ranked_stat is None else player.ranked_stat.timePlayed // 3600
    )

    draw.multiline_text(
        (20, 190),
        f"等级: {player.level()}\n"
        f"总局数: {player.gerneral_stat.played}\n"
        f"总时长: {player.gerneral_stat.timePlayed / 3600:.2f}\n"
        f"赛季排位MMR: {str(ranked_mmr).split('.')[0]}",
        fill="black",
        font=GEN_WAN_MIN_S,
        spacing=20,
    )
    draw.multiline_text(
        (415, 190),
        f"总KD: {player.gerneral_stat.kd()}\n"
        f"总胜率: {player.gerneral_stat.win_rate()}\n"
        f"排位时长: {ranked_time}\n"
        f"赛季非排MMR: {str(player.casual_stat.mmr).split('.')[0]}",
        fill="black",
        font=GEN_WAN_MIN_S,
        spacing=20,
    )

    return image


async def detail_image(player: Player) -> Image:
    def draw_rank(
                Image: Image, draw: ImageDraw, stat: CRStat, offset: int, has_rank: bool = False
        ):
        ranked_rank = (
            Image.open(
                rank_Image_path(rank(player.history_max_mmr_season["max_mmr"]))
            ).resize((150, 150))
            if has_rank
            else Image.open(rank_Image_path(rank(stat.mmr))).resize((150, 150))
        )

        paste_with_alpha(Image, ranked_rank, (20, offset + 20))
        # draw.rounded_rectangle(
        #     [10, offset + 10, 790, offset + 190], radius=5, outline='black', width=2)
        if not has_rank:
            draw.multiline_text(
                (190, offset + 20),
                f"赛季MMR: {str(stat.mmr).split('.')[0]}\n"
                f"KD:  {stat.kd()}\n"
                f"胜率：{stat.win_rate()}",
                fill="black",
                font=GEN_WAN_MIN_S,
                spacing=20,
            )
            draw.multiline_text(
                (510, offset + 20),
                f"局数: {stat.played}\n" + f"时长: {stat.timePlayed / 3600:.2f}",
                # + (f"\n历史最高MMR: {int(player.history_max_mmr)}" if has_rank else ""),
                fill="black",
                font=GEN_WAN_MIN_S,
                spacing=20,
            )
        else:
            draw.multiline_text(
                (190, offset + 20),
                f"历史最高MMR: {str(player.history_max_mmr_season['max_mmr']).split('.')[0]}\n"
                f"赛季最终MMR: {str(player.history_max_mmr_season['mmr']).split('.')[0]}\n"
                f"胜场：{player.history_max_mmr_season['wins']}",
                fill="black",
                font=GEN_WAN_MIN_S,
                spacing=20,
            )
            draw.multiline_text(
                (510, offset + 20),
                f"\n\n" + f"败场: {player.history_max_mmr_season['losses']}",
                fill="black",
                font=GEN_WAN_MIN_S,
                spacing=20,
            )

    image = Image.new("RGBA", (900, 940 if player.ranked_stat else 440), color="white")
    draw = await draw_head(image, player, "详细信息")
    str_len = GEN_WAN_MIN_S.getsize("— 非排数据 —")[0]
    draw.text((400 - str_len // 2, 190), "— 非排数据 —", fill="black", font=GEN_WAN_MIN_S)
    draw_rank(image, draw, player.casual_stat, 240)
    if player.ranked_stat is not None:
        str_len = GEN_WAN_MIN_S.getsize("— 排位数据 —")[0]
        draw.text(
            (400 - str_len // 2, 440), "— 排位数据 —", fill="black", font=GEN_WAN_MIN_S
        )
        draw_rank(image, draw, player.ranked_stat, 490)
    str_len = GEN_WAN_MIN_S.getsize("- 最高段位数据 -")[0]
    draw.text(
        (400 - str_len // 2, 690 if player.ranked_stat is not None else 440),
        "- 最高段位数据 -",
        fill="black",
        font=GEN_WAN_MIN_S,
    )
    draw_rank(
        image,
        draw,
        player.ranked_stat,
        740 if player.ranked_stat is not None else 540,
        True,
    )

    return image


async def plays_image(player: Player) -> Image:
    """
    暂时不需要近期对战了
    :param player:
    :return:
    """

    # def draw_play(draw: ImageDraw, stat: CRStat, offset: int):
    #     timestr = time.strftime(
    #         "%Y-%m-%d %H:%M", time.localtime(stat.time/1000))
    #     draw.text((20, offset + 20), timestr,
    #               fill='black', font=GEN_WAN_MIN_S)
    #     draw.multiline_text(
    #         (20, offset + 70),
    #         f"局数: {stat.played}\n"
    #         f"时长: {stat.timePlayed / 3600:.2f}",
    #         fill='black', font=GEN_WAN_MIN_S, spacing=20)
    #     draw.multiline_text(
    #         (400, offset + 70),
    #         f"KD: {stat.kd()}\n"
    #         f"胜率: {stat.win_rate()}",
    #         fill='black', font=GEN_WAN_MIN_S, spacing=20)
    #
    # image = Image.new('RGBA', (800, 900), color='white')
    # draw = await draw_head(image, player, "近期对战")
    # for (i, stat) in enumerate(player.recent_stat):
    #     draw_play(draw, stat, 190 + i * 170)
    #     if i >= 3:
    #         break
    #
    # return image

    def draw_play(Image: Image, draw: ImageDraw, stat: SeasonRanks, offset: int):
        ranked_rank = Image.open(rank_Image_path(rank(stat.mmr))).resize((150, 150))
        paste_with_alpha(Image, ranked_rank, (20, offset + 20))

        draw.multiline_text(
            (190, offset + 70),
            f"胜场: {stat.wins}\n" f"最终MMR: {str(stat.mmr).split('.')[0]}",
            fill="black",
            font=GEN_WAN_MIN_S,
            spacing=20,
        )
        draw.multiline_text(
            (495, offset + 70),
            f"败场: {stat.losses}\n" f"最高MMR: {str(stat.max_mmr).split('.')[0]}",
            fill="black",
            font=GEN_WAN_MIN_S,
            spacing=20,
        )

    image = Image.new(
        "RGBA",
        (
            990,
            player.season_rank.__len__() * 240
            if player.season_rank.__len__() > 3
            else 700,
        ),
        color="white",
    )
    draw = await draw_head(image, player, "历史段位")
    for (i, stat) in enumerate(player.season_rank):
        season = stat.get_season()
        len_ = GEN_WAN_MIN_S.getsize(f"— {season} —")[0]
        draw.text(
            (400 - len_ // 2, 200 * (i + 1)),
            f"— {season} —",
            fill="black",
            font=GEN_WAN_MIN_S,
        )
        draw_play(image, draw, stat, 190 + i * 200)

    return image


# async def operators_Image(player: Player) -> Image:
#     def draw_operator(
#             Image: Image, draw: ImageDraw, operator: OperatorStat, offset: int, second: bool
#     ):
#         operator_Image = Image.open(operator_Image_path(operator.name)).resize((170, 170))
#         paste_with_alpha(Image, operator_Image, (400 if second else 10, offset + 10))
#         draw.multiline_text(
#             (570 if second else 190, offset + 20),
#             f"时长: {operator.timePlayed / 3600:.1f}\n"
#             f"KD: {operator.kd()}\n"
#             f"胜率: {operator.win_rate()}",
#             fill="black",
#             font=GEN_WAN_MIN_S,
#             spacing=20,
#         )
#
#     Image = Image.new("RGBA", (800, 1600), color="white")
#     draw = await draw_head(Image, player, "干员信息")
#     for (i, operator) in enumerate(player.operator_stat):
#         draw_operator(Image, draw, operator, 190 + i // 2 * 200, i % 2 != 0)
#         if i >= 13:
#             break
#
#     return Image

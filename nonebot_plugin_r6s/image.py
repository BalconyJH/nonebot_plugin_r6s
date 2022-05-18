from .player import Player, CRStat, rank, OperatorStat, SeasonRanks
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as IMG
from PIL.ImageDraw import ImageDraw as IMGDraw
from io import BytesIO
from pathlib import Path
# import time
import base64

RESOURCE_PATH = Path(__file__).parent

IMGS_PATH = Path(__file__).parent / "imgs"
GEN_WAN_MIN = ImageFont.truetype(
    str(Path(__file__).parent / "fonts" / "GenYoMin-M.ttc"), 60
)
GEN_WAN_MIN_S = ImageFont.truetype(
    str(Path(__file__).parent / "fonts" / "GenYoMin-M.ttc"), 40
)


def rank_img_path(rank: int) -> str:
    return str((IMGS_PATH / "ranks" / f"r{rank}.png").resolve())


def operator_img_path(operator: str) -> str:
    return str((IMGS_PATH / "operators" / f"{operator}.png").resolve())


def avatar_img_path() -> str:
    return str((IMGS_PATH / "avatar" / "default_146_146.png").resolve())


def paste_with_alpha(image: IMG, img: IMG, pos: tuple) -> None:
    img_alpha = img.split()[3]
    image.paste(img, pos, img_alpha)


def encode_b64(img: IMG) -> str:
    img_io = BytesIO()
    img.save(img_io, "PNG")
    return base64.b64encode(img_io.getvalue()).decode()


async def draw_head(img: IMG, player: Player, title: str) -> IMGDraw:
    avatar_img = None
    try:
        avatar_img = await player.get_avatar()
    except:
        pass
    avatar = None
    if avatar_img is not None:
        avatar_data = BytesIO(avatar_img)
        avatar = Image.open(avatar_data).convert("RGBA").resize((110, 110))
    else:
        avatar = Image.open(avatar_img_path()).resize((110, 110))

    paste_with_alpha(img, avatar, (40, 40))
    draw = ImageDraw.Draw(img)
    draw.text((200, 20), player.username, fill="black", font=GEN_WAN_MIN)
    draw.text((200, 100), title, fill="black", font=GEN_WAN_MIN)
    return draw


async def base_image(player: Player) -> IMG:
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


async def detail_image(player: Player) -> IMG:
    def draw_rank(
            img: IMG, draw: IMGDraw, stat: CRStat, offset: int, has_rank: bool = False
    ):
        ranked_rank = (
            Image.open(rank_img_path(rank(stat.mmr))).resize((150, 150))
            if not has_rank
            else Image.open(
                rank_img_path(rank(player.history_max_mmr_season["max_mmr"]))
            ).resize((150, 150))
        )
        paste_with_alpha(img, ranked_rank, (20, offset + 20))
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


async def plays_image(player: Player) -> IMG:
    """
    暂时不需要近期对战了
    :param player:
    :return:
    """

    # def draw_play(draw: IMGDraw, stat: CRStat, offset: int):
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

    def draw_play(img: IMG, draw: IMGDraw, stat: SeasonRanks, offset: int):
        ranked_rank = Image.open(rank_img_path(rank(stat.mmr))).resize((150, 150))
        paste_with_alpha(img, ranked_rank, (20, offset + 20))

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


async def operators_img(player: Player) -> IMG:
    def draw_operator(
            img: IMG, draw: IMGDraw, operator: OperatorStat, offset: int, second: bool
    ):
        operator_img = Image.open(operator_img_path(operator.name)).resize((170, 170))
        paste_with_alpha(img, operator_img, (400 if second else 10, offset + 10))
        draw.multiline_text(
            (570 if second else 190, offset + 20),
            f"时长: {operator.timePlayed / 3600:.1f}\n"
            f"KD: {operator.kd()}\n"
            f"胜率: {operator.win_rate()}",
            fill="black",
            font=GEN_WAN_MIN_S,
            spacing=20,
        )

    img = Image.new("RGBA", (800, 1600), color="white")
    draw = await draw_head(img, player, "干员信息")
    for (i, operator) in enumerate(player.operator_stat):
        draw_operator(
            img, draw, operator, 190 + i // 2 * 200, False if i % 2 == 0 else True
        )
        if i >= 13:
            break

    return img

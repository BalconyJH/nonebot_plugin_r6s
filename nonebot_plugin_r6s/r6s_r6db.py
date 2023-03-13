from io import BytesIO
from pathlib import Path
import httpx
from PIL import Image as IMG
from nonebot.log import logger

BASEPATH = Path(__file__).parent
DATABASE = BASEPATH.joinpath("data")
DATABASE.joinpath("operators").mkdir(parents=True, exist_ok=True)
DATABASE.joinpath("weapons").mkdir(parents=True, exist_ok=True)

def rank(mmr: int) -> str:
    """
    根据给定的MMR值，返回对应的段位名称。

    参数：
    mmr (int): 表示玩家MMR值的整数。

    返回：
    str: 玩家对应的段位名称。
    """
    if mmr < 0:
        return "紫铜V"
    head = ["紫铜", "黄铜", "白银", "黄金", "白金", "钻石", "冠军"]
    if mmr < 2600:
        feet1 = ["V", "IV", "III", "II", "I"]
        tier = mmr // 100 - 11
        if tier < 5:
            return head[0] + feet1[tier]
        elif tier < 10:
            return head[1] + feet1[tier - 5]
        else:
            return head[2] + feet1[tier - 10]
    elif mmr < 4400:
        feet2 = ["III", "II", "I"]
        tier = mmr // 200 - 13
        return head[3] + feet2[tier] if tier < 3 else head[4] + feet2[(tier - 3) // 2]
    elif mmr < 5000:
        return head[-2]
    else:
        return head[-1]



async def get_picture(picture_type: str, name: str):
    """
    从本地或者网络中获取图片。

    参数：
    picture_type (str): 图片的类型，应为"operators"或"weapons"。
    name (str): 图片的名称或标识符。

    返回：
    Image: 图片的PIL.Image对象，如果获取失败返回None。

    示例：
    >>> get_picture("weapons", "ak47")
    <PIL.Image.Image image mode=RGBA size=...>
    """
    PICPATH = DATABASE / picture_type / f"{name}.png"
    if PICPATH.exists():
        with PICPATH.open(mode='rb') as f:
            return IMG.open(f).convert("RGBA")

    async with httpx.AsyncClient(timeout=10) as client:
        url = f"https://api.statsdb.net/r6/assets/{picture_type}/{name}"
        if picture_type == "operators":
            url += "/figure/small"
        try:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
        except (httpx.HTTPError, httpx.RequestError):
            logger.error(f"Failed to download {picture_type} image: {name}")
            return None

    with PICPATH.open(mode='wb') as f:
        f.write(response.content)

    logger.info(f"Downloaded image: {picture_type} - {name}")
    return IMG.open(BytesIO(response.content)).convert("RGBA")


async def get_user_avatar_picture(data: dict):
    """
    获取用户的头像图片。

    参数：
    data (dict): 用户的基本信息。

    返回：
    Image: 用户的头像图片，如果获取失败返回None。

    示例：
    >>> get_user_avatar_picture(data)
    <PIL.Image.Image image mode=RGBA size=...>
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(data["payload"]["user"]["avatar"], timeout=15)
            response.raise_for_status()
        return IMG.open(BytesIO(response.content)).convert("RGBA")
    except (httpx.HTTPError, httpx.RequestError) as e:
        logger.error(f"Failed to download user avatar image: {e}")
        return None



def second_to_miniutesecond(seconds: int) -> str:
    """
    将秒数转换为格式化的分钟和秒数。

    参数：
    sec：要转换的秒数，可以是整数或浮点数。

    返回：
    格式化的分钟和秒数的字符串，格式为“H.MM”。

    示例：
    >>> sec_to_minsec(3600)
    '1.00H'
    >>> sec_to_minsec(1500)
    '0.25H'
    """
    minutes, _ = divmod(seconds, 60)
    hours, minutes = divmod(int(minutes), 60)
    one_min = "%.2f" % (minutes / 60)
    return f"{hours:1d}.{one_min[2]}H"


def division_zero(a, b):
    return a / b if b else 0


async def basicinfo(data: dict) -> dict:
    return {
        "nickname": data["payload"]["user"]["nickname"],
        "level": data["payload"]["stats"]["progression"]["level"],
        "time": second_to_miniutesecond(
            data["payload"]["stats"]["general"]["timeplayed"]
        ),
        "mmr": data["payload"]["stats"]["seasonal"]["ranked"]["mmr"],
    }


async def get_record(data: dict) -> dict:
    """
    获取用户的基本信息

    参数：
    data：用户的基本信息

    返回：
    用户的基本信息

    示例：
    >>> get_record(data)
    {'kills': 0, 'deaths': 0, 'matchesplayed': 0, 'assists': 0, 'wins': 0, 'losses': 0, 'kd': 0.0, 'wl': '0.00', 'kpm': '0.00', 'knockdown': 0, 'gadget_destroy': 0}
    """
    general_stats = data["payload"]["stats"]["general"]
    kills, deaths, matchesplayed, assists, wins, losses, knockdown, gadget_destroy = (
        general_stats["kills"],
        general_stats["deaths"],
        general_stats["matchesplayed"],
        general_stats["assists"],
        general_stats["wins"],
        general_stats["losses"],
        general_stats["knockdown"],
        general_stats["gadget_destroy"],
    )

    kd = division_zero(kills, deaths)
    wl = division_zero(wins, losses)
    kpm = division_zero(kills, matchesplayed)

    return {
        "kills": kills,
        "deaths": deaths,
        "matchesplayed": matchesplayed,
        "assists": assists,
        "wins": wins,
        "losses": losses,
        "kd": kd,
        "wl": "%.2f" % wl,
        "kpm": "%.2f" % kpm,
        "knockdown": knockdown,
        "gadget_destroy": gadget_destroy,
    }


async def get_operator(data: dict) -> dict:
    operators = data["payload"]["stats"]["operators"].copy()
    most_played = sorted(operators, key=lambda l1: l1["timeplayed"], reverse=True)[0]
    best_kd = sorted(
        operators,
        key=lambda l2: (division_zero(l2["kills"], l2["deaths"]), l2["timeplayed"]),
        reverse=True,
    )[0]
    best_wl = sorted(
        operators,
        key=lambda l3: (division_zero(l3["wins"], l3["losses"]), l3["timeplayed"]),
        reverse=True,
    )[0]
    return {
        "most_played": most_played,
        "best_kd": best_kd,
        "best_wl": best_wl,
    }
# def con(*args) -> str:
#     r = "".join(arg + "\n" for arg in args)
#     return r[:-1]


def get_weapon_details(data: dict) -> dict:
    """
    从给定的数据中提取用户的最佳武器信息。

    参数：
    data (dict)：包含用户游戏统计数据的字典，应包含以下键：
        - "weaponDetails" (list): 包含不同武器的字典列表，每个字典应包含以下键：
            - "name" (str): 武器的名称。
            - "key" (str): 武器的标识符。
            - "kills" (int): 武器的击杀数。
            - "headshots" (int): 武器的爆头数。
            - "deaths" (int): 武器的死亡数。

    返回：
    dict：包含用户最佳武器的字典，应包含以下键：
        - "name" (str): 武器的名称。
        - "key" (str): 武器的标识符。
        - "kills" (int): 武器的击杀数。
        - "headshots" (int): 武器的爆头数。
        - "deaths" (int): 武器的死亡数。
        - "kd" (float): 武器的击杀/死亡比，四舍五入到小数点后两位。

    示例：
    >>> get_weapon_details(data)
    {'name': 'AK-47', 'key': 'ak47', 'kills': 500, 'headshots': 300, 'deaths': 200, 'kd': 2.5}
    """
    weapons = sorted(
        data["payload"]["stats"]["weaponDetails"].copy(),
        key=lambda lilt: lilt["kills"],
        reverse=True,
    )[0]

    weapon_kd = division_zero(weapons["kills"], weapons["deaths"] if weapons["deaths"] != 0 else 1)
    weapon_kd = round(weapon_kd, 2)

    return {
        "name": weapons["name"],
        "key": weapons["key"],
        "kills": weapons["kills"],
        "headshots": weapons["headshots"],
        "deaths": weapons["deaths"],
        "kd": weapon_kd,
    }


# def gen_stat(data: dict) -> str:
#     return con(
#         "KD：%.2f"
#         % (
#                 data["payload"]["stats"]["general"]["kills"]
#                 / data["payload"]["stats"]["general"]["deaths"]
#         )
#         if data["payload"]["stats"]["general"]["deaths"] != 0
#         else (
#                 "KD：%d/%d"
#                 % (
#                     data["payload"]["stats"]["general"]["kills"],
#                     data["payload"]["stats"]["general"]["deaths"],
#                 )
#         ),
#         "胜负比：%.2f"
#         % (
#                 data["payload"]["stats"]["general"]["wins"]
#                 / data["payload"]["stats"]["general"]["losses"]
#         )
#         if data["payload"]["stats"]["general"]["losses"] != 0
#         else (
#                 "胜负比：%d/%d"
#                 % (
#                     data["payload"]["stats"]["general"]["wins"],
#                     data["payload"]["stats"]["general"]["losses"],
#                 )
#         ),
#         "总场数：%d" % data["played"],
#         "游戏时长：%.1f" % (data["timePlayed"] / 3600),
#     )


# def base(data: dict) -> str:
#     return con(
#         data["payload"]["user"]["nickname"],
#         "等级：" + data["payload"]["stats"]["progression"]["level"],
#         "",
#         "综合数据",
#         gen_stat(data["StatGeneral"][0]),
#     )


# def pro(data: dict) -> str:
#     r = ""
#     return con(
#         data["username"],
#         r,
#         "",
#         f"排位MMR：{data['payload']['stats']['seasonal']['ranked']['mmr']:d}\n休闲MMR：{data['payload']['stats']['seasonal']['casual']['mmr']:d}\n隐藏Rank：{rank(data['payload']['stats']['seasonal']['ranked']['mmr'])}",
#         f"爆头击杀率：{data['payload']['stats']['general']['headshots'] / data['payload']['stats']['general']['kills']:.2f}",
#     )


# def gen_op(data: dict) -> str:
#     return con(
#         f"胜负比：{data['payload']['stats']['operators']['id']}",
#         f"胜负比：{(data['payload']['stats']['operators']['wins'] / data['payload']['stats']['operators']['losses']):.2f}",
#         f"KD：{(data['kills'] / data['deaths']):.2f} {data['kills']:d}/{data['deaths']:d}",
#         f"游戏时长: {(data['payload']['stats']['operators']['timePlayed'] / 3600):.2f}小时",
#     )


# def operators(data: dict) -> str:
#     ops: list = data["payload"]["stats"]["operators"]
#     ops.sort(reverse=True, key=lambda x: x["wins"] + x["losses"])
#     r = data["id"] + "常用干员数据："
#     for op in ops[:6]:
#         r = con(r, "", gen_op(op))
#     return r


# def recently_played(data: dict) -> str:
#     recently_ranked = [

#     ]
#     update_at_time = [
#         str(data["update_at"]["hours"]),
#         str(data["update_at"]["minutes"])
#     ]
#     return con(
#         ".".join(update_at_date)+" "+":".join(update_at_time),
#         "胜/负：%d/%d" % (data["won"], data["lost"]),
#         "KD：%.2f %d/%d" % ((data["kills"]/data["deaths"]), data["kills"], data["deaths"]
#                            ) if data["deaths"] != 0 else ("KD：- %d/%d" % (data["kills"], data["deaths"]))
#     )

from nonebot import on_command
from nonebot.adapters.cqhttp.message import MessageSegment
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Bot, Event
import ujson as json
import os

from .r6s_data import *
from .net import get_data_from_r6scn
from .image import *
from .player import new_player_from_r6scn


__zx_plugin_name__ = "彩六查分"
__plugin_usage__ = """
usage：
    查询你的掉分之路
    指令：
        r6s/r6spro/r6sops/r6sp/r6sset
""".strip()
__plugin_des__ = "彩虹六号围攻rank分查询"
__plugin_cmd__ = [
    "r6s/r6spro/r6sops/r6sp/r6sset",
]
__plugin_type__ = ("一些工具",)
__plugin_version__ = 0.3
__plugin_author__ = "Abrahum"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": [
        "r6s",
        "r6spro",
        "r6sops",
        "r6sp",
        "r6sset",
    ],
}


r6s = on_command("r6s", aliases={"彩六", "彩虹六号", "r6", "R6"}, rule=to_me(), priority=5, block=True)
r6s_pro = on_command("r6spro", aliases={"r6pro", "R6pro"}, rule=to_me(), priority=5, block=True)
r6s_ops = on_command("r6sops", aliases={"r6ops", "R6ops"}, rule=to_me(), priority=5, block=True)
r6s_plays = on_command("r6sp", aliases={"r6p", "R6p"}, rule=to_me(), priority=5, block=True)
r6s_set = on_command("r6sset", aliases={"r6set", "R6set"}, rule=to_me(), priority=5, block=True)


_cachepath = os.path.join("cache", "r6s.json")
ground_can_do = (base, pro)  # ground数据源乱码过多，干员和近期战绩还在努力解码中···


if not os.path.exists("cache"):
    os.makedirs("cache")

if not os.path.exists(_cachepath):
    with open(_cachepath, "w", encoding="utf-8") as f:
        f.write("{}")


def set_usr_args(state: T_State, event: Event):
    args = str(event.get_message()).strip()
    if args:
        state["username"] = args
    else:
        with open(_cachepath, "r", encoding="utf-8") as f:
            data: dict = json.load(f)
        state["username"] = data.get(event.get_user_id())


async def handler(matcher, state: T_State, func):
    username = state["username"]
    ''' 21.05.24 ground接口失效，暂时切换回r6scn
    if func in ground_can_do:
        # 优先使用ground数据源，cn数据源存在部分休闲与排位错位问题
        data = await get_data_from_ground(username)
    else:
        data = await get_data(username)
    '''
    data = await get_data(username)
    if not data:
        await matcher.finish("R6sCN又抽风啦，请稍后再试。")
    elif data == "Not Found":
        await matcher.finish("未找到干员『%s』" % username)
    elif not data.get("Casualstat") and not (func in ground_can_do):
        await matcher.finish("R6sCN没有更新你的数据，你是不是开了白裤裆寒冬一击。")
    await matcher.finish(func(data))


async def new_handler(matcher, state: T_State, func):
    username = state["username"]
    data = await get_data_from_r6scn(username)
    if data == "Not Found":
        await matcher.finish("未找到干员『%s』" % username)
    player = new_player_from_r6scn(data)
    img_b64 = encode_b64(await func(player))
    await matcher.finish(MessageSegment.image(file=f"base64://{img_b64}"))


@r6s_set.handle()
async def r6s_set_handler(bot: Bot, event: Event):
    args = str(event.get_message()).strip()
    if args:
        with open(_cachepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        data[event.get_user_id()] = args
        with open(_cachepath, "w", encoding="utf-8") as f:
            json.dump(data, f)
        await r6s_set.finish("已设置ID：%s" % args)


@r6s.handle()
async def r6s_handler(bot: Bot, event: Event, state: T_State):
    set_usr_args(state, event)


@r6s.got("username", prompt="请输入查询的角色昵称")
async def r6s_goter(bot: Bot, event: Event, state: T_State):
    # await handler(r6s, state, base)
    await new_handler(r6s, state, base_image)


@r6s_pro.handle()
async def r6s_pro_handler(bot: Bot, event: Event, state: T_State):
    set_usr_args(state, event)


@r6s_pro.got("username", prompt="请输入查询的角色昵称")
async def r6s_pro_goter(bot: Bot, event: Event, state: T_State):
    # await handler(r6s, state, pro)
    await new_handler(r6s_pro, state, detail_image)


@r6s_ops.handle()
async def r6s_ops_handler(bot: Bot, event: Event, state: T_State):
    set_usr_args(state, event)


@r6s_ops.got("username", prompt="请输入查询的角色昵称")
async def r6s_ops_goter(bot: Bot, event: Event, state: T_State):
    # await handler(r6s, state, operators)
    await new_handler(r6s_ops, state, operators_img)


@r6s_plays.handle()
async def r6s_plays_handler(bot: Bot, event: Event, state: T_State):
    set_usr_args(state, event)


@r6s_plays.got("username", prompt="请输入查询的角色昵称")
async def r6s_plays_goter(bot: Bot, event: Event, state: T_State):
    # await handler(r6s, state, plays)
    await new_handler(r6s_plays, state, plays_image)

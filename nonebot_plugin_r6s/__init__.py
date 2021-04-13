from nonebot import on_command
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Bot, Event
import ujson as json
import os

from .r6s_data import *
from .r6s_ground import get_data as get_data_from_ground


r6s = on_command("r6s", aliases={"彩六", "彩虹六号", "r6", "R6"}, rule=to_me())
r6s_pro = on_command("r6spro", aliases={"r6pro", "R6pro"}, rule=to_me())
r6s_ops = on_command("r6sops", aliases={"r6ops", "R6ops"}, rule=to_me())
r6s_plays = on_command("r6sp", aliases={"r6p", "R6p"}, rule=to_me())
r6s_set = on_command("r6sset", aliases={"r6set", "R6set"}, rule=to_me())


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
    if func in ground_can_do:
        # 优先使用ground数据源，cn数据源存在部分休闲与排位错位问题
        data = await get_data_from_ground(username)
    else:
        data = await get_data(username)
    if not data:
        await matcher.finish("R6sCN又抽风啦，请稍后再试。")
    elif data == "Not Found":
        await matcher.finish("未找到干员『%s』" % username)
    elif not data.get("Casualstat") and not (func in ground_can_do):
        await matcher.finish("R6sCN没有更新你的数据，你是不是开了白裤裆寒冬一击。")
    await matcher.finish(func(data))


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
    await handler(r6s, state, base)


@r6s_pro.handle()
async def r6s_pro_handler(bot: Bot, event: Event, state: T_State):
    set_usr_args(state, event)


@r6s_pro.got("username", prompt="请输入查询的角色昵称")
async def r6s_pro_goter(bot: Bot, event: Event, state: T_State):
    await handler(r6s, state, pro)


@r6s_ops.handle()
async def r6s_ops_handler(bot: Bot, event: Event, state: T_State):
    set_usr_args(state, event)


@r6s_ops.got("username", prompt="请输入查询的角色昵称")
async def r6s_ops_goter(bot: Bot, event: Event, state: T_State):
    await handler(r6s, state, operators)


@r6s_plays.handle()
async def r6s_plays_handler(bot: Bot, event: Event, state: T_State):
    set_usr_args(state, event)


@r6s_plays.got("username", prompt="请输入查询的角色昵称")
async def r6s_plays_goter(bot: Bot, event: Event, state: T_State):
    await handler(r6s, state, plays)

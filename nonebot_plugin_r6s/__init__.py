import os

import ujson as json
from nonebot import on_command, get_driver
from nonebot.adapters.onebot.v11 import Event, Message
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText

from .config import plugin_config
# from utils.image import *
from .player import new_player_from_r6scn
from .r6s_data import *

r6s = on_command("r6s", aliases={"彩六", "彩虹六号", "r6", "R6"}, priority=5, block=True)
r6s_pro = on_command("r6spro", aliases={"r6pro", "R6pro"}, priority=5, block=True)
r6s_ops = on_command("r6sops", aliases={"r6ops", "R6ops"}, priority=5, block=True)
r6s_plays = on_command("r6sp", aliases={"r6p", "R6p"}, priority=5, block=True)
r6s_set = on_command("r6sset", aliases={"r6set", "R6set"}, priority=5, block=True)

_cachepath = os.path.join("cache", "r6s.json")
ground_can_do = (base, pro)  # ground数据源乱码过多，干员和近期战绩还在努力解码中···
max_retry = plugin_config.r6s_max_retry
driver = get_driver()


if not os.path.exists("cache"):
    os.makedirs("cache")

if not os.path.exists(_cachepath):
    with open(_cachepath, "w", encoding="utf-8") as f:
        f.write("{}")


def set_usr_args(matcher: Matcher, event: Event, msg: Message):
    if msg.extract_plain_text():
        matcher.set_arg("username", msg)
    else:
        with open(_cachepath, "r", encoding="utf-8") as f:
            data: dict = json.load(f)
        if username := data.get(event.get_user_id()):
            matcher.set_arg("username", Message(username))


# async def new_handler(matcher: Matcher, username: str, func: FunctionType):
#     data = await get_r6s_adapter(
#         plugin_config.default_name, plugin_config.r6s_max_retry, plugin_config.r6s_proxy
#     )
#     if data == "Not Found":
#         await matcher.finish(f"未找到干员『{username}』")
#     try:
#         player = new_player_from_r6scn(data)
#     except:
#         await matcher.finish(f"查询干员出错『{username}』")
#         return
#     img_b64 = encode_b64(await func(player))
#     await matcher.finish(MessageSegment.image(file=f"base64://{img_b64}"))


# @r6s_set.handle()
# async def r6s_set_handler(event: Event, args: Message = CommandArg()):
#     if args := args.extract_plain_text():
#         with open(_cachepath, "r", encoding="utf-8") as f:
#             data = json.load(f)
#         data[event.get_user_id()] = args
#         with open(_cachepath, "w", encoding="utf-8") as f:
#             json.dump(data, f)
#         await r6s_set.finish(f"已设置ID：{args}")


# @r6s.handle()
# async def _(matcher: Matcher, event: Event, msg: Message = CommandArg()):
#     set_usr_args(matcher, event, msg)


@r6s.got("username", prompt="请输入查询的角色昵称")
async def _(username: str = ArgPlainText()):
    await new_handler(r6s, username, base_image)


# @r6s_pro.handle()
# async def _(matcher: Matcher, event: Event, msg: Message = CommandArg()):
#     set_usr_args(matcher, event, msg)


# @r6s_pro.got("username", prompt="请输入查询的角色昵称")
# async def _(username: str = ArgPlainText()):
#     await new_handler(r6s, username, detail_image)


# @r6s_ops.handle()
# async def _(matcher: Matcher, event: Event, msg: Message = CommandArg()):
#     set_usr_args(matcher, event, msg)


# @r6s_ops.got("username", prompt="请输入查询的角色昵称")
# async def _(username: str = ArgPlainText()):
#     await new_handler(r6s, username, operators_img)


# @r6s_plays.handle()
# async def _(matcher: Matcher, event: Event, msg: Message = CommandArg()):
#     set_usr_args(matcher, event, msg)


# @r6s_plays.got("username", prompt="请输入查询的角色昵称")
# async def _(username: str = ArgPlainText()):
#     await new_handler(r6s, username, plays_image)

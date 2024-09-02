import uuid
from contextlib import suppress
from pathlib import Path

import aiofiles
import aiohttp
from arclet.alconna import Alconna, Subcommand, Args, CommandMeta
from loguru import logger
from nonebot import get_driver, require
from nonebot_plugin_alconna import Match, UniMsg, on_alconna, Image
from nonebot_plugin_orm import async_scoped_session
from nonebot_plugin_session import EventSession
from siegeapi import Auth, InvalidRequest

from .utils import (
    R6sAuth,
    load_json_file,
    drop_file,
    create_trace_config,
)

require("nonebot_plugin_localstore")
require("nonebot_plugin_htmlrender")
require("nonebot_plugin_orm")

from .utils.database_model import LoginUserSessionBind
from .utils.model import Credentials
from .config import plugin_config
from nonebot_plugin_htmlrender import md_to_pic

# r6s = on_command(
#     "r6s", aliases={"彩六", "彩虹六号", "r6", "R6"}, priority=5, block=True
# )

r6s = on_alconna(
    Alconna(
        "r6s",
        Subcommand(
            "-b|--bind",
            Args["email", str]["password", str]["group", str],
            help_text="绑定登录信息到指定群组",
        ),
        Subcommand("-u|--unbind", Args["group", str], help_text="解绑登录信息"),
        Subcommand(
            "-s|--search",
            Args["username", str]["platform?", str],
            help_text="搜索玩家信息, 注意这里的用户名是育碧账号用户名而不是游戏内昵称",
        ),
        meta=CommandMeta(
            description="Rainbow Six Siege 玩家数据查询",
            usage=(
                "/r6s -b|--bind <email> <password> <group>\n"
                "/r6s -u|--unbind <group>\n"
                "/r6s -s|--search <username> [platform]"
            ),
            example=(
                "/r6s -b 123@gmail.com 123456 group1\n"
                "/r6s -u group1\n"
                "/r6s -s Juefdsfvcdvbd uplay"
            ),
        ),
    ),
    priority=5,
    block=True,
)
# r6s_pro = on_command("r6spro", aliases={"r6pro", "R6pro"}, priority=5, block=True)
# r6s_ops = on_command("r6sops", aliases={"r6ops", "R6ops"}, priority=5, block=True)
# r6s_plays = on_command("r6sp", aliases={"r6p", "R6p"}, priority=5, block=True)
# r6s_set = on_command("r6sset", aliases={"r6set", "R6set"}, priority=5, block=True)

driver = get_driver()


@r6s.assign("bind")
async def bind(
    bot,
    event,
    email: str,
    password: str,
    group: str,
    unimsg: UniMsg,
    event_session: EventSession,
    db_session: async_scoped_session,
):
    cache_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, plugin_config.salt)
    creds_path = Path(plugin_config.cache_dir / "creds" / f"{cache_uuid}.json")

    with suppress(InvalidRequest):
        async with aiohttp.ClientSession(
            trace_configs=[create_trace_config()]
        ) as session:
            auth = Auth(
                token=Auth.get_basic_token(email, password),
                creds_path=str(creds_path),
                session=session,
            )
            auth.save_creds()
            await auth.get_player(
                name="nonebot_plugin_r6s"
            )  # A request is needed to obtain the credentials. Idk why.
            await auth.close()

    async with db_session() as scoped_session:
        try:
            credentials = Credentials.model_validate(await load_json_file(creds_path))
            scoped_session.add(
                LoginUserSessionBind(
                    **credentials.model_dump(),
                    token=R6sAuth.get_salt_token(email, password, plugin_config.salt),
                    bind_id=group,
                    bind_account=event_session.id1,
                    platform=event_session.platform,
                )
            )
            await scoped_session.commit()

            drop_file(creds_path)

        except ValueError as e:
            logger.error(f"Error occurred during the session: {e!s}")
            await r6s.finish("绑定失败😭")
        except Exception as e:
            await scoped_session.rollback()
            logger.error(f"Error occurred during the session: {e!s}")
            await r6s.finish("绑定失败😭")

    await r6s.finish("绑定成功🚀🚀")


@r6s.assign("unbind")
async def unbind(
    bot,
    event,
    group: str,
    event_session: EventSession,
    db_session: async_scoped_session,
):
    if event_session.id1 is None:
        await r6s.finish("未知的异常🐽")
    async with db_session() as scoped_session:
        if not await LoginUserSessionBind.check_user_occupation(
            scoped_session,
            group,
            event_session.id1,
        ):
            await r6s.finish("未找到绑定信息🧐")
        else:
            await LoginUserSessionBind.unbind_user(
                scoped_session,
                group,
                event_session.id1,
            )
            await scoped_session.commit()
            await r6s.finish("解绑成功🚀🚀")


@r6s.assign("search")
async def search(
    bot,
    event,
    username: str,
    event_session: EventSession,
    db_session: async_scoped_session,
    platform: Match[str],
):
    if event_session.id2 is not None:
        async with db_session() as scoped_session:
            bind_session, _ = await LoginUserSessionBind.get_session(
                scoped_session,
                event_session.id2,
            )
        if bind_session is None:
            await r6s.finish("未找到绑定信息🧐")
        token = R6sAuth.get_origin_token(bind_session.token, plugin_config.salt)
        try:
            async with aiohttp.ClientSession(
                trace_configs=[create_trace_config()]
            ) as session:
                auth = Auth(
                    token=token,
                    session=session,
                )
                player = await auth.get_player(name=username)
                await player.load_linked_accounts()
        except InvalidRequest:
            await r6s.finish("未找到该用户🧐")


@r6s.assign("protocol")
async def _():
    md = Path(__file__).parent / "templates" / "agreement.md"
    async with aiofiles.open(md, encoding="utf-8") as file:
        agreement_content = await file.read()

    pic = await md_to_pic(md=agreement_content)

    await r6s.finish(Image(raw=pic))


# def set_usr_args(matcher: Matcher, event: Event, msg: Message):
#     if msg.extract_plain_text():
#         matcher.set_arg("username", msg)
#     else:
#         with open(_cachepath, "r", encoding="utf-8") as f:
#             data: dict = json.load(f)
#         if username := data.get(event.get_user_id()):
#             matcher.set_arg("username", Message(username))


# async def new_handler(matcher: Matcher, username: str, func: FunctionType):
#     player = await new_player_from_r6scn(username)
#     if player:
#         await matcher.finish(await func(player))
#     else:
#         await matcher.finish("未找到该用户")


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


# @r6s.handle()
# async def _():
#     data_model = PlayerData(**data).model_dump()
#     img = await template_to_pic(
#         str(Path(__file__).parent / "templates"),
#         "test.jinja",
#         data_model,
#         pages={
#             "viewport": {"width": 1300, "height": 650},
#         },
#     )
#     Image.open(io.BytesIO(img)).show()


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

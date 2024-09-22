from typing import Literal

from typing import cast
import aiohttp
from arclet.alconna import Arparma
from nonebot.internal.adapter import Event, Bot
from nonebot.typing import T_State
from nonebot_plugin_alconna import UniMessage, Match
from nonebot_plugin_orm import get_session
from nonebot_plugin_session import EventSession
from siegeapi import InvalidRequest

from nonebot_plugin_r6s import r6s, create_trace_config
from nonebot_plugin_r6s.adapters.siegeapi import SiegeAPI
from nonebot_plugin_r6s.config import global_config
from nonebot_plugin_r6s.utils.database_model import LoginUserSessionBind


async def condition_checker(
    event: Event, bot: Bot, state: T_State, arparma: Arparma
) -> bool:
    """
    Check if the user has binded a Ubisoft account.

    Args:
        event (Event): Event object.
        bot (Bot): Bot object.
        state (T_State): State object.
        arparma (Arparma): Arparma object.

    Returns:
        bool: Whether the user has binded a Ubisoft account.
    """
    target = UniMessage.get_target(event, bot)
    async with get_session() as db_session:
        bind_session = LoginUserSessionBind.get_session_by_bind_id(
            db_session,
            target.id,
        )
        state["bind_session"] = bind_session

        if bind_session:
            return True

        message = (
            "好像还没有绑定账号🧐，请先进行 Ubisoft 帐号绑定"
            if target.private
            else f"好像还没有绑定账号🧐，请管理员私聊 {global_config.nickname} 进行绑定"
        )
        await r6s.finish(message)


def platform_checker(platform: str) -> bool:
    return platform in {"uplay", "xbl", "psn"}


@r6s.assign("search", additional=condition_checker)
async def _(
    bot,
    event,
    username: str,
    state: T_State,
    event_session: EventSession,
    platform: Match[str],
):
    if platform.available and platform_checker(platform.result):
        await r6s.finish("未知的平台🧐, 支持的平台为 uplay, xbl 或 psn")

    if state["bind_session"] is None:
        target = UniMessage.get_target(event, bot)
        async with get_session() as db_session:
            state["bind_session"] = await LoginUserSessionBind.get_session_by_bind_id(
                db_session,
                target.id,
            )
        if state["bind_session"] is None:
            await r6s.finish("未知的异常🐽")

    try:
        async with aiohttp.ClientSession(
            trace_configs=[create_trace_config()],
        ) as http_session:
            await SiegeAPI.with_player_by_name(
                token=state["bind_session"].token,
                session=http_session,
                name=username,
                platform=cast(Literal["uplay", "xbl", "psn"], platform.result),
            )
    # image = await template_to_pic(
    #     str(plugin_config.resouce_dir),
    #     "test.jinja",
    #     templates=RenderData(
    #         font_family="JetBrains Mono",
    #         player_info=, rank_stats=, quick_stats=, role_info_group=,
    #         rank_info_group=, metadata=, ).model_dump(),
    #     pages={
    #         "viewport": {"width": 1300, "height": 650},
    #     },
    # )
    # await r6s.finish(Image(raw=image))
    except InvalidRequest:
        await r6s.finish("未找到该用户🧐")

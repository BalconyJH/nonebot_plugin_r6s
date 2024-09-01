from typing import Optional, Union

from nonebot.adapters.onebot.v11 import Bot as v11Bot
from nonebot.adapters.onebot.v12 import Bot as v12Bot
from nonebot.internal.adapter import Bot
from pydantic import BaseModel


class UserData(BaseModel):
    name: str
    card: Optional[str] = None
    user_id: str
    group_id: Optional[str] = None
    role: Optional[str] = None
    avatar_url: Optional[str] = None
    join_time: Optional[int] = None


class PlatformUtils:
    @classmethod
    async def get_user(
        cls, bot: Bot, user_id: str, group_id: Optional[str] = None
    ) -> Optional[UserData]:
        """
        Get user data

        Args:
            bot (Bot): Bot instance
            user_id (str): User id
            group_id (Optional[str], optional): Group id. Defaults to None.

        Returns:
            Optional[UserData]: User data
        """
        if isinstance(bot, v11Bot):
            if group_id:
                if user := await bot.get_group_member_info(
                    group_id=int(group_id), user_id=int(user_id)
                ):
                    return UserData(
                        name=user["nickname"],
                        card=user["card"],
                        user_id=user["user_id"],
                        group_id=user["group_id"],
                        role=user["role"],
                        join_time=user["join_time"],
                    )
            elif friend_list := await bot.get_friend_list():
                for f in friend_list:
                    if f["user_id"] == int(user_id):
                        return UserData(
                            name=f["nickname"],
                            card=f["remark"],
                            user_id=f["user_id"],
                        )
        if isinstance(bot, v12Bot):
            if group_id:
                if user := await bot.get_group_member_info(
                    group_id=group_id, user_id=user_id
                ):
                    return UserData(
                        name=user["user_name"],
                        card=user["user_displayname"],
                        user_id=user["user_id"],
                        group_id=group_id,
                    )
            elif friend_list := await bot.get_friend_list():
                for f in friend_list:
                    if f["user_id"] == int(user_id):
                        return UserData(
                            name=f["user_name"],
                            card=f["user_remark"],
                            user_id=f["user_id"],
                        )
        # if isinstance(bot, DodoBot) and group_id:
        #     if user := await bot.get_member_info(
        #         island_source_id=group_id, dodo_source_id=user_id
        #     ):
        #         return UserData(
        #             name=user.nick_name,
        #             card=user.personal_nick_name,
        #             avatar_url=user.avatar_url,
        #             user_id=user.dodo_source_id,
        #             group_id=user.island_source_id,
        #             join_time=int(user.join_time.timestamp()),
        #         )
        # if isinstance(bot, KaiheilaBot) and group_id:
        #     if user := await bot.user_view(guild_id=group_id, user_id=user_id):
        #         second = int(user.joined_at / 1000) if user.joined_at else None
        #         return UserData(
        #             name=user.nickname or "",
        #             avatar_url=user.avatar,
        #             user_id=user_id,
        #             group_id=group_id,
        #             join_time=second,
        #         )
        return None

    @classmethod
    def get_platform(cls, bot: Bot) -> Optional[str]:
        """
        Get platform

        Args:
            bot (Bot): Bot instance

        Returns:
            Optional[str]: Platform name
        """
        if isinstance(bot, Union[v11Bot, v12Bot]):
            return "qq"
        # if isinstance(bot, DodoBot):
        #     return "dodo"
        # if isinstance(bot, KaiheilaBot):
        #     return "kaiheila"
        # return "discord" if isinstance(bot, DiscordBot) else None

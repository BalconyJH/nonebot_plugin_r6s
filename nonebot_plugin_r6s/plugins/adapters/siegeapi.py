import asyncio
from typing import Optional, Literal, overload, TypeVar

from aiohttp import ClientSession
from nonebot import logger
from siegeapi import Auth, Player

from nonebot_plugin_r6s.utils.model import PlayerInfo, LinkAccount

T = TypeVar("T", bound="SiegeAPI")


class SiegeAPI(Auth):
    def __init__(self, email: str, password: str, session: ClientSession):
        super().__init__(email, password, session=session)
        self.player = None
        self.player_name = None
        self.linked_accounts = None

    @overload
    @classmethod
    async def with_player(
        cls: type[T],
        email: str,
        password: str,
        session: ClientSession,
        name: str,
        uid: None = None,
        platform: Literal["uplay", "xbl", "psn"] = "uplay",
    ) -> T: ...

    @overload
    @classmethod
    async def with_player(
        cls: type[T],
        email: str,
        password: str,
        session: ClientSession,
        name: None,
        uid: str,
        platform: Literal["uplay", "xbl", "psn"] = "uplay",
    ) -> T: ...

    @classmethod
    async def with_player(
        cls: type[T],
        email: str,
        password: str,
        session: ClientSession,
        name: Optional[str] = None,
        uid: Optional[str] = None,
        platform: Literal["uplay", "xbl", "psn"] = "uplay",
    ) -> T:
        instance = cls(email, password, session)
        cls.player_name = name
        instance.player = await instance.get_player(
            name=name, uid=uid, platform=platform
        )
        return instance

    async def load_data(self):
        try:
            if self.player is not None:
                results = await asyncio.gather(
                    self.player.load_linked_accounts(),
                    self.player.load_ranked_v2(),
                    self.player.load_playtime(),
                    self.player.load_progress(),
                    self.player.load_persona(),
                    return_exceptions=True,
                )
                for i, result in enumerate(results):
                    if isinstance(result, ValueError):
                        logger.error(f"Task {i} raised an exception: {result}")
        except Exception:
            logger.exception(
                f"An error occurred while loading player: {self.player_name} data"
            )

    @overload
    async def fetch_player(
        self,
        name: str,
        uid: None = None,
        platform: Literal["uplay", "xbl", "psn"] = "uplay",
    ) -> Player: ...

    @overload
    async def fetch_player(
        self, name: None, uid: str, platform: Literal["uplay", "xbl", "psn"] = "uplay"
    ) -> Player: ...

    async def fetch_player(
        self,
        name: Optional[str] = None,
        uid: Optional[str] = None,
        platform: Literal["uplay", "xbl", "psn"] = "uplay",
    ) -> Player:
        self.player = await super().get_player(name=name, uid=uid, platform=platform)
        return self.player

    async def load_player_info(self) -> PlayerInfo:
        if not self.player:
            raise ValueError(
                "Player is not set. Please use get_player() to fetch a player first."
            )

        return PlayerInfo(
            avatar_url=self.player.profile_pic_url_500,
            player_name=self.player.name,
            player_level=self.player.level,
            player_mmr=getattr(self.player.ranked_profile, "rank_points", 0),
            aliases=[""],  # TODO: Add aliases (upstream unsupported)
            linked_accounts=[
                # LinkAccount(
                #     platform_type=account.platform_type,
                #     name_on_platform=account.name_on_platform,
                # )
                LinkAccount(**vars(account))
                for account in self.player.linked_accounts
            ],
        )

import asyncio
from typing import Optional, Literal, overload, TypeVar

from aiohttp import ClientSession
from nonebot import logger
from siegeapi import Auth, Player

from nonebot_plugin_r6s.utils.model import PlayerInfo, LinkAccount, UserPreferences

T = TypeVar("T", bound="SiegeAPI")


class SiegeAPI(Auth):
    def __init__(self, email: str, password: str, session: ClientSession):
        super().__init__(email, password, session=session)
        self.player = None
        self.player_name = None
        self.linked_accounts = None

    @classmethod
    async def with_player_by_name(
        cls: type[T],
        email: str,
        password: str,
        session: ClientSession,
        name: str,
        platform: Literal["uplay", "xbl", "psn"] = "uplay",
    ) -> T:
        """
        Create a SiegeAPI instance with a player by name.

        Args:
            email (str): Ubisoft account email.
            password (str): Ubisoft account password.
            session (ClientSession): aiohttp client session.
            name (str): Player name.
            platform (Literal["uplay", "xbl", "psn"], optional): Platform. Defaults
            to "uplay".

        Returns:
            SiegeAPI: SiegeAPI instance.
        """
        instance = cls(email, password, session)
        cls.player_name = name
        instance.player = await instance.get_player(name=name, platform=platform)
        return instance

    @classmethod
    async def with_player_by_uid(
        cls: type[T],
        email: str,
        password: str,
        session: ClientSession,
        uid: str,
        platform: Literal["uplay", "xbl", "psn"] = "uplay",
    ) -> T:
        """
        Create a SiegeAPI instance with a player by UID.

        Args:
            email (str): Ubisoft account email.
            password (str): Ubisoft account password.
            session (ClientSession): aiohttp client session.
            uid (str): Player UID.
            platform (Literal["uplay", "xbl", "psn"], optional): Platform. Defaults
            to "uplay".

        Returns:
            SiegeAPI: SiegeAPI instance.
        """
        instance = cls(email, password, session)
        instance.player = await instance.get_player(uid=uid, platform=platform)
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

    async def load_linked_accounts(self):
        if not self.player:
            raise ValueError(
                "Player is not set. Please use get_player() to fetch a player first."
            )

        return [LinkAccount(**vars(account)) for account in self.player.linked_accounts]

    async def load_persona(self) -> Optional[UserPreferences]:
        if not self.player:
            raise ValueError(
                "Player is not set. Please use get_player() to fetch a player first."
            )

        return (
            UserPreferences(
                tag=self.player.persona.tag,
                enabled=self.player.persona.enabled,
                nickname=self.player.persona.nickname,
            )
            if self.player.persona
            else None
        )

    async def load_player_info(self) -> PlayerInfo:
        if not self.player:
            raise ValueError(
                "Player is not set. Please use get_player() to fetch a player first."
            )

        return PlayerInfo(
            avatar_url=self.player.profile_pic_url,
            name=self.player.name,
            level=self.player.level,
            mmr=(
                self.player.ranked_profile.rank_points
                if self.player.ranked_profile
                else 0
            ),
            linked_accounts=await self.load_linked_accounts(),
            total_time_played=self.player.total_time_played_hours,
            aliases=[""],  # TODO: Add aliases(Upstream unsupported)
            persona=await self.load_persona(),
        )

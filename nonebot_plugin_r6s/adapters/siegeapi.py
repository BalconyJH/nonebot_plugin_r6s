import asyncio
from typing import Optional, Literal, overload, TypeVar

from aiohttp import ClientSession
from nonebot import logger
from siegeapi import Auth, Player

from nonebot_plugin_r6s.utils import win_rate, kd_parser
from nonebot_plugin_r6s.utils.model import (
    PlayerInfo,
    LinkAccount,
    UserPreferences,
    RankStats,
)

T = TypeVar("T", bound="SiegeAPI")


class SiegeAPI(Auth):
    def __init__(self, token: str, session: ClientSession, **kwargs):
        super().__init__(token=token, session=session, extra_get_kwargs=kwargs)
        self.player = None
        self.player_name = None
        self.linked_accounts = None

    @classmethod
    async def with_player_by_name(
        cls: type[T],
        token: str,
        session: ClientSession,
        name: str,
        platform: Literal["uplay", "xbl", "psn"] = "uplay",
        **kwargs,
    ) -> T:
        """
        Create a SiegeAPI instance with a player by name.

        Args:
            token (str): Ubisoft account token.
            session (ClientSession): aiohttp client session.
            name (str): Player name.
            platform (Literal["uplay", "xbl", "psn"], optional): Platform. Defaults
            to "uplay".

        Returns:
            SiegeAPI: SiegeAPI instance.
        """
        instance = cls(token=token, session=session, **kwargs)
        instance.player = await instance.get_player(name=name, platform=platform)
        return instance

    @classmethod
    async def with_player_by_uid(
        cls: type[T],
        token: str,
        session: ClientSession,
        uid: str,
        platform: Literal["uplay", "xbl", "psn"] = "uplay",
        **kwargs,
    ) -> T:
        """
        Create a SiegeAPI instance with a player by UID.

        Args:
            token (str): Ubisoft account token.
            session (ClientSession): aiohttp client session.
            uid (str): Player UID.
            platform (Literal["uplay", "xbl", "psn"], optional): Platform. Defaults
            to "uplay".

        Returns:
            SiegeAPI: SiegeAPI instance.
        """
        instance = cls(token=token, session=session, **kwargs)
        instance.player = await instance.get_player(uid=uid, platform=platform)
        return instance

    async def load_data(self):
        if self.player is not None:
            results = await asyncio.gather(
                self.player.load_linked_accounts(),
                self.player.load_ranked_v2(),
                self.player.load_playtime(),
                self.player.load_progress(),
                self.player.load_persona(),
                # self.player.load_summaries(),
                return_exceptions=True,
            )
            for i, result in enumerate(results):
                if isinstance(result, ValueError):
                    logger.error(f"Task {i} raised an exception: {result}")
        else:
            logger.warning(f"Player is None, cannot load data for {self.player_name}")

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

    async def load_rank_stats(self):
        if not self.player:
            raise ValueError(
                "Player is not set. Please use get_player() to fetch a player first."
            )

        if not self.player.ranked_profile:
            raise ValueError(
                "Player does not have ranked profile. "
                "Please use load_ranked_v2() to fetch ranked profile first."
            )

        wr = win_rate(
            self.player.ranked_profile.wins, self.player.ranked_profile.losses
        )
        kd = kd_parser(
            self.player.ranked_profile.kills,
            self.player.ranked_profile.deaths,
        )

        return RankStats(
            wins=self.player.ranked_profile.wins,
            losses=self.player.ranked_profile.losses,
            wr=f"{wr:.2%}",
            kd=kd,
            kills=self.player.ranked_profile.kills,
            deaths=self.player.ranked_profile.deaths,
        )

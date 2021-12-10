from io import BytesIO
import httpx
from typing import List, Dict, Optional
import json


class DataStruct:
    def __repr__(self) -> str:
        return self.__dict__.__repr__()


class BasicStat(DataStruct):
    level: int
    platform: str
    region: str  # apac emea ncsa

    def __init__(self, data: Dict):
        self.__dict__.update(data)


class GeneralStat(DataStruct):
    killAssists: int       # 协助击杀
    kills: int             # 击杀
    deaths: int            # 死亡
    meleeKills: int        # 近战击杀
    penetrationKills: int  # 穿透击杀
    headshot: int          # 爆头击杀
    revives: int           # 救助次数
    bulletsHit: int        # 子弹命中数
    bulletsFired: int      # 发射子弹数

    timePlayed: int        # 游玩时间
    played: int            # 游玩局数
    won: int               # 胜利局数
    lost: int              # 失败局数

    def __init__(self, data: Dict):
        self.__dict__.update(data)

    def kd(self) -> str:
        if self.deaths == 0:
            return '∞'
        return f'{self.kills / self.deaths:.2f}'

    def win_rate(self) -> str:
        return f'{self.won / self.played * 100:.2f}%'


class CRStat(DataStruct):
    model: str             # 模式 casual or ranked
    kills: int             # 击杀
    deaths: int            # 死亡
    timePlayed: int        # 游玩时间
    played: int            # 游玩局数
    won: int               # 胜利局数
    lost: int              # 失败局数
    mmr: Optional[float]   # MMR
    time: int              # 时间 ms timestamp

    def __init__(self, data: Dict) -> None:
        self.__dict__.update(data)
        if data.get("update_at") is not None:
            self.time = data["update_at"]["time"]

    def kd(self) -> str:
        if not hasattr(self, 'deaths'):
            return "Unkown"
        if self.deaths == 0:
            return '∞'
        return f'{self.kills / self.deaths:.2f}'

    def win_rate(self) -> str:
        if not hasattr(self, 'played'):
            return "Unkown"
        if self.played == 0:  # 不明原因
            return "-"
        return f'{self.won / self.played * 100:.2f}%'


class OperatorStat(DataStruct):
    name: str
    kills: int
    deaths: int
    timePlayed: int
    won: int
    lost: int
    played: int

    def __init__(self, data: Dict) -> None:
        self.__dict__.update(data)
        self.played = self.won + self.lost

    def kd(self) -> str:
        if self.deaths == 0:
            return '∞'
        return f'{self.kills / self.deaths:.2f}'

    def win_rate(self) -> str:
        if self.played == 0:
            return "-"
        return f'{self.won / self.played * 100:.2f}'


class Player(DataStruct):
    username: str
    user_id: str
    basic_stat: List[BasicStat]        # 感觉是各服务器数据
    gerneral_stat: GeneralStat         # 综合数据
    casual_stat: CRStat
    ranked_stat: Optional[CRStat]
    recent_stat: List[CRStat]          # 最近对战的数据
    operator_stat: List[OperatorStat]  # 干员数据

    def __init__(self, username: str, user_id: str) -> None:
        self.username = username
        self.user_id = user_id
        self.basic_stat = []
        self.gerneral_stat = GeneralStat({})
        self.casual_stat = CRStat({})
        self.ranked_stat = None
        self.recent_stat = []
        self.operator_stat = []

    def level(self) -> int:
        level = 0
        for stat in self.basic_stat:
            level = max(level, stat.level)
        return level

    async def get_avatar(self, retry_times=0) -> bytes:
        try:
            AVATAR_BASE = "https://ubisoft-avatars.akamaized.net/{}/default_146_146.png"
            async with httpx.AsyncClient() as client:
                r = await client.get(AVATAR_BASE.format(self.user_id))
                return r.content
        except:
            if retry_times < 3:
                return await self.get_avatar(retry_times + 1)

    def casual_rank(self) -> int:
        return rank(self.casual_stat.mmr)

    def ranked_rank(self) -> Optional[int]:
        if hasattr(self.ranked_stat, 'mmr'):
            return rank(self.ranked_stat.mmr)
        else:
            return 0


def rank(mmr: float) -> int:
    mmr = int(mmr)
    rank = 0
    if mmr < 1000:
        rank = 0
    elif mmr < 2600:
        rank = mmr // 100 - 10
    elif mmr < 3200:
        rank = mmr // 200 + 3
    elif mmr < 4400:
        rank = mmr // 400 + 11
    elif mmr < 5000:
        rank = 22
    else:
        rank = 23
    return rank


def new_player_from_r6scn(data: Dict) -> Player:
    player = Player(data["username"], data["Casualstat"]["user_id"])
    for d in data["Basicstat"]:
        player.basic_stat.append(BasicStat(d))
    player.gerneral_stat = GeneralStat(data["StatGeneral"][0])
    for d in data["StatCR"]:
        if d["model"] == "casual":
            player.casual_stat = CRStat(d)
        elif d["model"] == "ranked":
            player.ranked_stat = CRStat(d)
    for d in data["StatCR2"]:
        player.recent_stat.append(CRStat(d))
    for d in data["StatOperator"]:
        player.operator_stat.append(OperatorStat(d))
    return player


if __name__ == "__main__":
    with open("tests/abrahumlink.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        player = new_player_from_r6scn(data)
        print(player.casual_rank())

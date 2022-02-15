import httpx
from typing import List, Dict, Optional


class DataStruct:
    def __repr__(self) -> str:
        return self.__dict__.__repr__()


class BasicStat(DataStruct):
    level: int
    platform: str
    region: str  # apac emea ncsa

    def __init__(self, data: Dict):
        self.__dict__.update(data)


class SeasonRanks(DataStruct):
    # season: str            # 当前赛季
    season: int  # 赛季数
    mmr: int  # 最终mmr分数
    max_mmr: int  # 最高mmr分数
    wins: int  # 胜场
    losses: int  # 败场

    def __init__(self, data: dict):
        self.__dict__.update(data)

    def get_season(self) -> str:
        # """Y6S4 = 24 -> (6-1)*4 + 4"""
        # # 第一步取余数
        # remainder = self.season_num % 4
        # year = 0
        # quarter = 0
        # # 如果等于0, 则为S4
        # if remainder == 0:
        #     quarter = 4
        #     # 年则为整除数
        #     year = self.season_num / 4
        # # 如果不等于0, 则值为赛季数
        # else:
        #     quarter = remainder
        #     # 年为减去的季度数除以4再加1
        #     year = (self.season_num - remainder) / 4 + 1

        SEASON_OF_YEAR = 4
        year = (self.season + (SEASON_OF_YEAR - 1)) / SEASON_OF_YEAR
        quarter = (self.season + (SEASON_OF_YEAR - 1)) % SEASON_OF_YEAR + 1
        season = f"Y{int(year)}S{int(quarter)}"

        return season


class GeneralStat(DataStruct):
    killAssists: int  # 协助击杀
    kills: int  # 击杀
    deaths: int  # 死亡
    meleeKills: int  # 近战击杀
    penetrationKills: int  # 穿透击杀
    headshot: int  # 爆头击杀
    revives: int  # 救助次数
    bulletsHit: int  # 子弹命中数
    bulletsFired: int  # 发射子弹数

    timePlayed: int  # 游玩时间
    played: int  # 游玩局数
    won: int  # 胜利局数
    lost: int  # 失败局数

    def __init__(self, data: Dict):
        self.__dict__.update(data)

    def kd(self) -> str:
        if self.deaths == 0:
            return "∞"
        return f"{self.kills / self.deaths:.2f}"

    def win_rate(self) -> str:
        return f"{self.won / self.played * 100:.2f}%"


class CRStat(DataStruct):
    model: str  # 模式 casual or ranked
    kills: int  # 击杀
    deaths: int  # 死亡
    timePlayed: int  # 游玩时间
    played: int  # 游玩局数
    won: int  # 胜利局数
    lost: int  # 失败局数
    mmr: Optional[float]  # MMR
    time: int  # 时间 ms timestamp

    def __init__(self, data: Dict) -> None:
        self.__dict__.update(data)
        if data.get("update_at") is not None:
            self.time = data["update_at"]["time"]

    def kd(self) -> str:
        if not hasattr(self, "deaths"):
            return "Unkown"
        if self.deaths == 0:
            return "∞"
        return f"{self.kills / self.deaths:.2f}"

    def win_rate(self) -> str:
        if not hasattr(self, "played"):
            return "Unkown"
        if self.played == 0:  # 不明原因
            return "-"
        return f"{self.won / self.played * 100:.2f}%"


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
            return "∞"
        return f"{self.kills / self.deaths:.2f}"

    def win_rate(self) -> str:
        if self.played == 0:
            return "-"
        return f"{self.won / self.played * 100:.2f}"


class Player(DataStruct):
    username: str
    user_id: str
    basic_stat: List[BasicStat]  # 感觉是各服务器数据
    gerneral_stat: GeneralStat  # 综合数据
    casual_stat: CRStat
    ranked_stat: Optional[CRStat]
    season_rank: List[SeasonRanks]  # 历史段位数据
    history_max_mmr_season: Dict  # 按照要求增加历史最高mmr
    recent_stat: List[CRStat]  # 最近对战的数据
    operator_stat: List[OperatorStat]  # 干员数据

    def __init__(self, username: str, user_id: str) -> None:
        self.username = username
        self.user_id = user_id
        self.basic_stat = []
        self.gerneral_stat = GeneralStat({})
        self.casual_stat = CRStat({})
        self.ranked_stat = None
        self.history_max_mmr_season = {}
        self.season_rank = []
        self.recent_stat = []
        self.operator_stat = []

    def level(self) -> int:
        level = 0
        for stat in self.basic_stat:
            level = max(level, stat.level)
        return level

    async def get_avatar(self, retry_times=0) -> bytes | None:
        try:
            AVATAR_BASE = "https://ubisoft-avatars.akamaized.net/{}/default_146_146.png"
            async with httpx.AsyncClient() as client:
                avataUrl = AVATAR_BASE.format(self.user_id)
                r = await client.get(avataUrl)
                return r.content
        except:
            if retry_times < 3:
                return await self.get_avatar(retry_times + 1)
            else:
                return None

    def casual_rank(self) -> int:
        return rank(self.casual_stat.mmr)

    def ranked_rank(self) -> Optional[int]:
        if hasattr(self.ranked_stat, "mmr"):
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
    # elif mmr < 4100:
    #     rank = mmr // 400 + 11
    # 与最新版本的段位间隔相符
    elif mmr < 5000:
        rank = (mmr + 100) // 300 + 8
    else:
        rank = 25
    return rank


def new_player_from_r6scn(data: Dict) -> Player:
    player = Player(data["username"], data["Casualstat"]["user_id"])
    for d in data["Basicstat"]:
        player.basic_stat.append(BasicStat(d))
    player.gerneral_stat = GeneralStat(data["StatGeneral"][0])
    for d in data["StatCR"]:
        if d["model"] == "casual":
            player.casual_stat = CRStat(d)
            player.casual_stat.mmr = data["Casualstat"]["mmr"]
        elif d["model"] == "ranked":
            player.ranked_stat = CRStat(d)
            player.ranked_stat.mmr = data["Basicstat"][0]["mmr"]
    for d in data["StatCR2"]:
        player.recent_stat.append(CRStat(d))
    for d in data["StatOperator"]:
        player.operator_stat.append(OperatorStat(d))

    dup_seasonid = []
    seasonranks = []

    for d in data["SeasonRanks"]:
        if d["season"] not in dup_seasonid:
            player.season_rank.append(SeasonRanks(d))
            dup_seasonid.append(d["season"])
            seasonranks.append(d)

    seasonranks.sort(key=lambda x: x["max_mmr"], reverse=True)
    player.history_max_mmr_season = seasonranks[0]

    return player

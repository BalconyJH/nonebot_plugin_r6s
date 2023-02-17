import httpx
def rank(mmr: int) -> str:
    head = ["紫铜", "黄铜", "白银", "黄金", "白金", "钻石", "冠军"]
    feet2 = ["III", "II", "I"]
    if mmr < 2600:
        mmrd = int(mmr // 100 - 11)
        feet1 = ["V", "IV", "III", "II", "I"]
        if mmrd < 5:
            return head[0] + feet1[mmrd]
        elif mmrd < 10:
            return head[1] + feet1[mmrd - 5]
        else:
            return head[2] + feet1[mmrd - 10]
    elif mmr < 4400:
        mmrd = int(mmr // 200 - 13)
        return head[3] + feet2[mmrd] if mmrd < 3 else head[4] + feet2[(mmrd - 3) // 2]
    elif mmr < 5000:
        return head[-2]
    else:
        return head[-1]


def second_to_miniutesecond(seconds: int) -> str:
    """
    将秒数转换为格式化的分钟和秒数。

    参数：
    sec：要转换的秒数，可以是整数或浮点数。

    返回：
    格式化的分钟和秒数的字符串，格式为“H.MM”。

    示例：
    >>> sec_to_minsec(3600)
    '1.00H'
    >>> sec_to_minsec(1500)
    '0.25H'
    """
    minutes, _ = divmod(seconds, 60)
    hours, minutes = divmod(int(minutes), 60)
    one_min = "%.2f" % (minutes / 60)
    return f"{hours:1d}.{one_min[2]}H"


def division_zero(a, b):
    return a / b if b else 0


async def get_user_avatar(user_id: str, retries: int = 3):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(data["payload"]["user"]["avatar"], timeout=15)
            return r.json()["payload"]["avatar_url"]


async def basicinfo(data: dict) -> dict:
    return {
        "nickname": data["payload"]["user"]["nickname"],
        "level": data["payload"]["stats"]["progression"]["level"],
        "time": second_to_miniutesecond(
            data["payload"]["stats"]["general"]["timeplayed"]
        ),
        "mmr": data["payload"]["stats"]["seasonal"]["ranked"]["mmr"],
    }


async def get_record(data: dict) -> dict:
    general_stats = data["payload"]["stats"]["general"]
    kills, deaths, matchesplayed, assists, wins, losses, knockdown, gadget_destroy = (
        general_stats["kills"],
        general_stats["deaths"],
        general_stats["matchesplayed"],
        general_stats["assists"],
        general_stats["wins"],
        general_stats["losses"],
        general_stats["knockdown"],
        general_stats["gadget_destroy"],
    )

    kd = division_zero(kills, deaths)
    wl = division_zero(wins, losses)
    kpm = division_zero(kills, matchesplayed)

    return {
        "kills": kills,
        "deaths": deaths,
        "matchesplayed": matchesplayed,
        "assists": assists,
        "wins": wins,
        "losses": losses,
        "kd": kd,
        "wl": "%.2f" % wl,
        "kpm": "%.2f" % kpm,
        "knockdown": knockdown,
        "gadget_destroy": gadget_destroy,
    }


async def get_operator(data: dict) -> dict:
    operators = data["payload"]["stats"]["operators"].copy()
    most_played = sorted(operators, key=lambda l1: l1["timeplayed"], reverse=True)[0]
    best_kd = sorted(
        operators,
        key=lambda l2: (division_zero(l2["kills"], l2["deaths"]), l2["timeplayed"]),
        reverse=True,
    )[0]
    best_wl = sorted(
        operators,
        key=lambda l3: (division_zero(l3["wins"], l3["losses"]), l3["timeplayed"]),
        reverse=True,
    )[0]
    return {
        "most_played": most_played,
        "best_kd": best_kd,
        "best_wl": best_wl,
    }
# def con(*args) -> str:
#     r = "".join(arg + "\n" for arg in args)
#     return r[:-1]


def gen_stat(data: dict) -> str:
    return con(
        "KD：%.2f"
        % (
                data["payload"]["stats"]["general"]["kills"]
                / data["payload"]["stats"]["general"]["deaths"]
        )
        if data["payload"]["stats"]["general"]["deaths"] != 0
        else (
                "KD：%d/%d"
                % (
                    data["payload"]["stats"]["general"]["kills"],
                    data["payload"]["stats"]["general"]["deaths"],
                )
        ),
        "胜负比：%.2f"
        % (
                data["payload"]["stats"]["general"]["wins"]
                / data["payload"]["stats"]["general"]["losses"]
        )
        if data["payload"]["stats"]["general"]["losses"] != 0
        else (
                "胜负比：%d/%d"
                % (
                    data["payload"]["stats"]["general"]["wins"],
                    data["payload"]["stats"]["general"]["losses"],
                )
        ),
        "总场数：%d" % data["played"],
        "游戏时长：%.1f" % (data["timePlayed"] / 3600),
    )


def base(data: dict) -> str:
    return con(
        data["payload"]["user"]["nickname"],
        "等级：" + data["payload"]["stats"]["progression"]["level"],
        "",
        "综合数据",
        gen_stat(data["StatGeneral"][0]),
    )


def pro(data: dict) -> str:
    r = ""
    return con(
        data["username"],
        r,
        "",
        f"排位MMR：{data['payload']['stats']['seasonal']['ranked']['mmr']:d}\n休闲MMR：{data['payload']['stats']['seasonal']['casual']['mmr']:d}\n隐藏Rank：{rank(data['payload']['stats']['seasonal']['ranked']['mmr'])}",
        f"爆头击杀率：{data['payload']['stats']['general']['headshots'] / data['payload']['stats']['general']['kills']:.2f}",
    )


def gen_op(data: dict) -> str:
    return con(
        f"胜负比：{data['payload']['stats']['operators']['id']}",
        f"胜负比：{(data['payload']['stats']['operators']['wins'] / data['payload']['stats']['operators']['losses']):.2f}",
        f"KD：{(data['kills'] / data['deaths']):.2f} {data['kills']:d}/{data['deaths']:d}",
        f"游戏时长: {(data['payload']['stats']['operators']['timePlayed'] / 3600):.2f}小时",
    )


def operators(data: dict) -> str:
    ops: list = data["payload"]["stats"]["operators"]
    ops.sort(reverse=True, key=lambda x: x["wins"] + x["losses"])
    r = data["id"] + "常用干员数据："
    for op in ops[:6]:
        r = con(r, "", gen_op(op))
    return r


def recently_played(data: dict) -> str:
    recently_ranked = [

    ]
    update_at_time = [
        str(data["update_at"]["hours"]),
        str(data["update_at"]["minutes"])
    ]
    return con(
        ".".join(update_at_date)+" "+":".join(update_at_time),
        "胜/负：%d/%d" % (data["won"], data["lost"]),
        "KD：%.2f %d/%d" % ((data["kills"]/data["deaths"]), data["kills"], data["deaths"]
                           ) if data["deaths"] != 0 else ("KD：- %d/%d" % (data["kills"], data["deaths"]))
    )

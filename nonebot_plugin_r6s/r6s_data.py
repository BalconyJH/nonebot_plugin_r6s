from datetime import datetime

import httpx
import asyncio


def rank(mmr: int) -> str:
    if mmr > 4000:
        return "冠军"
    rank_tiers = {
        500: "紫铜",
        1000: "黄铜",
        1500: "白银",
        2000: "黄金",
        2500: "白金",
        3000: "翡翠",
        3500: "钻石",
    }
    tier = next(key for key in rank_tiers if key > mmr)
    rank_division = {
        0: "V",
        100: "IV",
        200: "III",
        300: "II",
        400: "I"
    }
    division = next(key for key in rank_division if key > mmr % 500)
    return rank_tiers[tier] + rank_division[division]


async def get_data(usr_name: str, trytimes=6) -> dict:
    if trytimes == 0:
        return ""
    try:
        url = f"https://www.r6s.cn/Stats?username={usr_name}&platform="
        headers = {
            'Host': 'www.r6s.cn',
            'referer': 'https://www.r6s.cn',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
        if not response.json() and trytimes == 1:
            return "Not Found"
        r: dict = response.json()
        if not (r.get("username") or r.get("StatCR")):
            trytimes -= 1
            await asyncio.sleep(0.5)
            r = await get_data(usr_name, trytimes=trytimes)
        return r
    except:
        trytimes -= 1
        await asyncio.sleep(0.5)
        r = await get_data(usr_name, trytimes=trytimes)
        return r


def con(*args) -> str:
    r = "".join(arg + "\n" for arg in args)
    return r[:-1]


def gen_stat(data: dict) -> str:
    return con(
        "KD：%.2f" % (data["kills"] / data["deaths"]) if data["deaths"] != 0 else (
            "KD：%d/%d" % (data["kills"], data["deaths"])),
        "胜负比：%.2f" % (data["won"] / data["lost"]) if data["lost"] != 0 else (
            "胜负比：%d/%d" % (data["won"], data["lost"])),
        "总场数：%d" % data["played"],
        "游戏时长：%.1f" % (data["timePlayed"] / 3600)
    )


def base(data: dict) -> str:
    return con(
        data["username"],
        "等级："+str(data["Basicstat"][0]["level"]), "",
        "综合数据",
        gen_stat(data["StatGeneral"][0])
    )


def pro(data: dict) -> str:
    r = ""
    casual = True
    for stat in data["StatCR"]:
        r = con(r, "休闲数据" if casual else "\n排位数据", gen_stat(stat))
        casual = False
    return con(
        data["username"],
        r,
        "",
        "休闲隐藏MMR：%d" % data["Casualstat"]["mmr"]
        if casual
        else "排位MMR：%d\n隐藏MMR：%d\n隐藏Rank：%s"
        % (
            data["Basicstat"][0]["mmr"],
            data["Casualstat"]["mmr"],
            rank(data["Casualstat"]["mmr"]),
        ),
        "爆头击杀率：%.2f"
        % (
            data["StatGeneral"][0]["headshot"]
            / data['StatGeneral'][0]['kills']
        ),
    )


def gen_op(data: dict) -> str:
    return con(
        "干员："+data["name"],
        "胜负比：%.2f" % (data["won"]/data["lost"]),
        "KD：%.2f %d/%d" % ((data["kills"]/data["deaths"]),
                           data["kills"], data["deaths"]),
        "游戏时长：%.2f" % (data["timePlayed"] / 3600)
    )


def operators(data: dict) -> str:
    ops: list = data["StatOperator"]
    ops.sort(reverse=True, key=lambda x: x["won"]+x["lost"])
    r = data["username"]+"常用干员数据："
    for op in ops[:6]:
        r = con(r, "", gen_op(op))
    return r


def gen_play(data: dict) -> str:
    last_rank_time = datetime.fromtimestamp(data["time"] / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')
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


def plays(data: dict) -> str:
    r = data["username"]+"近期对战："
    for stat in data["StatCR2"][:3]:
        r = con(r, "", gen_play(stat))
    return r

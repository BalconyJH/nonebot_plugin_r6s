from httpx import AsyncClient
import ujson as json
import asyncio
import re


from .r6s_stats import get_stats


async def get_id(name: str):
    id = await get_stats(name)
    if id:
        return id

    '''
    # 从R6_ground搜索获取ubi_id
    async with AsyncClient() as client:
        resp = await client.get("https://global.r6sground.cn/cache/%s/search" % name)
    data = resp.json()
    if data["hits"]:
        return data["hits"]["u0"]["uplayMainId"]
    '''

    return "Not Found"


async def _get_data(ubi_id: str) -> dict:
    async with AsyncClient() as client:
        resp = await client.get("https://global.r6sground.cn/stats/%s/data" % ubi_id)
    datas = re.split(r"(data: )", resp.text)
    rdatas = {}
    for d in datas:
        if d[:1] != "{":
            pass
        else:
            d = d.replace("!46$", "false")
            d = d.replace("!47$", "true")
            d_jdson = json.loads(d)
            rdatas[d_jdson["key"]] = d_jdson["data"]
    if not rdatas.get("userMainData"):
        return "Not Found"
    elif not rdatas["userMainData"].get("!15$_!6$s:!5$"):
        return "Not Found"  # 应该是有ubi账号但没打过R6
    return rdatas


async def get_data(name: str, retry: int = 3) -> dict:
    ubi_id = await get_id(name)
    if ubi_id == "Not Found" or not ubi_id:
        return "Not Found"
    rdata = await _get_data(ubi_id)
    while rdata == "Not Found" and retry != 0:
        asyncio.sleep(1)
        rdata = await _get_data(ubi_id)
        retry -= 1
    if retry == 0:
        return "Not Found"
    return trans_data(rdata)


def trans_data(data: dict) -> dict:
    rdict = {
        "username": data["userMainData"]["UsernameOnPlatform"],
        "Casualstat": {
            "mmr": int(data["userMainData"]["pvp_casual_s!6$_mean"])
        },
        "Basicstat": [
            {
                "level": data["userMainData"]["!100$"],
                "mmr": int(data["userMainData"]["!26$_!28$_mmr"])
            }
        ],
        "StatGeneral": [
            {
                "kills": data["userMainData"]["!15$_!6$s:!5$"],
                "deaths": data["userMainData"]["!15$_!7$:!5$"],
                "won": data["userMainData"]["!15$_!19$!8$:!5$"],
                "lost": data["userMainData"]["!15$_!19$!9$:!5$"],
                "played": data["userMainData"]["!15$_!19$!32$:!5$"],
                "timePlayed": data["userMainData"]["!15$_!31$:!5$"],
                "headshot": data["userMainData"]["!15$_!14$:!5$"],
            }
        ],
        "StatCR": [
            {
                "kills": data["userMainData"]["casualpvp_!6$s:!5$"],
                "deaths": data["userMainData"]["casualpvp_!7$:!5$"],
                "won": data["userMainData"]["casualpvp_!19$!8$:!5$"],
                "lost": data["userMainData"]["casualpvp_!19$!9$:!5$"],
                "played": data["userMainData"]["casualpvp_!19$!32$:!5$"],
                "timePlayed": data["userMainData"]["casualpvp_!31$:!5$"],
            }
        ]
    }
    if data["userMainData"].get("!26$edpvp_!6$s:!5$"):
        rdict["StatCR"].append(
            {
                "kills": data["userMainData"].get("!26$edpvp_!6$s:!5$"),
                "deaths": data["userMainData"].get("!26$edpvp_!7$:!5$"),
                "won": data["userMainData"].get("!26$edpvp_!19$!8$:!5$"),
                "lost": data["userMainData"].get("!26$edpvp_!19$!9$:!5$"),
                "played": data["userMainData"].get("!26$edpvp_!19$!32$:!5$"),
                "timePlayed": data["userMainData"].get("!26$edpvp_!31$:!5$"),
            }
        )
    return rdict

import httpx
import asyncio
import re
import json


async def get_data_from_r6scn(user_name: str, trytimes=6) -> dict:
    if trytimes == 0:
        return ""
    try:
        base_url = "https://www.r6s.cn/Stats?username="
        url = base_url + str(user_name) + '&platform='
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
            r = await get_data_from_r6scn(user_name, trytimes=trytimes)
        return r
    except:
        trytimes -= 1
        await asyncio.sleep(0.5)
        r = await get_data_from_r6scn(user_name, trytimes=trytimes)
        return r


async def get_data_from_r6sground(user_name: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://global.r6sground.cn/stats/%s/data" % user_name)
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


async def get_data_from_r6stats(user_name: str) -> dict:
    # parse user_name to ubi_id first
    ubi_id = user_name  # todo
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://r6stats.com/api/stats/{ubi_id}?queue=true")
    # todo

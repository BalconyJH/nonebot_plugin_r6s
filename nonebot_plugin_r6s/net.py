import httpx
import asyncio
import re
import json

from nonebot import get_driver, logger

AUTH = (get_driver().config.r6db_user_id, get_driver().config.r6db_password)


async def get_data_from_r6scn(user_name: str) -> dict:
    url = "https://api.r6s.cn/apistats/stats/getprofilesbyuplayname"
    # url_base_on_userid = "https://api.r6s.cn/apistats/stats/fullstats" # 使用userid进行查询,作为备用接口
    headers = {
        'User-Agent': 'PostmanRuntime/7.30.0',
        'Referer': 'https://test.r6s.cn',
        'Accept': '*/*',
        'Host': 'api.r6s.cn',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        "params": user_name
    }

    try:
        session = httpx.AsyncClient(trust_env=True)
        response = await session.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise ConnectionError(f"API returned status code {response.status_code}")
    except Exception as e:
        logger.warning("未知请求错误")
        raise RuntimeError(f"Request failed: {str(e)}") from e


async def get_data_from_r6sground(user_name: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://global.r6sground.cn/stats/{user_name}/data")
    datas = re.split(r"(data: )", resp.text)
    rdatas = {}
    for d in datas:
        if d[:1] == "{":
            d = d.replace("!46$", "false")
            d = d.replace("!47$", "true")
            d_jdson = json.loads(d)
            rdatas[d_jdson["key"]] = d_jdson["data"]
    if not rdatas.get("userMainData") or rdatas["userMainData"].get("!15$_!6$s:!5$"):
        return {user_name: f"{user_name}", "error": "Not Found"}
    return rdatas


async def get_data_from_r6stats(user_name: str) -> dict:
    # parse user_name to ubi_id first
    ubi_id = user_name  # todo
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://r6stats.com/api/stats/{ubi_id}?queue=true")
    # todo


async def get_data_from_r6db(user_name: str) -> dict:
    async with httpx.AsyncClient(timeout=10, auth=AUTH, follow_redirects=True) as client:
        resp = await client.get(f"https://api.statsdb.net/r6/pc/player/{user_name}")
    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 404:
        raise ConnectionError(f"")
    elif resp.status_code == 401:
        logger.warning("请在.env文件填写正确的r6db_user_id和r6db_password")
        raise ConnectionError({"error": "Not authorized"})
    elif resp.status_code == 429:
        logger.warning("API达到请求上限")
        raise ConnectionRefusedError("API request limit reached")
    else:
        return {user_name: f"{user_name}", "error": "Error"}



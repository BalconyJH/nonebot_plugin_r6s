import asyncio
import json
import re
from typing import Union, Optional

import aiohttp
import httpx
from nonebot import get_driver
from nonebot.log import logger

from .config import plugin_config

AUTH = (get_driver().config.r6db_user_id, get_driver().config.r6db_password)
max_retry = plugin_config.r6s_max_retry


async def get_data_from_r6scn(user_name: str) -> dict:
    url = "https://api.r6s.cn/apistats/stats/getprofilesbyuplayname"
    # url_base_on_userid = "https://api.r6s.cn/apistats/stats/fullstats" # 使用userid进行查询,作为备用接口
    headers = {
        "User-Agent": "PostmanRuntime/7.30.0",
        "Referer": "https://test.r6s.cn",
        "Accept": "*/*",
        "Host": "api.r6s.cn",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"params": user_name}

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


async def get_data_from_r6ground(user_name: str) -> dict:
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


async def get_data_from_r6db(user_name: str) -> Union[dict, str, None]:
    async with httpx.AsyncClient(
            timeout=10, auth=AUTH, follow_redirects=True
    ) as client:
        resp = await client.get(f"https://api.statsdb.net/r6/pc/player/{user_name}")
    if resp.status_code == 200:
        return resp.json()
    elif resp.status_code == 404:
        return None
    elif resp.status_code == 401:
        logger.warning("请在.env文件填写正确的r6db_user_id和r6db_password")
        raise ConnectionError({"error": "Not authorized"})
    elif resp.status_code == 429:
        logger.warning("API达到请求上限")
        raise ConnectionRefusedError("API request limit reached")


async def get_data_from_r6racker(user_name: str, proxy: str) -> Optional[dict]:
    url_list = [
        f"https://r6.tracker.network/profile/pc/{user_name}",
        f"https://r6.tracker.network/profile/pc/{user_name}/seasons",
    ]

    for retry_count in range(max_retry):
        try:
            async with aiohttp.ClientSession() as session:

                async def fetch(url):
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                                      "like Gecko) Chrome/110.0.0.0 Safari/537.36"
                    }
                    async with session.get(url, headers=headers, proxy=proxy) as resp:
                        resp.raise_for_status()
                        return await resp.text()

                results = await asyncio.gather(*[fetch(url) for url in url_list])
                return {"basic_data": results[0], "seasons_data": results[1]}
        except aiohttp.ClientError:
            logger.warning(f"请求错误，重试次数：{retry_count + 1}")
            await asyncio.sleep(1)
    return None

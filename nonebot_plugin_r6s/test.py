import asyncio

import httpx


async def get_data_from_r6scn(user_name: str, trytimes=6) -> dict:
    # if trytimes == 0:
    #     return ""
    # try:
    #     url = f"https://www.r6s.cn/Stats?username={user_name}&platform="
    #     headers = {
    #         'Host': 'www.r6s.cn',
    #         'referer': 'https://www.r6s.cn',
    #         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
    #         'x-requested-with': 'XMLHttpRequest'
    #     }
    #     async with httpx.AsyncClient() as client:
    #         response = await client.get(url, headers=headers)
    #     if not response.json() and trytimes == 1:
    #         return "Not Found"
    #     r: dict = response.json()
    #     if not (r.get("username") or r.get("StatCR")):
    #         trytimes -= 1
    #         await asyncio.sleep(0.5)
    #         r = await get_data_from_r6scn(user_name, trytimes=trytimes)
    #     return r
    # except:
    #     trytimes -= 1
    #     await asyncio.sleep(0.5)
    #     r = await get_data_from_r6scn(user_name, trytimes=trytimes)
    #     return r
    url = "https://api.r6s.cn/apistats/stats/getprofilesbyuplayname"
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
            raise Exception(f"API returned status code {response.status_code}")
    except Exception as e:
        raise Exception(f"Request failed: {str(e)}") from e


# get_data_from_r6scn(user_name="BalconyJH")
def main():
    loop = asyncio.get_event_loop()
    task = get_data_from_r6scn(user_name="BalconyJH")

    print(loop.run_until_complete(task))


if __name__ == '__main__':
    main()
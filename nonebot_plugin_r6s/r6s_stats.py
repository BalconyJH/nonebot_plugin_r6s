from httpx import AsyncClient


# 从R6stats获取ubi_id或者标准信息
async def get_stats(name: str, full_return: bool = False):
    async with AsyncClient() as client:
        resp = await client.get("https://r6stats.com/api/player-search/%s/pc" % name)
    data = resp.json()["data"]
    if data:
        if full_return:
            return data
        else:
            return data[0]["ubisoft_id"]
    else:
        return False

from httpx import AsyncClient


# 从R6stats获取ubi_id或者标准信息
async def get_stats(name: str, full_return: bool = False):
    async with AsyncClient() as client:
        resp = await client.get(f"https://r6stats.com/api/player-search/{name}/pc")
    if data := resp.json()["data"]:
        return data if full_return else data[0]["ubisoft_id"]
    else:
        return False

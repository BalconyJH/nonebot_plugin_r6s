import aiofiles
import aiohttp


async def download_res_async(url, path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            async with aiofiles.open(path, 'wb') as file:
                async for chunk in response.content.iter_chunked(1024):
                    await file.write(chunk)
from pathlib import Path

import aiohttp
from tqdm import tqdm

from ..config import plugin_config

path = Path(__file__).parent / "test" / "font.ttc"

url = 'https://media.githubusercontent.com/media/BalconyJH/Font/main/font.ttc'
proxy = plugin_config.r6s_proxy


async def download_res_async(url, path, proxy):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy) as response:
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True, desc=os.path.split(str(path))[1])
            with open(path, 'wb') as file:
                while True:
                    chunk = await response.content.read(block_size)
                    if not chunk:
                        break
                    progress_bar.update(len(chunk))
                    file.write(chunk)
            progress_bar.close()

import os
from io import BytesIO
from pathlib import Path
from typing import Optional

import PIL
import aiohttp
from PIL import Image as IMG
from PIL.Image import Image
from nonebot import logger
from tqdm import tqdm

from ..config import plugin_config

path = Path(__file__).parent / "test" / "font.ttc"

url = 'https://media.githubusercontent.com/media/BalconyJH/Font/main/font.ttc'
proxy = plugin_config.r6s_proxy


async def download_file_async(url: str, path: Optional[str], proxy=proxy) -> bool:
    """异步下载文件。

    Args:
        url (str): 文件的 URL。
        path (str): 文件保存路径。
        proxy (str): HTTP 代理地址。

    Returns:
        bool: 表示文件下载完成。
    """
    try:
        if path is None:
            cache_dir = plugin_config.r6s_cache_dir
            filename = os.path.basename(url)
            path = os.path.join(cache_dir, filename)

        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy) as response:
                total_size = int(response.headers.get('content-length', 0))
                block_size = 1024

                progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True,
                                    desc=os.path.split(str(path))[1] if path else url)
                with open(path, 'wb') as file:
                    while True:
                        chunk = await response.content.read(block_size)
                        if not chunk:
                            break
                        progress_bar.update(len(chunk))
                        file.write(chunk)
                progress_bar.close()

                return True
    except (aiohttp.ClientError, OSError) as e:
        logger.error(f"Failed to download file from {url}. Error: {str(e)}")
        return False


async def download_image_async(url: str, proxy=proxy) -> Image:
    """异步下载图片。

    Args:
        url (str): 图片的 URL。
        proxy (str): HTTP 代理地址。

    Returns:
        PIL.Image.Image: 表示下载的图片。
    """
    try:
        # 使用 aiohttp 发起 HTTP 请求
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy) as response:
                total_size = int(response.headers.get('content-length', 0))
                block_size = 1024

                progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True,
                                    desc=url)
                img_bytes = BytesIO()
                while True:
                    chunk = await response.content.read(block_size)
                    if not chunk:
                        break
                    progress_bar.update(len(chunk))
                    img_bytes.write(chunk)
                # 将 BytesIO 对象的读取位置移到开头
                img_bytes.seek(0)
                img = IMG.open(img_bytes)
                progress_bar.close()

                return img
    except (aiohttp.ClientError, PIL.UnidentifiedImageError) as e:
        # 捕获异常，返回 None
        logger.error(f"Failed to download image from {url}. Error: {str(e)}")

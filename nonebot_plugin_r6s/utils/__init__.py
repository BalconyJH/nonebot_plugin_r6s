import asyncio
from pathlib import Path

from nonebot import logger

from .image import init_basic_info_image
from ..config import plugin_config
from ..utils.res import download_res_async


async def get_r6s_adapter(adapter=plugin_config.r6s_adapters, *args, **kwargs):
    if adapter == "r6tracker":
        from ..net import get_data_from_r6racker

        r6s_adapter = get_data_from_r6racker(*args, **kwargs)
    elif adapter == "r6db":
        from ..net import get_data_from_r6db

        r6s_adapter = get_data_from_r6db(*args, **kwargs)
    else:
        raise ValueError("Invalid driver specified")
    return r6s_adapter


async def network_connectivity():
    default_name = "MacieJay"
    try:
        await get_r6s_adapter(default_name, plugin_config.r6s_max_retry),
    except ConnectionError:
        return False
    else:
        return True


async def initialize():
    async def generate_default_image():
        try:
            await init_basic_info_image()
            return True
        except FileExistsError:
            return False

    async def verify_font():
        """检查config中字体文件是否存在"""
        try:
            if not Path(plugin_config.r6s_font).exists():
                await download_res_async(
                    "https://media.githubusercontent.com/media/BalconyJH/Font/main/font.ttc",
                    plugin_config.r6s_font,
                    plugin_config.r6s_proxy,
                )
        except FileNotFoundError as e:
            logger.error(f"字体文件不存在且下载失败：{e}")
            return False

    async def verify_resource_integrity():
        try:
            results = await asyncio.gather(
                network_connectivity(),
                generate_default_image(),
            )
            if results[0] is False:
                logger.warning("查询源连接失败")
            if results[1] is False:
                logger.warning("生成预设图片失败")
            logger.info("初始化成功")

        except Exception as e:
            logger.error(f"初始化失败：{e}")


def on_startup():

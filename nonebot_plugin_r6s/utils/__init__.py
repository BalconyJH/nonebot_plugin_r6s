import asyncio
import importlib
from pathlib import Path

from nonebot import logger

from .image import init_basic_info_image
from ..config import plugin_config
from ..utils.res import download_res_async

FONT_PATH = plugin_config.r6s_font
PROXY = plugin_config.r6s_proxy
DEFAULT_NAME = plugin_config.r6s_default_name
MAX_RETRY = plugin_config.r6s_max_retry


async def get_r6s_adapter(adapter=plugin_config.r6s_adapters, *args, **kwargs):
    """
    根据指定的适配器获取R6S游戏数据。

    Args:
        adapter (str): 适配器名称。
        *args: 传递给适配器的位置参数。
        **kwargs: 传递给适配器的关键字参数。

    Returns:
        获取到的游戏数据。

    Raises:
        ValueError: 无效的适配器名称。
    """
    net_module = "..net"
    # 定义适配器名称与模块路径、函数名的映射关系
    adapter_map = {
        "r6tracker": (net_module, "get_data_from_r6racker"),
        "r6db": (net_module, "get_data_from_r6db"),
        "r6stats": (net_module, "get_data_from_r6stats"),
        "r6ground": (net_module, "get_data_from_r6ground"),
        "r6scn": (net_module, "get_data_from_r6scn"),
    }
    # 获取适配器的模块路径和函数名，并动态导入所需的模块和函数
    module_path, func_name = adapter_map.get(adapter)
    module = importlib.import_module(module_path, package=__package__)
    adapter_func = getattr(module, func_name, None)
    if adapter_func is None:
        # 如果适配器名称无效，则抛出异常
        raise ValueError("Invalid adapter")
    # 调用适配器实现并返回结果
    return await adapter_func(*args, **kwargs)


async def check_font_exists(font_path: str) -> bool:
    """检查指定路径下的字体文件是否存在"""
    return Path(font_path).exists()


class InitR6sPlugin:
    @staticmethod
    async def network_connectivity():
        """检查网络连接"""
        try:
            await get_r6s_adapter(DEFAULT_NAME, MAX_RETRY)
        except ConnectionError:
            return False
        else:
            return True

    @staticmethod
    async def generate_default_image():
        """生成默认图片"""
        try:
            await init_basic_info_image()
            return True
        except FileExistsError:
            return False

    @staticmethod
    async def verify_font():
        """检查字体文件是否存在"""
        try:
            font_exists = await check_font_exists(FONT_PATH)
            if not font_exists:
                await download_res_async(
                    "https://media.githubusercontent.com/media/BalconyJH/Font/main/font.ttc",
                    FONT_PATH,
                    PROXY,
                )
            return True
        except (FileNotFoundError, asyncio.TimeoutError):
            return False

    @staticmethod
    async def verify_resource_integrity():
        """检查资源完整性"""
        try:
            connectivity_result, image_result, font_result = await asyncio.gather(
                InitR6sPlugin.network_connectivity(),
                InitR6sPlugin.generate_default_image(),
                InitR6sPlugin.verify_font(),
            )
            if connectivity_result is False:
                logger.warning("查询源连接失败")
            if image_result is False:
                logger.warning("生成预设图片失败")
            if font_result is False:
                logger.warning("字体文件校验失败")
            if all([connectivity_result, image_result, font_result]):
                logger.info("初始化成功")
                return True
            else:
                logger.warning("初始化失败")
                return False
        except Exception as e:
            logger.exception(f"初始化失败：{e}")
            return False

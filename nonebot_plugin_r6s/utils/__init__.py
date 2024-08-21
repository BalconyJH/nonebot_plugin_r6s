import asyncio
import json
import os
from functools import wraps
from pathlib import Path
from time import monotonic
from types import SimpleNamespace
from typing import Callable, Any

import aiohttp
from aiofiles import open
from nonebot import logger
from siegeapi import Auth


# async def get_r6s_adapter(adapter=plugin_config.r6s_adapters, *args, **kwargs):
#     """
#     根据指定的适配器获取R6S游戏数据。
#
#     Args:
#         adapter (str): 适配器名称。
#         *args: 传递给适配器的位置参数。
#         **kwargs: 传递给适配器的关键字参数。
#
#     Returns:
#         获取到的游戏数据。
#
#     Raises:
#         ValueError: 无效的适配器名称。
#     """
#     net_module = "..net"
#     # 定义适配器名称与模块路径、函数名的映射关系
#     adapter_map = {
#         "r6tracker": (net_module, "get_data_from_r6racker"),
#         "r6db": (net_module, "get_data_from_r6db"),
#         "r6stats": (net_module, "get_data_from_r6stats"),
#         "r6ground": (net_module, "get_data_from_r6ground"),
#         "r6scn": (net_module, "get_data_from_r6scn"),
#     }
#     # 获取适配器的模块路径和函数名，并动态导入所需的模块和函数
#     module_path, func_name = adapter_map.get(adapter)
#     module = importlib.import_module(module_path, package=__package__)
#     adapter_func = getattr(module, func_name, None)
#     if adapter_func is None:
#         # 如果适配器名称无效，则抛出异常
#         raise ValueError("Invalid adapter")
#     # 调用适配器实现并返回结果
#     return await adapter_func(*args, **kwargs)


def check_font_exists(font_path: str) -> bool:
    """检查指定路径下的字体文件是否存在"""
    return Path(font_path).exists()


# def on_startup():
#     """初始化插件"""
#
#     async def network_connectivity():
#         """检查网络连接"""
#         try:
#             await get_r6s_adapter(DEFAULT_NAME, MAX_RETRY)
#         except ConnectionError:
#             return False
#         else:
#             return True
#
#     async def generate_default_image():
#         """生成默认图片"""
#         try:
#             await init_basic_info_image()
#             return True
#         except FileExistsError:
#             return False
#
#     async def verify_font():
#         """检查字体文件是否存在"""
#         try:
#             font_exists = await check_font_exists(FONT_PATH.join("font.ttc"))
#             if not font_exists:
#                 await download_res_async(
#                     "https://media.githubusercontent.com/media/BalconyJH/Font/main/font.ttc",
#                     FONT_PATH,
#                     PROXY,
#                 )
#             return True
#         except (FileNotFoundError, asyncio.TimeoutError):
#             return False
#
#     try:
#         connectivity_result, image_result, font_result = await asyncio.gather(
#             network_connectivity(),
#             generate_default_image(),
#             verify_font(),
#         )
#         if connectivity_result is False:
#             logger.warning("查询源连接失败")
#         if image_result is False:
#             logger.warning("生成预设图片失败")
#         if font_result is False:
#             logger.warning("字体文件校验失败")
#         if all([connectivity_result, image_result, font_result]):
#             logger.info("初始化成功")
#             return True
#         else:
#             logger.warning("初始化失败")
#             return False
#     except Exception as e:
#         logger.exception(f"初始化失败：{e}")
#         return False


class R6sAuth(Auth):
    @staticmethod
    def get_salt_token(email: str, password: str, salt: str = "r6s") -> str:
        # 调用基类的方法生成 Base64 编码的字符串
        basic_token = Auth.get_basic_token(email, password)
        # 在生成的 Base64 字符串后面附加传入的额外字符串
        return basic_token + salt

    @staticmethod
    def get_origin_token(salt_token: str, salt: str) -> str:
        return salt_token[: -len(salt)]


def log_return_msg(func: Callable) -> Callable:
    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        result = await func(*args, **kwargs)
        if isinstance(result, tuple) and isinstance(result[-1], str):
            logger.debug(f"Function '{func.__name__}' returned message: {result[-1]}")
        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        result = func(*args, **kwargs)
        if isinstance(result, tuple) and isinstance(result[-1], str):
            logger.debug(f"Function '{func.__name__}' returned message: {result[-1]}")
        return result

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def create_trace_config() -> aiohttp.TraceConfig:
    """
    Creates a TraceConfig object and binds the start and end request callbacks.

    Returns:
        aiohttp.TraceConfig: Configured trace config with callbacks.
    """

    async def _on_request_start(
        session: aiohttp.ClientSession,
        trace_config_ctx: SimpleNamespace,
        params: aiohttp.TraceRequestStartParams,
    ):
        logger.debug(f"Starting request: {params.method} {params.url}")
        trace_config_ctx.start_time = monotonic()

    async def _on_request_end(
        session: aiohttp.ClientSession,
        trace_config_ctx: SimpleNamespace,
        params: aiohttp.TraceRequestEndParams,
    ):
        elapsed_time = monotonic() - trace_config_ctx.start_time
        logger.debug(
            f"Ending request: {params.response.status} {params.url} - Time elapsed: "
            f"{elapsed_time:.2f} seconds"
        )

    trace_config = aiohttp.TraceConfig()
    trace_config.on_request_start.append(_on_request_start)
    trace_config.on_request_end.append(_on_request_end)
    return trace_config


def drop_file(path: Path) -> None:
    """
    Delete the file at the specified path if it exists and is a file.

    Args:
        path (Path): The path to the file to be deleted.
    """
    if path.is_file():
        os.remove(path)
        logger.info(f"File {path.name} deleted.")
    elif path.exists():
        logger.info(f"{path} is not a file.")
    else:
        logger.info(f"{path} does not exist.")


async def load_json_file(path: Path) -> dict:
    """
    Asynchronously load and parse a JSON file from the specified path.

    Args:
        path (Path): The path to the JSON file.

    Returns:
        dict: The parsed JSON data as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist at the specified path.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    async with open(path, encoding="utf-8") as f:
        return json.loads(await f.read())

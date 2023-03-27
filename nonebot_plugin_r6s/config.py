from typing import Optional

from nonebot import get_driver
from pydantic import BaseSettings, Extra
from nonebot import get_driver
from .net import get_data_from_r6racker


class Config(BaseSettings, extra=Extra.ignore):
    default_name: str = "MacieJay"
    r6s_max_retry: int = 3
    r6s_proxy: Optional[str] = None
    r6s_db_username: Optional[str] = None
    r6s_db_password: Optional[str] = None
    r6s_adapters: Optional[str] = "r6tracker"


global_config = get_driver().config
plugin_config = Config.parse_obj(global_config)

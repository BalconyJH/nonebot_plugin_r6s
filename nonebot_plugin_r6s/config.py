from pathlib import Path
from typing import Optional

from nonebot import get_driver
from pydantic import BaseSettings, Extra, root_validator


class Config(BaseSettings, extra=Extra.ignore):
    r6s_default_name: str = "MacieJay"
    r6s_max_retry: int = 3
    r6s_proxy: Optional[str]
    r6s_db_username: Optional[str]
    r6s_db_password: Optional[str]
    r6s_adapters: Optional[str]
    r6s_font: Optional[str] = None
    r6s_cache_dir: Optional[str] = None

    @root_validator("r6s_font")
    def set_default_values(cls, values):
        if not values.get("r6s_font"):
            values["r6s_font"] = str(
                Path(__file__).parent / "fonts"
            )
        if not values.get("r6s_cache_dir"):
            values["r6s_cache_dir"] = str(
                Path(__file__).parent / "cache"
            )
        if not values.get("r6s_adapters"):
            values["r6s_adapters"] = "r6tracker"


global_config = get_driver().config
plugin_config = Config.parse_obj(global_config)

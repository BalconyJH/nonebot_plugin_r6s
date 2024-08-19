from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
import nonebot_plugin_localstore as store
from loguru import logger
from nonebot import get_driver, get_plugin_config
from pydantic import BaseModel, model_validator, field_validator


class Config(BaseModel):
    max_retry: int = 3
    font_name: str = "JetBrains Mono"
    proxy: Optional[str] = None
    resouce_dir: Path = store.get_plugin_data_dir()
    cache_dir: Path = store.get_plugin_cache_dir()
    config_dir: Path = store.get_plugin_config_dir()
    font_path: Path = resouce_dir / "font"
    image_dir: Path = resouce_dir / "image"
    database_dir: Path = resouce_dir / "database"

    @model_validator(mode="after")
    def ensure_directories_exist(self):
        directories = [self.font_path, self.image_dir, self.database_dir]
        for directory in directories:
            logger.debug(f"Ensuring directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
        return self

    @field_validator("proxy")
    def validate_proxy(cls, v: str) -> str:
        parsed_url = urlparse(v)
        if parsed_url.scheme not in {"http", "https"}:
            raise ValueError("Proxy must start with 'http://' or 'https://'.")

        if not parsed_url.hostname or not parsed_url.port:
            raise ValueError(
                "Proxy must include both a valid hostname/IP and a port number."
            )

        logger.info(f"Testing proxy: {v}")
        try:
            httpx.get(
                "http://www.google.com", proxies={"http://": v, "https://": v}
            ).raise_for_status()
        except Exception as e:
            logger.warning(f"Proxy test failed: {e}")

        return v


global_config = get_driver().config
plugin_config = get_plugin_config(Config)

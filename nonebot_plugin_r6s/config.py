from typing import Optional

from pydantic import BaseSettings


class Config(BaseSettings):
    r6s_max_retry: int = 3
    r6s_proxy: Optional[str] = None
    r6s_db_username: Optional[str] = None
    r6s_db_password: Optional[str] = None
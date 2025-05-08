from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import List

class BotSettings(BaseSettings):
    bot_token: SecretStr
    admin_ids: List[int]
    model_config = SettingsConfigDict(env_file='.env', _env_file_encoding='utf-8')


class GuildSettings(BaseSettings):
    guild_id: str
    token: str
    model_config = SettingsConfigDict(env_file='.env', _env_file_encoding='utf-8')

guild_config = GuildSettings()


config = BotSettings()


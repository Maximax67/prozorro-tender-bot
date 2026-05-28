from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    CHAT_ID: int
    MESSAGE_THREAD_ID: int | None = None
    CRON_SECRET: SecretStr

    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: SecretStr

    BUYER_ID: str
    WEBHOOK_URL: HttpUrl | None = None
    WEBHOOK_SECRET: SecretStr | None = None
    MODE: str = "webhook"

    APP_TITLE: str = "Prozorro Tender Bot"
    APP_VERSION: str = "1.0.0"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings(**{})

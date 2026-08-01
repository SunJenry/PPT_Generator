from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ark_api_key: str
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    ark_model: str = "kimi-k2.6"
    tavily_api_key: str
    unsplash_access_key: str = ""


class _LazySettings:
    """Lazy proxy that defers Settings instantiation until first access."""

    def __getattr__(self, name: str):
        return getattr(Settings(), name)


settings = _LazySettings()

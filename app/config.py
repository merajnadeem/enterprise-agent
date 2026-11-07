from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    app_name: str = "Enterprise Agentic AI"
    app_env: str = "development"
    database_url: str
    redis_url: str
    llm_provider: str = "openai"
    fast_model: str
    strong_model: str
    openai_api_key: str | None = None
    azure_search_endpoint: str | None = None
    servicebus_namespace: str | None = None
    otel_service_name: str = "enterprise-agent"
    otel_exporter_otlp_endpoint: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

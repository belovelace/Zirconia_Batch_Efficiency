from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "zirsave"
    ENV: str = "development"
    DATABASE_URL: str | None = None
    REDIS_URL: str = "redis://localhost:6379/0"
    METRICS_PATH: str = "/metrics"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    GRACEFUL_TIMEOUT: int = 30

    class Config:
        env_file = ".env"


settings = Settings()

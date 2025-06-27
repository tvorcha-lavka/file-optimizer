from pydantic_settings import BaseSettings, SettingsConfigDict


class CelerySettings(BaseSettings):
    DEBUG: bool = False

    APP_NAME: str = "file-optimizer"
    BROKER_URL: str = "pyamqp://admin:admin@rabbitmq:5672//"
    RESULT_BACKEND: str = "redis://redis:6379/0"

    CONCURRENCY: int = 2
    MAX_TASKS_PER_CHILD: int = 20

    model_config = SettingsConfigDict(
        env_prefix="CELERY_",
        case_sensitive=True,
    )


celery_settings = CelerySettings()

from pydantic.v1 import BaseSettings


class CelerySettings(BaseSettings):
    APP_NAME: str = "file-optimizer"
    CELERY_BROKER_URL: str = "pyamqp://admin:admin@rabbitmq:5672//"
    CELERY_RESULT_BACKEND: str = "rpc://"


celery_settings = CelerySettings()

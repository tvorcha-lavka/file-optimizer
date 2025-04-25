import logging.config

from celery import Celery  # type: ignore

from core.config.celery import celery_settings
from core.config.log import logging_settings

# Configure Celery
app = Celery(
    main=celery_settings.APP_NAME,
    broker=celery_settings.CELERY_BROKER_URL,
    backend=celery_settings.CELERY_RESULT_BACKEND,
)

app.conf.update(
    broker_connection_retry_on_startup=True,
    accept_content=["json"],
    task_serializer="json",
    timezone="UTC",
)

app.autodiscover_tasks(packages=["tasks"], force=True)

# Configure logging
logging.config.dictConfig(logging_settings.configure())

#!/usr/bin/env python
"""
Entrypoint for all available services of the `tvorcha-lavka-file-optimizer` project.
"""
from argparse import ArgumentParser, RawTextHelpFormatter
from os import environ
from pathlib import Path
from re import sub

from click import style
from dotenv import load_dotenv
from pydantic import BaseModel

from core.celery.client import app
from core.celery.enums import QueueEnum
from core.celery.settings import celery_settings
from core.config.log import logging_settings

BASE_DIR = Path(__file__).parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

ENV_STATE = environ["ENV_STATE"]


def to_snake_case(text: str) -> str:
    if "-" in text:
        return text.replace("-", "_").lower()
    return sub(r"(?<!^)(?=[A-Z])", "_", text).lower()


def to_kebab_case(text: str) -> str:
    if "_" in text:
        return text.replace("_", "-").lower()
    return sub(r"(?<!^)(?=[A-Z])", "-", text).lower()


class CeleryWorkers(BaseModel):
    file_optimizer: list[str]

    @classmethod
    def list(cls) -> list[str]:
        return list(to_kebab_case(key) for key in cls.model_fields.keys())


class CeleryConfig(CeleryWorkers):
    pass


def run_celery(worker: str) -> None:
    celery_config = CeleryConfig(
        file_optimizer=[
            "worker",
            "--pool=%s" % ("solo" if celery_settings.DEBUG else "prefork"),
            "--concurrency=%s" % celery_settings.CONCURRENCY,
            "--queues=%s" % QueueEnum.FILE_OPTIMIZER,
            "--max-tasks-per-child=%s" % celery_settings.MAX_TASKS_PER_CHILD,
            "--hostname=file-optimizer@%h",
            "--loglevel=%s" % logging_settings.LEVEL_CONSOLE,
            "--without-mingle",
            "--without-gossip",
        ],
    )

    log_style = "yellow" if ENV_STATE == "development" else "green"
    message = f"Running celery worker in {ENV_STATE.upper()} mode."

    print(style(message, fg=log_style, bold=True))
    app.start(getattr(celery_config, worker))


def main() -> None:
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter)

    parser.add_argument(
        "--worker",
        required=False,
        choices=(names := CeleryWorkers.list()),
        metavar="<arg>",
        help=f"Runs specified celery worker.\nargs={names}",
    )
    args = parser.parse_args()

    if args.worker:
        run_celery(to_snake_case(args.worker))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

import logging.config
import sys
from copy import copy
from pathlib import Path
from typing import Any, ClassVar, Literal

import click
from pydantic_settings import BaseSettings, SettingsConfigDict

# ----------------------------------------------------------------------------------------------------------------------
# --- Code taken from uvicorn.logging.py module ------------------------------------------------------------------------

TRACE_LOG_LEVEL = 5


class ColorizedFormatter(logging.Formatter):
    """
    A custom log formatter class that:

    * Outputs the LOG_LEVEL with an appropriate color.
    * If a log call includes an `extra={"color_message": ...}` it will be used
      for formatting the output, instead of the plain text message.
    """

    level_name_colors = {
        TRACE_LOG_LEVEL: lambda level_name: click.style(str(level_name), fg="blue"),
        logging.DEBUG: lambda level_name: click.style(str(level_name), fg="cyan"),
        logging.INFO: lambda level_name: click.style(str(level_name), fg="green"),
        logging.WARNING: lambda level_name: click.style(str(level_name), fg="yellow"),
        logging.ERROR: lambda level_name: click.style(str(level_name), fg="red"),
        logging.CRITICAL: lambda level_name: click.style(str(level_name), fg="bright_red"),
    }

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
        use_colors: bool | None = None,
    ):
        if use_colors in (True, False):
            self.use_colors = use_colors
        else:
            self.use_colors = sys.stdout.isatty()
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def color_level_name(self, level_name: str, level_no: int) -> str:
        def default(level_name: str) -> str:
            return str(level_name)  # pragma: no cover

        func = self.level_name_colors.get(level_no, default)
        return func(level_name)  # type: ignore

    def should_use_colors(self) -> bool:
        return True  # pragma: no cover

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        levelname = recordcopy.levelname
        seperator = " " * (8 - len(recordcopy.levelname))
        if self.use_colors:
            levelname = self.color_level_name(levelname, recordcopy.levelno)
            if "color_message" in recordcopy.__dict__:
                recordcopy.msg = recordcopy.__dict__["color_message"]
                recordcopy.__dict__["message"] = recordcopy.getMessage()
        recordcopy.__dict__["levelprefix"] = levelname + ":" + seperator
        return super().formatMessage(recordcopy)


class DefaultFormatter(ColorizedFormatter):
    def should_use_colors(self) -> bool:
        return sys.stderr.isatty()  # pragma: no cover


# --- End of code from uvicorn.logging.py module -----------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------


class NoTracebackWarningFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno == logging.WARNING:
            record.exc_info = None
        return True


class LoggingSettings(BaseSettings):
    LEVEL_CONSOLE: int | str = logging.INFO
    LEVEL_FILE: int | str = logging.WARNING

    PATH: Path = Path("/") / "mnt" / "efs" / "logs" / "file-optimizer"

    FILE_MAX_SIZE: int = 10
    FILE_BACKUP_COUNT: int = 5

    DEFAULT_HANDLERS: ClassVar = Literal[
        "console",
        "file_optimize_errors",
        "file_worker_errors",
    ]

    DEFAULT_FORMATTER: ClassVar = DefaultFormatter(
        fmt="%(levelprefix)s %(message)s",
        use_colors=True,
    )

    model_config = SettingsConfigDict(
        env_prefix="LOGGING_",
        case_sensitive=True,
    )

    @staticmethod
    def to_handlers(
        handlers: list[DEFAULT_HANDLERS] | None = None,
        propagate: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return {
            "handlers": handlers or [],
            "propagate": propagate,
            **kwargs,
        }

    def set_default_formatter_to_loggers(self) -> None:
        for logger_name in logging.root.manager.loggerDict.keys():
            logger = logging.getLogger(logger_name)

            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(self.DEFAULT_FORMATTER)

            logger.handlers = []
            logger.addHandler(handler)
            logger.propagate = False

    def file_handler(self, file_name: str, level: int | str | None = None) -> dict[str, Any]:
        return {
            "formatter": "file",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": self.PATH / file_name,
            "backupCount": self.FILE_BACKUP_COUNT,
            "maxBytes": self.FILE_MAX_SIZE * 1024**2,
            "level": level or self.LEVEL_FILE,
        }

    def configure(self) -> dict[str, Any]:
        self.PATH.mkdir(parents=True, exist_ok=True)
        self.set_default_formatter_to_loggers()
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": DefaultFormatter,
                    "fmt": "%(levelprefix)s %(message)s",
                    "use_colors": True,
                },
                "file": {
                    "()": DefaultFormatter,
                    "fmt": "%(asctime)s %(levelprefix)s %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "filters": {
                "no_traceback_warning": {
                    "()": NoTracebackWarningFilter,
                }
            },
            "handlers": {
                "console": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "level": self.LEVEL_CONSOLE,
                },
                "file_optimize_errors": self.file_handler("optimize-errors.log"),
                "file_worker_errors": self.file_handler("worker-errors.log"),
            },
            "loggers": {
                "celery.optimize": self.to_handlers(["console", "file_optimize_errors"]),
                "celery.worker": self.to_handlers(["console", "file_worker_errors"]),
                "celery.worker.consumer.consumer": self.to_handlers(
                    handlers=["console", "file_worker_errors"],
                    filters=["no_traceback_warning"],
                ),
            },
        }


logging_settings = LoggingSettings()

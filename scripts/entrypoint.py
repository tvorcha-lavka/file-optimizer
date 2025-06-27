#!/usr/bin/env python
"""
Development entrypoint for `file-optimizer` project.

This script runs the Celery application for development purposes.
"""
from core.config.log import logging_settings as settings
from main import app


def main() -> None:
    params = [
        "worker",
        "--pool=solo",
        "--concurrency=2",
        "--queues=file-optimizer.queue",
        "--max-tasks-per-child=20",
        "--hostname=file-optimizer@%h",
        "--loglevel=%s" % settings.LOGGING_LEVEL_CONSOLE,
        "--without-mingle",
        "--without-gossip",
    ]
    app.start(params)


if __name__ == "__main__":
    main()

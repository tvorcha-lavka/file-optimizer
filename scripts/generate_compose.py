#!/usr/bin/env python
"""Generate docker compose files from templates"""
from os import environ
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

ENV_STATE = environ["ENV_STATE"]


def run_jinja() -> None:
    from jinja2 import Environment, FileSystemLoader

    jinja = Environment(loader=FileSystemLoader(BASE_DIR / "docker/templates"))

    for template_name in jinja.list_templates():
        jinja_template = jinja.get_template(template_name)

        folder = BASE_DIR / ("docker/development" if "dev" in template_name else "docker")
        folder.mkdir(parents=True, exist_ok=True)

        output_file_name = template_name.replace(".j2", ".yml")
        output_file_path = folder / output_file_name

        with open(output_file_path, "w") as f:
            print(f"Generating: {output_file_name}")

            f.write(jinja_template.render(env=environ))
            print(f"file:///{output_file_path.as_posix()}")


if __name__ == "__main__":
    run_jinja()

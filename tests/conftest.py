from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from typing import Any, Generator
from uuid import UUID

import pytest
from pydantic.v1 import BaseSettings

from core.celery.client import app
from core.config.file import image_settings
from processors import ImageOptimizeProcessor


@dataclass
class File:
    path: Path
    type: str  # noqa: VNE003


@dataclass
class ProcessedFileBound:
    original: File
    _150x200: File
    _450x600: File
    _675x900: File


class SettingsForTests(BaseSettings):
    USER_ID: UUID = UUID("00000000-0000-0000-0000-000000000001")
    SESSION_ID: UUID = UUID("00000000-0000-0000-0000-000000000002")
    PRODUCT_ID: UUID = UUID("00000000-0000-0000-0000-000000000003")

    BASE_DIR: Path = Path("/") / "tmp" / "test-dir"
    ORIGINAL_FILES_DIR: Path = BASE_DIR / str(USER_ID) / str(SESSION_ID) / "original"
    PROCESSED_FILES_DIR: Path = BASE_DIR / str(USER_ID) / str(SESSION_ID) / "processed"


@pytest.fixture(scope="session")
def test_settings() -> SettingsForTests:
    test_settings = SettingsForTests()
    image_settings.BASE_FILES_DIR = test_settings.BASE_DIR

    return test_settings


@pytest.fixture(scope="session", autouse=True)
def configure_celery() -> None:
    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )


@pytest.fixture(scope="class")
def original_files_dir(test_settings: SettingsForTests) -> Generator[Path, Any, None]:
    test_settings.ORIGINAL_FILES_DIR.mkdir(parents=True, exist_ok=True)

    yield test_settings.ORIGINAL_FILES_DIR

    rmtree(test_settings.BASE_DIR, ignore_errors=True)


@pytest.fixture(scope="class")
def processed_files_dir(test_settings: SettingsForTests) -> Generator[Path, Any, None]:
    test_settings.PROCESSED_FILES_DIR.mkdir(parents=True, exist_ok=True)

    yield test_settings.PROCESSED_FILES_DIR

    rmtree(test_settings.BASE_DIR, ignore_errors=True)


@pytest.fixture(scope="function")
def original_file(original_files_dir: Path) -> Generator[File, Any, None]:
    file_hash, file_type, mime_type = "0000000000000000", "jpg", "image/jpeg"
    _file_ = File(path=original_files_dir / f"0_{file_hash}.{file_type}", type=mime_type)

    _file_.path.touch(exist_ok=True)

    yield _file_

    for file_path in original_files_dir.iterdir() if original_files_dir.exists() else []:
        file_path.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def processed_files(processed_files_dir: Path) -> Generator[ProcessedFileBound, Any, None]:
    dimensions = ("original", "150x200", "450x600", "675x900")
    file_types = ("jpg", "webp", "webp", "webp")
    mime_types = ("image/jpeg", "image/webp", "image/webp", "image/webp")
    file_hash = "0000000000000000"

    files = tuple(
        File(path=processed_files_dir / f"{size}_0_{file_hash}.{file_type}", type=mime_type)
        for size, file_type, mime_type in zip(dimensions, file_types, mime_types)
    )

    processed_files_dir.mkdir(parents=True, exist_ok=True)

    for _file_ in files:
        _file_.path.touch(exist_ok=True)

    yield ProcessedFileBound(*files)

    for file_path in processed_files_dir.iterdir() if processed_files_dir.exists() else []:
        file_path.unlink(missing_ok=True)


@pytest.fixture(scope="class")
def image_optimize_processor(test_settings: SettingsForTests) -> ImageOptimizeProcessor:
    return ImageOptimizeProcessor(
        user_id=test_settings.USER_ID,
        session_id=test_settings.SESSION_ID,
        product_id=test_settings.PRODUCT_ID,
    )

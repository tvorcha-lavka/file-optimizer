from pathlib import Path

from pydantic.v1 import BaseSettings


class ImageFileSettings(BaseSettings):
    WEBP_QUALITY: int = 90
    JPEG_QUALITY: int = 80

    ORIGINAL_FILE_FORMAT: str = "JPEG"
    PROCESSED_FILE_FORMAT: str = "WEBP"

    BASE_FILES_DIR: Path = Path("/") / "mnt" / "efs" / "images"

    QUALITY_MAP: dict[str, int] = {"JPEG": JPEG_QUALITY, "WEBP": WEBP_QUALITY}
    SUFFIX_MAP: dict[str, str] = {"JPEG": "jpg", "WEBP": "webp"}


image_settings = ImageFileSettings()

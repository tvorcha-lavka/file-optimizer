from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class ImageFileSettings(BaseSettings):
    WEBP_QUALITY: int = 90
    JPEG_QUALITY: int = 80

    ORIGINAL_FILE_FORMAT: str = "JPEG"
    PROCESSED_FILE_FORMAT: str = "WEBP"

    BASE_FILES_DIR: Path = Path("/") / "mnt" / "efs" / "images"

    QUALITY_MAP: dict[str, int] = {"JPEG": JPEG_QUALITY, "WEBP": WEBP_QUALITY}
    SUFFIX_MAP: dict[str, str] = {"JPEG": "jpg", "WEBP": "webp"}

    model_config = SettingsConfigDict(
        env_prefix="IMAGE_",
        case_sensitive=True,
    )


image_settings = ImageFileSettings()

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class ImageFileSettings(BaseSettings):
    BASE_FILES_DIR: Path = Path("/") / "mnt" / "efs" / "images"

    model_config = SettingsConfigDict(
        env_prefix="IMAGE_",
        case_sensitive=True,
    )


image_settings = ImageFileSettings()

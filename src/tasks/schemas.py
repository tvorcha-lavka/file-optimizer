from pathlib import Path, PurePosixPath
from uuid import UUID

from pydantic import BaseModel


class ImageConfig(BaseModel):
    format: str  # noqa: VNE003
    height: int
    width: int
    quality: int
    template: str = ""


class PresetType(BaseModel):
    original: ImageConfig
    processed: list[ImageConfig]


class ImagePreset(BaseModel):
    aws_s3_folder: PurePosixPath
    type: PresetType  # noqa: VNE003


class OptimizeProductImages(BaseModel):
    """
    Data Transfer Object
    for optimizing product images task.
    """

    user_id: UUID
    session_id: UUID
    product_id: UUID
    preset: ImagePreset


class UploadProductImageData(BaseModel):
    """
    Data Transfer Object
    for uploading files to S3 task.
    """

    aws_s3_folder: PurePosixPath
    processed_files_dir: Path
    product_id: UUID

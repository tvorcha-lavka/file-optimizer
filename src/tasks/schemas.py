from pathlib import Path
from uuid import UUID

from pydantic import BaseModel


class OptimizeProductImages(BaseModel):
    """
    Data Transfer Object
    for optimizing product images task.
    """

    user_id: UUID
    session_id: UUID
    product_id: UUID


class UploadProductImageData(BaseModel):
    """
    Data Transfer Object
    for uploading files to S3 task.
    """

    processed_files_dir: Path
    product_id: UUID

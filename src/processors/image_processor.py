from enum import Enum
from logging import getLogger
from pathlib import Path
from uuid import UUID

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener  # type: ignore

from core.config.file import image_settings as settings
from core.exceptions import ImageProcessingError, NoAnyImageFiles, NoOriginalImageFiles
from core.utils import log_param

logger = getLogger("celery.optimize")
register_heif_opener()


class ProductImageDimensions(Enum):
    """Enumeration for different product image dimensions."""

    SMALL = (150, 200)
    MEDIUM = (450, 600)
    LARGE = (675, 900)


class ImageOptimizeProcessor:
    """Handles image processing, including resizing and optimization."""

    __slots__ = (
        "_file_path",
        "_product_id",
        "_user_id",
        "_session_id",
        "_user_dir",
        "_session_dir",
        "original_files_dir",
        "processed_files_dir",
    )

    def __init__(self, user_id: UUID, session_id: UUID, product_id: UUID) -> None:
        self._file_path = Path()

        self._product_id = product_id
        self._user_id = user_id
        self._session_id = session_id

        self._user_dir = settings.BASE_FILES_DIR / str(self._user_id)
        self._session_dir = self._user_dir / str(self._session_id)

        self.original_files_dir = self._session_dir / "original"
        self.processed_files_dir = self._session_dir / "processed"

    def has_any_original_files(self) -> bool:
        """Checks if there are original images available in the directory."""
        return self.original_files_dir.exists() and any(self.original_files_dir.iterdir())

    def has_any_processed_files(self) -> bool:
        """Checks if there are processed images available in the directory."""
        return self.processed_files_dir.exists() and any(self.processed_files_dir.iterdir())

    def process(self) -> None:
        """Processes images, ensuring they are optimized and resized."""
        if not self.has_any_original_files() and not self.has_any_processed_files():
            logger.debug("No any processed or original images. %s", log_param("Product ID", self._product_id))
            raise NoAnyImageFiles()

        if not self.has_any_original_files():
            logger.debug("No any original images.   %s", log_param("Product ID", self._product_id))
            raise NoOriginalImageFiles()

        logger.debug("Processing images...  %s", log_param("Product ID", self._product_id))

        try:
            # Create the processed files directory
            self.processed_files_dir.mkdir(parents=True, exist_ok=True)

            # Process the original files
            for file_path in self.original_files_dir.iterdir():
                self._process(file_path)

            # Delete the original files directory
            self.original_files_dir.rmdir()

        except (UnidentifiedImageError, ValueError, TypeError, OSError) as e:
            message = "Image optimization failed. user_id=%s, session_id=%s, error=%s"
            logger.warning(message, self._user_id, self._session_id, e)

            raise ImageProcessingError(e)

        logger.debug("Images are processed! %s", log_param("Product ID", self._product_id))

    def _process(self, file_path: Path) -> None:
        """Processes a single image, applying transformations and optimizations."""
        self._file_path = file_path

        with Image.open(self._file_path) as img_file:
            logger.debug("Optimizing original image %s", self._file_path.name)
            img_file = self._process_original(img_file, settings.ORIGINAL_FILE_FORMAT)

            logger.debug("Optimizing original image %s with scaling.", self._file_path.name)
            self._process_original_with_scaling(img_file, settings.PROCESSED_FILE_FORMAT)

        # Delete the original file
        self._file_path.unlink(missing_ok=True)

    def _process_original(self, img_file: Image.Image, file_format: str) -> Image.Image:
        """Processes and saves the original image with optimizations."""
        suffix = settings.SUFFIX_MAP[settings.ORIGINAL_FILE_FORMAT]
        quality = settings.QUALITY_MAP[settings.ORIGINAL_FILE_FORMAT]

        # Apply EXIF orientation
        img = ImageOps.exif_transpose(img_file)

        # Remove transparency
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Create a new file name
        file_name = f"original_{self._file_path.stem}.{suffix}"
        new_file_path = self.processed_files_dir / file_name

        # Save the image to a new file
        logger.debug("Saving optimized original image %s", file_name)
        img.save(fp=new_file_path, format=file_format, quality=quality, optimize=True, exif=b"")

        return img

    def _process_original_with_scaling(self, img_file: Image.Image, file_format: str) -> None:
        """Processes and saves the processed image in different sizes."""
        suffix = settings.SUFFIX_MAP[file_format]
        quality = settings.QUALITY_MAP[file_format]

        for size in ProductImageDimensions:
            img = img_file.copy()
            width, height = size.value

            # Resize the image while preserving the proportions
            img.thumbnail((width, height), Image.Resampling.LANCZOS)

            # Create a new file name
            file_name = f"{width}x{height}_{self._file_path.stem}.{suffix}"
            new_file_path = self.processed_files_dir / file_name

            # Save the image to a new file
            logger.debug("Saving processed image %s", file_name)
            img.save(fp=new_file_path, format=file_format, quality=quality, optimize=True, exif=b"")

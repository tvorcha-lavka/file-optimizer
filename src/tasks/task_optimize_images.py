from logging import getLogger

from celery import Task  # type: ignore

from core.exceptions import ImageProcessingError, NoAnyImageFiles, NoOriginalImageFiles
from main import app
from processors import ImageOptimizeProcessor

from .schemas import OptimizeProductImages, UploadProductImageData

logger = getLogger("celery.optimize")


@app.task(name="optimize.product.images", queue="file-optimizer.queue", bind=True)
def optimize_product_images_task(self: Task, json_str: str) -> str | None:
    """Optimizes images and sends them to upload process."""
    # Validate the data
    data = OptimizeProductImages.model_validate_json(json_str)

    # Initialize the processor
    processor = ImageOptimizeProcessor(data.user_id, data.session_id, data.product_id)

    try:
        # Execute process
        processor.process()
    except ImageProcessingError as e:
        raise self.retry(exc=e)

    except NoAnyImageFiles:
        logger.info("No data to process. Product ID: %s", data.product_id)
        return None

    except NoOriginalImageFiles:
        pass

    # Preparing data to transfer to the next task
    next_task_data = UploadProductImageData(
        processed_files_dir=processor.processed_files_dir,
        product_id=data.product_id,
    )

    return next_task_data.model_dump_json()

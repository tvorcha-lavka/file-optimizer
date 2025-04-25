from logging import getLogger

from celery import Task  # type: ignore

from core.exceptions import ImageProcessingError, NoAnyImageFiles, NoOriginalImageFiles
from main import app
from processors import ImageOptimizeProcessor

from .schemas import OptimizeProductImages, UploadFilesToS3

logger = getLogger("celery.optimize")


@app.task(name="optimize.product.images", queue="optimize.queue", bind=True, max_retries=3)
def optimize_product_images_task(self: Task, json_str: str) -> None:
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
        return

    except NoOriginalImageFiles:
        pass

    # Preparing data to transfer to the next task
    upload_data = UploadFilesToS3(
        processed_files_dir=processor.processed_files_dir,
        product_id=data.product_id,
    )

    # Send task to upload files
    logger.debug("Sending task to upload files...")

    # Call the next task
    app.send_task(
        name="upload.s3.product.images",
        queue="upload.queue",
        kwargs={"json_str": upload_data.model_dump_json()},
    )

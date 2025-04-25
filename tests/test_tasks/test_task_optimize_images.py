from contextlib import nullcontext

import pytest
from celery import states  # type: ignore
from celery.exceptions import Retry  # type: ignore
from pytest_mock import MockerFixture

from core.exceptions import ImageProcessingError, NoAnyImageFiles, NoOriginalImageFiles
from main import app
from processors import ImageOptimizeProcessor
from tasks import optimize_product_images_task
from tasks.schemas import OptimizeProductImages, UploadFilesToS3


class TestOptimizeImagesTask:
    @pytest.fixture(autouse=True)
    def setup(self, image_optimize_processor: ImageOptimizeProcessor) -> None:
        self.processor = image_optimize_processor

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "exception, expected_exception, should_call_next_task",
        [
            (None, None, True),
            (NoAnyImageFiles, None, False),
            (NoOriginalImageFiles, None, True),
            (ImageProcessingError, Retry, False),
        ],
    )
    def test_optimize_product_images_task(
        self,
        mocker: MockerFixture,
        exception: type[Exception] | None,
        expected_exception: type[Exception] | None,
        should_call_next_task: bool,
    ) -> None:
        """Success case of process files task."""
        # Patch `process` method to not call the real logic
        process_mock = mocker.patch.object(ImageOptimizeProcessor, "process", side_effect=exception)
        next_task_call = mocker.patch.object(app, "send_task")

        # Preparing data to transfer to the task
        optimize_dto = OptimizeProductImages(
            user_id=self.processor._user_id,
            session_id=self.processor._session_id,
            product_id=self.processor._product_id,
        )

        with pytest.raises(expected_exception) if expected_exception else nullcontext():
            # Call the task
            result = optimize_product_images_task.apply_async(
                queue="optimize.queue",
                kwargs={"json_str": optimize_dto.model_dump_json()},
            )

        if not expected_exception:
            # Check that the `upload` method has been called
            process_mock.assert_called_once_with()

            # Check that the task completed successfully
            assert result.status == states.SUCCESS

            if should_call_next_task:
                # Preparing data to transfer to the next task
                upload_data = UploadFilesToS3(
                    processed_files_dir=self.processor.processed_files_dir,  # noqa
                    product_id=self.processor._product_id,
                )
                # Check that the next task has been called with the correct arguments
                next_task_call.assert_called_once_with(
                    name="upload.s3.product.images",
                    queue="upload.queue",
                    kwargs={"json_str": upload_data.model_dump_json()},
                )
            else:
                next_task_call.assert_not_called()
        else:
            next_task_call.assert_not_called()

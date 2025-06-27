from contextlib import nullcontext

import pytest
from celery import states  # type: ignore
from celery.exceptions import Retry  # type: ignore
from pytest_mock import MockerFixture

from core.exceptions import ImageProcessingError, NoAnyImageFiles, NoOriginalImageFiles
from processors import ImageOptimizeProcessor
from tasks import optimize_product_images_task
from tasks.schemas import OptimizeProductImages, UploadProductImageData


class TestOptimizeImagesTask:
    @pytest.fixture(autouse=True)
    def setup(self, image_optimize_processor: ImageOptimizeProcessor) -> None:
        self.processor = image_optimize_processor

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "exception, expected_exception",
        [
            (None, None),
            (NoAnyImageFiles, None),
            (NoOriginalImageFiles, None),
            (ImageProcessingError, Retry),
        ],
    )
    def test_optimize_product_images_task(
        self,
        mocker: MockerFixture,
        exception: type[Exception] | None,
        expected_exception: type[Exception] | None,
    ) -> None:
        """Success case of process files task."""
        # Patch `process` method to not call the real logic
        process_mock = mocker.patch.object(ImageOptimizeProcessor, "process", side_effect=exception)

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

        if expected_exception:
            return

        # Check that the `upload` method has been called
        process_mock.assert_called_once_with()

        # Check that the task completed successfully
        assert result.status == states.SUCCESS

        if isinstance(result.result, str):
            # Preparing data to transfer to the next task
            next_task_data = UploadProductImageData(
                processed_files_dir=self.processor.processed_files_dir,  # noqa
                product_id=self.processor._product_id,
            )
            assert result.result == next_task_data.model_dump_json()
        else:
            assert result.result is None

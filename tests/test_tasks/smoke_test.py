from pathlib import Path
from shutil import copytree
from typing import Any

import pytest
from pytest_mock import MockerFixture

from main import app
from processors import ImageOptimizeProcessor
from tasks.schemas import OptimizeProductImages
from tests.conftest import SettingsForTests


class TestOptimizeFlow:

    @pytest.fixture(autouse=True)
    def setup(self, original_files_dir: Path, test_settings: SettingsForTests) -> None:
        copytree(Path("/tests/test_data"), original_files_dir, dirs_exist_ok=True)
        self.files_count = len(list(original_files_dir.iterdir()))

        self.task_dto = OptimizeProductImages(
            user_id=test_settings.USER_ID,
            session_id=test_settings.SESSION_ID,
            product_id=test_settings.PRODUCT_ID,
        )

    @pytest.mark.smoke
    def test_optimize_flow(self, mocker: MockerFixture) -> None:
        """Smoke test for optimize flow."""

        def apply_async(*args: Any, **kwargs: Any) -> None:
            """Patches `send_task` method as `apply_async`."""
            if task := app.tasks.get(kwargs.pop("name", None)):
                task.apply_async(*args, **kwargs)

        # Patch task calls method `send_task` as `apply_async`
        mocker.patch.object(app, "send_task", side_effect=apply_async)

        # Create SPYs to verify that the flow methods are being called as expected
        _process_spy = mocker.spy(ImageOptimizeProcessor, "_process")
        _process_original_spy = mocker.spy(ImageOptimizeProcessor, "_process_original")
        _process_original_with_scaling_spy = mocker.spy(ImageOptimizeProcessor, "_process_original_with_scaling")

        # Execute upload flow through the first task
        app.send_task(
            name="optimize.product.images",
            queue="optimize.queue",
            kwargs={"json_str": self.task_dto.model_dump_json()},
        )

        # Verify that the flow methods are being called as expected
        assert _process_spy.call_count == self.files_count
        assert _process_original_spy.call_count == self.files_count
        assert _process_original_with_scaling_spy.call_count == self.files_count

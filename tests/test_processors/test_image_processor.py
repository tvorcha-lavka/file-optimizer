from contextlib import nullcontext
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest
from PIL import Image, ImageOps, UnidentifiedImageError
from pytest_mock import MockerFixture

from core.exceptions import ImageProcessingError, NoAnyImageFiles, NoOriginalImageFiles
from processors import ImageOptimizeProcessor
from tests.conftest import File


class TestImageOptimizeProcessor:
    @pytest.fixture(autouse=True)
    def setup(self, image_optimize_processor: ImageOptimizeProcessor) -> None:
        self.processor = image_optimize_processor

    @pytest.mark.unit
    @pytest.mark.parametrize("has_originals", (True, False))
    def test_has_any_original_files(self, request: FixtureRequest, has_originals: bool) -> None:
        """Test has_any_original_files method."""
        if has_originals:  # dynamically fixture
            request.getfixturevalue("original_file")

        # Call `has_any_original_files` method
        result = self.processor.has_any_original_files()

        # Check result
        assert result == has_originals

    @pytest.mark.unit
    @pytest.mark.parametrize("has_processed", (True, False))
    def test_has_any_processed_files(self, request: FixtureRequest, has_processed: bool) -> None:
        """Test has_any_processed_files method."""
        if has_processed:  # dynamically fixture
            request.getfixturevalue("processed_files")

        # Call `has_any_processed_files` method
        result = self.processor.has_any_processed_files()

        # Check result
        assert result == has_processed

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "has_any_original_files, has_any_processed_files, exception, expected_exception",
        [
            (True, False, None, None),  # Success, no exceptions
            (False, False, NoAnyImageFiles, NoAnyImageFiles),
            (False, True, NoOriginalImageFiles, NoOriginalImageFiles),
            (True, False, UnidentifiedImageError, ImageProcessingError),
            (True, False, ValueError, ImageProcessingError),
            (True, False, TypeError, ImageProcessingError),
            (True, False, OSError, ImageProcessingError),
        ],
    )
    def test_process(
        self,
        mocker: MockerFixture,
        has_any_original_files: bool,
        has_any_processed_files: bool,
        exception: type[Exception] | None,
        expected_exception: type[Exception] | None,
    ) -> None:
        """Test process method."""
        # Patch dependencies
        mocker.patch.object(ImageOptimizeProcessor, "has_any_original_files", return_value=has_any_original_files)
        mocker.patch.object(ImageOptimizeProcessor, "has_any_processed_files", return_value=has_any_processed_files)

        mocker.patch(f"{ImageOptimizeProcessor.__module__}.logger.warning")
        mocker.patch.object(Path, "iterdir", return_value=[mocker.MagicMock()])

        mkdir_mock = mocker.patch.object(Path, "mkdir")
        rmdir_mock = mocker.patch.object(Path, "rmdir")

        # Patch `_process` method to rise exceptions
        mock_process = mocker.patch.object(ImageOptimizeProcessor, "_process", side_effect=exception)

        # Call `process` method and assert results
        with pytest.raises(expected_exception) if expected_exception else nullcontext():
            self.processor.process()

        if not expected_exception:
            mkdir_mock.assert_called_once()
            mock_process.assert_called_once()
            rmdir_mock.assert_called_once()
        else:
            if expected_exception in (NoOriginalImageFiles, NoAnyImageFiles):
                mkdir_mock.assert_not_called()
                mock_process.assert_not_called()
                rmdir_mock.assert_not_called()
            else:
                mkdir_mock.assert_called_once()
                mock_process.assert_called_once()
                rmdir_mock.assert_not_called()

    @pytest.mark.unit
    def test__process(self, mocker: MockerFixture, original_file: File) -> None:
        """Test _process method."""
        # Patch dependencies
        mocked_image = mocker.MagicMock()
        mocked_image.__enter__.return_value = mocked_image
        mocked_image.__exit__.return_value = None

        mocker.patch.object(Image, "open", return_value=mocked_image)
        mock_process = mocker.patch.object(ImageOptimizeProcessor, "_process_original", return_value=mocked_image)
        mock_process_with_scaling = mocker.patch.object(ImageOptimizeProcessor, "_process_original_with_scaling")
        unlink_mock = mocker.spy(Path, "unlink")

        # Call `_process` method
        self.processor._process(original_file.path)

        # Check results
        mock_process.assert_called_once_with(mocked_image)
        mock_process_with_scaling.assert_called_once_with(mocked_image)
        unlink_mock.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.parametrize("image_mode", ("RGB", "RGBA", "P"))
    def test__process_original(self, mocker: MockerFixture, original_file: File, image_mode: str) -> None:
        """Test _process_original method."""
        # Create a mock image
        mocked_image = mocker.MagicMock(spec=Image.Image)
        mocked_transposed = mocker.MagicMock(spec=Image.Image)

        mocked_transposed.mode = image_mode
        mocked_transposed.convert.return_value = mocked_transposed

        mocker.patch.object(ImageOps, "exif_transpose", return_value=mocked_transposed)
        save_mock = mocked_transposed.save = mocker.MagicMock()

        i = self.processor._preset.type.original

        # Patch processor internals
        self.processor._file_path = original_file.path
        file_name = i.template.format(hash=self.processor._file_path.stem)
        new_file_path = self.processor.processed_files_dir / file_name  # noqa

        # Call `_process_original` method
        result = self.processor._process_original(mocked_image)

        # Assert results
        assert result == mocked_transposed
        save_mock.assert_called_once_with(
            fp=new_file_path,
            format=i.format,
            quality=i.quality,
            optimize=True,
            exif=b"",
        )

    @pytest.mark.unit
    def test__process_original_with_scaling(self, mocker: MockerFixture, original_file: File) -> None:
        """Test _process_original_with_scaling method."""
        # Mock image
        mocked_image = mocker.MagicMock(spec=Image.Image)
        copied_image = mocker.MagicMock(spec=Image.Image)
        mocked_image.copy.return_value = copied_image

        copied_image.thumbnail = mocker.MagicMock()
        save_mock = copied_image.save = mocker.MagicMock()

        # Patch processor internals
        self.processor._file_path = original_file.path

        # Call `_process_original_with_scaling` method
        self.processor._process_original_with_scaling(mocked_image)

        # Assert thumbnail + save called per dimension
        assert mocked_image.copy.call_count == len(self.processor._preset.type.processed)
        assert copied_image.thumbnail.call_count == len(self.processor._preset.type.processed)
        assert save_mock.call_count == len(self.processor._preset.type.processed)

        for i in self.processor._preset.type.processed:

            copied_image.thumbnail.assert_any_call((i.width, i.height), Image.Resampling.LANCZOS)

            expected_filename = i.template.format(hash=self.processor._file_path.stem)
            expected_path = self.processor.processed_files_dir / expected_filename  # noqa

            save_mock.assert_any_call(
                fp=expected_path,
                format=i.format,
                quality=i.quality,
                optimize=True,
                exif=b"",
            )

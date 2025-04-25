class ImageProcessingError(Exception):
    """Base class for image processing errors."""

    pass


class NoAnyImageFiles(Exception):
    """Raised when there are no any image files in the directory."""

    pass


class NoOriginalImageFiles(Exception):
    """Raised when there are no original image files in the directory."""

    pass

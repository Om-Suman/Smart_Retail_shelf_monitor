class SmartShelfException(Exception):
    """Base application exception."""


class ModelLoadError(SmartShelfException):
    """Raised when the YOLO model cannot be loaded."""


class InvalidImageError(SmartShelfException):
    """Raised when an uploaded image is invalid."""


class InferenceError(SmartShelfException):
    """Raised when inference fails."""
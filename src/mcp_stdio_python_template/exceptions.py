class SkippedOperationError(Exception):
    """Raised when an operation should be skipped gracefully (exit code 0)."""

    pass


class AbortOperationError(Exception):
    """Raised when an operation should be aborted (exit code 1)."""

    pass


class ConfigError(AbortOperationError, ValueError):
    """Raised when a variable is invalid or missing."""

    pass

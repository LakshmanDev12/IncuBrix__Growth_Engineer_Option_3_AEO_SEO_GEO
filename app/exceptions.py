"""Domain-specific application exceptions."""

from typing import Any, Optional


class AppException(Exception):
    """Base domain exception with message and optional details."""

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, entity_name: str, identifier: Any) -> None:
        super().__init__(
            f"{entity_name} with identifier '{identifier}' was not found.",
            {"entity": entity_name, "identifier": str(identifier)},
        )


class DuplicateEntityError(AppException):
    """Raised when an attempt is made to insert a duplicate record."""

    def __init__(self, entity_name: str, field: str, value: Any) -> None:
        super().__init__(
            f"{entity_name} already exists with {field}='{value}'.",
            {"entity": entity_name, "field": field, "value": str(value)},
        )


class EvidenceStorageError(AppException):
    """Raised when reading or writing evidence artifacts fails."""
    pass


class PipelineExecutionError(AppException):
    """Raised when an execution pipeline stage encounters an unrecoverable failure."""
    pass


class ProviderError(AppException):
    """Base exception for external search and AI provider failures."""
    pass


class ProviderConfigurationError(ProviderError):
    """Raised when a requested external provider is missing required credentials or setup."""
    pass


class ProviderRateLimitError(ProviderError):
    """Raised when an external provider returns an HTTP 429 rate limit."""
    pass


class ProviderTimeoutError(ProviderError):
    """Raised when an external provider request times out."""
    pass

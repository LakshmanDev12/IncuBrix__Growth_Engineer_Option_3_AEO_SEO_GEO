"""Bounded Retry Utility with Exponential Backoff and Error Discrimination.

Provides bounded retries for transient network, timeout, and provider rate-limit
errors while failing fast on permanent client and authentication errors.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Optional, Set, Tuple, Type

import httpx

from app.logging_config import get_logger

logger = get_logger("incubrix.retry")

DEFAULT_TRANSIENT_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    ConnectionError,
    TimeoutError,
)

RETRYABLE_STATUS_CODES: Set[int] = {429, 500, 502, 503, 504}


def is_transient_error(exc: Exception) -> bool:
    """Determine whether an exception represents a recoverable, transient condition."""
    if isinstance(exc, DEFAULT_TRANSIENT_EXCEPTIONS):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS_CODES
    return False


def execute_with_retry(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 2,
    base_delay: float = 0.05,
    backoff_factor: float = 2.0,
    operation_name: str = "operation",
    **kwargs: Any,
) -> Tuple[Any, int, Optional[Exception]]:
    """Execute a callable with bounded retries on transient errors.

    Returns:
        Tuple of (result, total_attempts_made, last_exception_if_any)
    """
    attempt = 0
    last_error: Optional[Exception] = None

    while attempt <= max_retries:
        attempt += 1
        try:
            result = func(*args, **kwargs)
            if attempt > 1:
                logger.info(
                    "Operation '%s' succeeded on attempt %d/%d after transient recovery.",
                    operation_name,
                    attempt,
                    max_retries + 1,
                )
            return result, attempt, None
        except Exception as exc:
            last_error = exc
            if not is_transient_error(exc) or attempt > max_retries:
                if attempt > 1:
                    logger.warning(
                        "Operation '%s' exhausted %d retries. Final error: %s",
                        operation_name,
                        max_retries,
                        exc,
                    )
                raise exc

            delay = base_delay * (backoff_factor ** (attempt - 1))
            logger.warning(
                "Transient error in '%s' on attempt %d/%d: %s. Retrying in %.3fs...",
                operation_name,
                attempt,
                max_retries + 1,
                exc,
                delay,
            )
            time.sleep(delay)

    return None, attempt, last_error

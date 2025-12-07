# dust_client/exceptions.py

from __future__ import annotations

from typing import Any, Dict, Optional, Type


# ---------------------------------------------------------------------------
# Base SDK exceptions
# ---------------------------------------------------------------------------


class DustError(Exception):
    """Base exception for all Dust SDK errors."""


class DustAPIError(DustError):
    """
    Raised when the Dust HTTP API returns a non-2xx response.

    Attributes:
        status_code: HTTP status code returned by the server.
        code: Optional Dust-specific error code (string).
        message: Human-readable error message.
        details: Raw error details payload.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.__str__())

    def __str__(self) -> str:
        base = f"Dust API error {self.status_code}"
        if self.code:
            base += f" [{self.code}]"
        if self.message:
            base += f": {self.message}"
        return base


# ---------------------------------------------------------------------------
# HTTP status–based subclasses
# ---------------------------------------------------------------------------


class DustBadRequestError(DustAPIError):
    """400 Bad Request"""


class DustUnauthorizedError(DustAPIError):
    """401 Unauthorized"""


class DustForbiddenError(DustAPIError):
    """403 Forbidden"""


class DustNotFoundError(DustAPIError):
    """404 Not Found"""


class DustConflictError(DustAPIError):
    """409 Conflict"""


class DustRateLimitError(DustAPIError):
    """429 Too Many Requests"""


class DustServerError(DustAPIError):
    """5xx Server Error"""


# ---------------------------------------------------------------------------
# Mapping helper used by DustClient
# ---------------------------------------------------------------------------

_STATUS_MAP: Dict[int, Type[DustAPIError]] = {
    400: DustBadRequestError,
    401: DustUnauthorizedError,
    403: DustForbiddenError,
    404: DustNotFoundError,
    409: DustConflictError,
    429: DustRateLimitError,
}


def map_status_to_error(status_code: int) -> Type[DustAPIError]:
    """
    Return the appropriate DustAPIError subclass for the given HTTP status code.

    Falls back to DustServerError for 5xx, or DustAPIError for other cases.
    """
    if status_code in _STATUS_MAP:
        return _STATUS_MAP[status_code]

    if 500 <= status_code <= 599:
        return DustServerError

    return DustAPIError

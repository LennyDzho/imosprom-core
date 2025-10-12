import logging
from fastapi import Request, status, Response

from src.core.infra import ErrorJsonResponse, ErrorStatus

logger = logging.getLogger(__name__)


async def not_api_key_exception_handler(_request: Request, _exc: Exception) -> Response:

    return ErrorJsonResponse(
        code=status.HTTP_401_UNAUTHORIZED,
        message="Not Authenticated",
        status=ErrorStatus.UNAUTHENTICATED,
    )


async def invalid_api_key_exception_handler(
    _request: Request, _exc: Exception
) -> Response:
    return ErrorJsonResponse(
        code=status.HTTP_403_FORBIDDEN,
        message="Invalid authenticated credentials",
        status=ErrorStatus.PERMISSION_DENIED,
    )

async def forbidden_exception_handler(_request: Request, _exc: Exception) -> Response:
    return ErrorJsonResponse(
        code=status.HTTP_403_FORBIDDEN,
        message="Forbidden",
        status=ErrorStatus.PERMISSION_DENIED,
    )

async def inactive_user_exception_handler(_request: Request, _exc: Exception) -> Response:
    return ErrorJsonResponse(
        code=status.HTTP_403_FORBIDDEN,
        message="Inactive user",
        status=ErrorStatus.PERMISSION_DENIED,
    )

async def not_found_exception_handler(_request: Request, exc: Exception) -> Response:
    return ErrorJsonResponse(
        code=status.HTTP_404_NOT_FOUND,
        message=exc.detail or "Not found",
        status=ErrorStatus.NOT_FOUND,
    )

async def conflict_exception_handler(_request: Request, exc: Exception) -> Response:
    return ErrorJsonResponse(
        code=status.HTTP_409_CONFLICT,
        message=exc.detail or "Conflict",
        status=ErrorStatus.ALREADY_EXISTS,
    )

async def http_exception_handler(_request: Request, exc: Exception):

    logger.error(
        "HTTPException: %s %s",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        exc,
    )

    return ErrorJsonResponse(
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Internal server error",
        status=ErrorStatus.INTERNAL,
    )
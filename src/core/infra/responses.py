from fastapi.responses import JSONResponse

from src.core.infra.enums import ErrorStatus
from src.core.infra.schemas import ErrorResponse, ErrorData


class ErrorJsonResponse(JSONResponse):
    def __init__(
        self,
        *,
        code: int,
        message: str,
        status: ErrorStatus,
    ):
        error_data = ErrorData(code=code, message=message, status=status)
        super().__init__(
            status_code=code,
            content=ErrorResponse(error=error_data).model_dump(),
            media_type="application/json; charset=utf-8",
        )

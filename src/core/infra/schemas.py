from pydantic import BaseModel, Field

from src.core.infra.enums import ErrorStatus


class BaseApiResponse(BaseModel):
    status: str = Field(default="ok", examples=["ok", "error"])
    message: str


class ErrorData(BaseModel):
    code: int
    message: str
    status: ErrorStatus


class ErrorResponse(BaseModel):
    error: ErrorData

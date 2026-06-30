from typing import Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: DataT


class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str

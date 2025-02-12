from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")
class MultiportalResponseWrapper(BaseModel, Generic[T]):
    status: str | None = None
    responseMessage: str | None = None 
    object: T | None = None
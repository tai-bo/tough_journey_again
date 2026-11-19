from pydantic import BaseModel

from .enums import ErrorStatusStrEnum, StatusStrEnum


class Error(BaseModel):
  status: ErrorStatusStrEnum
  note: str | None = None


class Response(BaseModel):
  input_file: str
  status: StatusStrEnum
  errors: list[Error | None]

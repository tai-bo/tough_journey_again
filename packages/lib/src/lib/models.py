from pydantic import BaseModel, Field

from .settings import TAI_NAMING_PATTERN
from .types import UTCTimestampT


class CreateRecordBase(BaseModel):
  created_by: str = Field(pattern=TAI_NAMING_PATTERN)
  created_at: UTCTimestampT


class UpdateRecordBase(BaseModel):
  updated_by: str = Field(pattern=TAI_NAMING_PATTERN)
  updated_at: UTCTimestampT


class RecordBase(CreateRecordBase, UpdateRecordBase):
  pass

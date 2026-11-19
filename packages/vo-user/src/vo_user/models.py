from uuid import UUID

from lib.types import UTCTimestampT
from pydantic import BaseModel, Field, computed_field

from .types import RequestGroupT, RequestInputTypeT


class Request(BaseModel):
  group: RequestGroupT
  type: RequestInputTypeT

  @computed_field
  @property
  def vo_state_name(self) -> str:
    return f"request_{self.group}_{self.type}"


class RequestResponse(BaseModel):
  vo_state_name: str
  new_count: int


class IsolatesBase(BaseModel):
  last_updated: UTCTimestampT
  query_id: UUID


class Isolates(IsolatesBase):
  point_ids: list


class IsolatesResponse(IsolatesBase):
  point_count: int = Field(ge=0)

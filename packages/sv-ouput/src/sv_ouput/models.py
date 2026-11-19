from pydantic import BaseModel
from user.types import AuthUIDT
from vector_db.models import QueryBase


class SummariseMomentsInput(BaseModel):
  auth_uid: AuthUIDT
  query_base: QueryBase

  @property
  def idempotency_key(self) -> str:
    return f"{self.auth_uid}_{self.query_base.query_period.period_key}"

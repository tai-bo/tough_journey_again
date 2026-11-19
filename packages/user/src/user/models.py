from pydantic import BaseModel

from .types import AuthUIDT


class UserBase(BaseModel):
  auth_uid: AuthUIDT

from pydantic import BaseModel, Field

from .enums import HarmTypeStrEnum


class ModeratorAgentDeps(BaseModel):
  harm_types: str


class ModeratorAgentOutput(BaseModel):
  violation: bool = Field(description="If the content violates any harm types.")
  harm_types: list[HarmTypeStrEnum]

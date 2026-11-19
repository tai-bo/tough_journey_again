from pydantic import BaseModel, Field, field_validator

from .enums import ModelStrEnum

AGENT_TEMPERATURE_MIN = 0
AGENT_TIMEOUT_MIN = 30
AGENT_MAX_TOKENS = 10_000


class AgentConfig(BaseModel):
  model_name: ModelStrEnum
  temperature: int = Field(ge=AGENT_TEMPERATURE_MIN)
  timeout: int = Field(ge=AGENT_TIMEOUT_MIN)
  max_tokens: int = Field(le=AGENT_MAX_TOKENS)

  @field_validator("model_name", mode="before")
  @classmethod
  def parse_model_name(cls, v: str) -> ModelStrEnum:
    return ModelStrEnum[v]

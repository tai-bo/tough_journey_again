from lib.types import StrippedStrT
from pydantic import BaseModel, Field


class TitleGeneratorAgentOutput(BaseModel):
  title: StrippedStrT = Field(
    description="A concise title for the text content, up to 5 words."
  )

  primary_language: StrippedStrT = Field(
    description="Primary language used in the text content, use `UNKNOWN` if not sure. Otherwise **must** use an `IETF BCP 47` language tag value here."
  )

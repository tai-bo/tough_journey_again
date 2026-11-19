from lib.types import StrippedStrT
from pydantic import BaseModel, Field


class PDFDescriberAgentOutput(BaseModel):
  description: StrippedStrT = Field(
    description="A detailed description of the PDF, up to 250 words."
  )

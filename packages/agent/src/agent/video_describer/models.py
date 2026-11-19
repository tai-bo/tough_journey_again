from lib.types import StrippedStrT
from pydantic import BaseModel, Field
from storage.models import Location


class VideoDescriberAgentDeps(BaseModel):
  created_at_local: str
  location: Location | None = None


class VideoDescriberAgentOutput(BaseModel):
  description: StrippedStrT = Field(
    description="A detailed description of the image, up to 250 words. Treat entire description as a single paragraph. So it **must not** contain any newline or tab characters."
  )

from typing import Literal

from pydantic_ai.models.google import GoogleModel

from .image_describer.models import ImageDescriberAgentDeps, ImageDescriberAgentOutput
from .moderator.models import ModeratorAgentDeps, ModeratorAgentOutput
from .pdf_describer.models import PDFDescriberAgentOutput
from .title_generator.models import TitleGeneratorAgentOutput
from .transcriber.models import TranscriptioAgentDeps, TranscriptionAgentOutput
from .video_describer.models import VideoDescriberAgentDeps, VideoDescriberAgentOutput

AgentNameT = Literal[
  "transcriber",
  "image_describer",
  "video_describer",
  "pdf_describer",
  "title_generator",
  "moderator",
]

ModelT = GoogleModel

ModelProviderT = Literal["google"]

AgentDepsT = (
  None
  | TranscriptioAgentDeps
  | ImageDescriberAgentDeps
  | VideoDescriberAgentDeps
  | ModeratorAgentDeps
)

AgentOutputT = (
  TranscriptionAgentOutput
  | ImageDescriberAgentOutput
  | VideoDescriberAgentOutput
  | PDFDescriberAgentOutput
  | TitleGeneratorAgentOutput
  | ModeratorAgentOutput
)

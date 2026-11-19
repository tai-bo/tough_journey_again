from lib.types import StrippedStrT
from pydantic import BaseModel, Field
from storage.models import Location


class TranscriptioAgentDeps(BaseModel):
  created_at_local: str
  location: Location | None = None


class TranscriptionMetadata(BaseModel):
  speaker_primary_language: StrippedStrT = Field(
    description="Primary language spoken in the audio recording. **Must** use an `IETF BCP 47` language tag value here."
  )


class Transcription(BaseModel):
  transcription: StrippedStrT = Field(
    description="Treat entire transcription as a single paragraph. So it **must not** contain any newline or tab characters."
  )
  transcription_metadata: TranscriptionMetadata


class TranscriptionAgentOutput(Transcription):
  title: StrippedStrT = Field(
    description="A concise title for the transcription, up to 5 words."
  )

  has_human_spoken_words: bool = Field(
    description="False if the audio recording contains no human spoken words, otherwise true."
  )

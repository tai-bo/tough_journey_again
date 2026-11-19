from agent.image_describer.models import ImageDescriberAgentDeps
from agent.transcriber.models import TranscriptioAgentDeps
from agent.video_describer.models import VideoDescriberAgentDeps
from pydantic import BaseModel
from storage.types import (
  AudioContentTypeT,
  ImageContentTypeT,
  PDFContentTypeT,
  TAIBlobURI,
  TextContentTypeT,
  VideoContentTypeT,
)


class TranscriberInput(BaseModel):
  audio_uri: TAIBlobURI
  audio_media_type: AudioContentTypeT
  agent_deps: TranscriptioAgentDeps


class ImageInput(BaseModel):
  image_uri: TAIBlobURI
  image_media_type: ImageContentTypeT
  agent_deps: ImageDescriberAgentDeps


class VideoInput(BaseModel):
  video_uri: TAIBlobURI
  video_media_type: VideoContentTypeT
  agent_deps: VideoDescriberAgentDeps


class PDFInput(BaseModel):
  pdf_uri: TAIBlobURI
  pdf_media_type: PDFContentTypeT


class TextInput(BaseModel):
  text_uri: TAIBlobURI
  text_media_type: TextContentTypeT

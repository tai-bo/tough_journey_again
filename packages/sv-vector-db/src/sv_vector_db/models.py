from lib.types import StrippedStrT, UTCTimestampT
from pydantic import BaseModel
from qdrant_client import models
from storage.models import (
  AudioInputFileMetadata,
  ImageInputFileMetadata,
  Location,
  PDFInputFileMetadata,
  TextInputFileMetadata,
  VideoInputFileMetadata,
)
from storage.types import InputTypeT
from user.models import UserBase
from vector_db.models import EmbedderEmbedding, PayloadIndexSchema, PointGroup
from vector_db.types import CollectionNameT, TaskTypeT


class TextEmbedding(EmbedderEmbedding):
  task_type: TaskTypeT


class CreateCollectionInput(BaseModel):
  collection_name: CollectionNameT


class CreateCollectionResponse(BaseModel):
  exists: bool
  created: bool


class CreateCollectionPayloadIndexInput(CreateCollectionInput):
  payload_index_schema: PayloadIndexSchema


class UpsertCollectionPayloadBase(BaseModel):
  vector: models.VectorStruct
  id: models.ExtendedPointId | None = None


class TranscriptionPayload(UserBase):
  transcription: StrippedStrT
  audio_input_file_metadata: AudioInputFileMetadata


class UpsertTranscriptionInput(UpsertCollectionPayloadBase):
  transcription_payload: TranscriptionPayload


class ImagePayload(UserBase):
  image_description: StrippedStrT
  image_input_file_metadata: ImageInputFileMetadata


class VideoPayload(UserBase):
  video_description: StrippedStrT
  video_input_file_metadata: VideoInputFileMetadata


class UpsertImageInput(UpsertCollectionPayloadBase):
  image_payload: ImagePayload


class UpsertVideoInput(UpsertCollectionPayloadBase):
  video_payload: VideoPayload


class PDFPayload(UserBase):
  pdf_description: StrippedStrT
  pdf_input_file_metadata: PDFInputFileMetadata


class UpsertPDFInput(UpsertCollectionPayloadBase):
  pdf_payload: PDFPayload


class TextPayload(UserBase):
  text: StrippedStrT
  text_input_file_metadata: TextInputFileMetadata


class UpsertTextInput(UpsertCollectionPayloadBase):
  text_payload: TextPayload


class MomentPayload(UserBase):
  timestamp: UTCTimestampT
  location: Location | None = None
  description: StrippedStrT
  input_type: InputTypeT


class UpsertMomentInput(UpsertCollectionPayloadBase):
  payload: MomentPayload


class QueryGroupPointsResponse(BaseModel):
  point_groups: list[PointGroup] | None

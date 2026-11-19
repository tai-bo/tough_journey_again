from uuid import UUID

from lib.settings import TAI_NAMING_PATTERN
from lib.types import UTCTimestampT
from pydantic import BaseModel, Field
from pydantic_extra_types.coordinate import Latitude, Longitude

from .types import (
  AudioContentTypeT,
  ImageContentTypeT,
  PDFContentTypeT,
  TAIBlobURI,
  TextContentTypeT,
  VideoContentTypeT,
)


class BlobBase(BaseModel):
  bucket_name: str = Field(pattern=TAI_NAMING_PATTERN)
  blob_name: str

  @property
  def uri(self) -> TAIBlobURI:
    return f"gs://{self.bucket_name}/{self.blob_name}"


class Geo(BaseModel):
  lat: Latitude
  lon: Longitude


class Location(BaseModel):
  geo: Geo | None = None
  city: str | None
  region: str | None


class Recording(BaseModel):
  recording_start: UTCTimestampT
  recording_end: UTCTimestampT


class InputFileMetadataBase(BaseModel):
  uuid: UUID
  created_at_local: str
  location: Location | None = None


class AudioInputFileMetadata(InputFileMetadataBase, Recording):
  pass


class AudioInputFile(BlobBase):
  content_type: AudioContentTypeT
  metadata: AudioInputFileMetadata


class VideoInputFileMetadata(InputFileMetadataBase, Recording):
  pass


class VideoInputFile(BlobBase):
  content_type: VideoContentTypeT
  metadata: VideoInputFileMetadata


class ImageInputFileMetadata(InputFileMetadataBase):
  created_at: UTCTimestampT


class ImageInputFile(BlobBase):
  content_type: ImageContentTypeT
  metadata: ImageInputFileMetadata


class TextInputFileMetadata(InputFileMetadataBase):
  created_at: UTCTimestampT


class TextInputFile(BlobBase):
  content_type: TextContentTypeT
  metadata: TextInputFileMetadata


class PDFInputFileMetadata(InputFileMetadataBase):
  document_uuid: UUID
  total_page_count: int = Field(ge=1)
  page_number: int = Field(ge=1)
  created_at: UTCTimestampT


class PDFInputFile(BlobBase):
  content_type: PDFContentTypeT
  metadata: PDFInputFileMetadata

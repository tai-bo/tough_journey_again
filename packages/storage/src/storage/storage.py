from abc import ABC, abstractmethod
from pathlib import PurePath

from google.auth import default, impersonated_credentials
from google.cloud.storage import Blob, Client
from lib.settings import Settings
from pydantic import BaseModel, ConfigDict, Field
from pydantic.dataclasses import dataclass
from restate import TerminalError

from .models import (
  AudioInputFile,
  AudioInputFileMetadata,
  BlobBase,
  ImageInputFile,
  ImageInputFileMetadata,
  PDFInputFile,
  PDFInputFileMetadata,
  TextInputFile,
  TextInputFileMetadata,
  VideoInputFile,
  VideoInputFileMetadata,
)
from .types import TAIBlobURI

_SIGNED_URL_EXP_SECOND = 30


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class TAIBlob(ABC):
  client: Client
  settings: Settings
  blob: Blob = Field(init=False)

  def __post_init__(self):
    blob = self.client.bucket(self.blob_base.bucket_name).get_blob(
      self.blob_base.blob_name
    )

    if blob is None:
      raise TerminalError(
        message=f"Blob {self.blob_base.blob_name} was not found in the bucket {self.blob_base.bucket_name}.",
        status_code=404,
      )

    self.blob = blob

  @property
  @abstractmethod
  def blob_base(self) -> BlobBase: ...

  @property
  def uri(self) -> TAIBlobURI:
    return f"gs://{self.blob_base.bucket_name}/{self.blob_base.blob_name}"

  @property
  def file_path(self) -> PurePath:
    return PurePath(self.blob_base.blob_name)

  def get_signed_url(self, lifetime: int = _SIGNED_URL_EXP_SECOND) -> str:
    source_credentials, _ = default()
    target_credentials = impersonated_credentials.Credentials(
      source_credentials=source_credentials,
      target_principal=f"{self.settings.service_account}@{self.settings.project}.iam.gserviceaccount.com",
      target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
      lifetime=lifetime,
    )

    return self.blob.generate_signed_url(
      expiration=lifetime,
      version="v4",
      method="GET",
      credentials=target_credentials,
    )


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class UserBlob(TAIBlob):
  @property
  @abstractmethod
  def metadata(self) -> BaseModel: ...

  @property
  @abstractmethod
  def idempotency_key(self) -> str: ...

  @property
  def auth_uid(self) -> str:
    return self.file_path.parts[0]


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class UserInputBlob[InputFile: BaseModel](UserBlob, ABC):
  input_file: InputFile


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class AudioInputBlob(UserInputBlob[AudioInputFile]):
  input_file: AudioInputFile

  @property
  def blob_base(self) -> BlobBase:
    return BlobBase(
      bucket_name=self.input_file.bucket_name, blob_name=self.input_file.blob_name
    )

  @property
  def metadata(self) -> AudioInputFileMetadata:
    return AudioInputFileMetadata.model_validate(self.input_file.metadata)

  @property
  def idempotency_key(self) -> str:
    return str(self.metadata.uuid)


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class ImageInputBlob(UserInputBlob[ImageInputFile]):
  input_file: ImageInputFile

  @property
  def blob_base(self) -> BlobBase:
    return BlobBase(
      bucket_name=self.input_file.bucket_name, blob_name=self.input_file.blob_name
    )

  @property
  def metadata(self) -> ImageInputFileMetadata:
    return ImageInputFileMetadata.model_validate(self.input_file.metadata)

  @property
  def idempotency_key(self) -> str:
    return str(self.metadata.uuid)


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class VideoInputBlob(UserInputBlob[VideoInputFile]):
  input_file: VideoInputFile

  @property
  def blob_base(self) -> BlobBase:
    return BlobBase(
      bucket_name=self.input_file.bucket_name, blob_name=self.input_file.blob_name
    )

  @property
  def metadata(self) -> VideoInputFileMetadata:
    return VideoInputFileMetadata.model_validate(self.input_file.metadata)

  @property
  def idempotency_key(self) -> str:
    return str(self.metadata.uuid)


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class PDFInputBlob(UserInputBlob[PDFInputFile]):
  input_file: PDFInputFile

  @property
  def blob_base(self) -> BlobBase:
    return BlobBase(
      bucket_name=self.input_file.bucket_name, blob_name=self.input_file.blob_name
    )

  @property
  def metadata(self) -> PDFInputFileMetadata:
    return PDFInputFileMetadata.model_validate(self.input_file.metadata)

  @property
  def idempotency_key(self) -> str:
    return str(self.metadata.uuid)


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class TextInputBlob(UserInputBlob[TextInputFile]):
  input_file: TextInputFile

  @property
  def blob_base(self) -> BlobBase:
    return BlobBase(
      bucket_name=self.input_file.bucket_name, blob_name=self.input_file.blob_name
    )

  @property
  def metadata(self) -> TextInputFileMetadata:
    return TextInputFileMetadata.model_validate(self.input_file.metadata)

  @property
  def idempotency_key(self) -> str:
    return str(self.metadata.uuid)

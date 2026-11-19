from typing import Self

from google.genai import types
from lib.types import UTCTimestampT
from pydantic import BaseModel, Field, computed_field, field_validator, model_validator
from qdrant_client import models
from storage.models import ImageInputFile, PDFInputFile, VideoInputFile
from user.types import AuthUIDT

from .enums import VectorNameStrEnum
from .types import (
  AsymmetricTaskTypeT,
  CollectionNameT,
  EmbedActionT,
  PointGroupT,
  QueryT,
  TaskTypeT,
)

_VECTOR_SIZE_MIN = 768
_VECTOR_SIZE_MAX = 3072

_QUERY_PARAM_PAGE_SIZE_MIN = 1
_QUERY_PARAM_PAGE_SIZE_MAX = 300

_QUERY_TUNING_SCORE_THRESHOLD_DEFAULT = 0.7
_QUERY_TUNING_SCORE_THRESHOLD_MIN = 0.618
_QUERY_TUNING_PREFETCH_LIMIT_DEFAULT = 100
_QUERY_TUNING_PREFETCH_LIMIT_MIN = 30
_QUERY_TUNING_PREFETCH_LIMIT_MAX = 100
_QUERY_TUNING_QUERY_LIMIT_DEFAULT = 10
_QUERY_TUNING_QUERY_LIMIT_MIN = 10
_QUERY_TUNING_QUERY_LIMIT_MAX = 30
_QUERY_TUNING_AVG_WEIGHT_THRESHOLD_DEFAULT = 0.500


class VectorConfig(BaseModel):
  name: VectorNameStrEnum
  size: int = Field(ge=_VECTOR_SIZE_MIN, le=_VECTOR_SIZE_MAX)
  distance: models.Distance = models.Distance.COSINE

  @field_validator("name", mode="before")
  @classmethod
  def validate_name(cls, v: str) -> VectorNameStrEnum:
    try:
      return VectorNameStrEnum[v]
    except KeyError:
      return VectorNameStrEnum(v)


class PayloadIndexSchema(BaseModel):
  field_name: str
  field_schema: models.PayloadSchemaType


class FullTextIndexSchema(BaseModel):
  field_name: str


class CollectionConfig(BaseModel):
  index_auth_uid: bool
  vector_configs: list[VectorConfig]
  payload_index_schemas: list[PayloadIndexSchema]
  full_text_index_schemas: list[FullTextIndexSchema]


class EmbedderEmbedding(BaseModel):
  embedding: list[float]


class EmbedderContent(BaseModel):
  content: types.Content


class TextEmbedderInput(BaseModel):
  embed_action: EmbedActionT
  input: str
  title: str = "none"
  task_types: list[TaskTypeT] = [
    VectorNameStrEnum.SEARCH,
    VectorNameStrEnum.CLASSIFICATION,
    VectorNameStrEnum.CLUSTERING,
  ]
  get_type: AsymmetricTaskTypeT | None = None


class TextEmbedderContent(EmbedderContent):
  task_type: TaskTypeT
  embed_action: EmbedActionT

  @computed_field
  @property
  def restate_action_name(self) -> str:
    return f"embed-{self.embed_action}-{self.task_type}"


class TextEmbedding(TextEmbedderContent, EmbedderEmbedding):
  pass


class ImageEmbedderInput(BaseModel):
  image_input_file: ImageInputFile


class ImageEmbedderContent(EmbedderContent):
  @computed_field
  @property
  def task_type(self) -> TaskTypeT:
    return VectorNameStrEnum.SEARCH

  @computed_field
  @property
  def restate_action_name(self) -> str:
    return f"embed-image-{self.task_type}"


class ImageEmbedding(ImageEmbedderContent, EmbedderEmbedding):
  pass


class VideoEmbedderInput(BaseModel):
  video_input_file: VideoInputFile


class VideoEmbedderContent(EmbedderContent):
  @computed_field
  @property
  def task_type(self) -> TaskTypeT:
    return VectorNameStrEnum.SEARCH

  @computed_field
  @property
  def restate_action_name(self) -> str:
    return f"embed-video-{self.task_type}"


class VideoEmbedding(VideoEmbedderContent, EmbedderEmbedding):
  pass


class PDFEmbedderInput(BaseModel):
  pdf_input_file: PDFInputFile


class PDFEmbedderContent(EmbedderContent):
  @computed_field
  @property
  def task_type(self) -> TaskTypeT:
    return VectorNameStrEnum.SEARCH

  @computed_field
  @property
  def restate_action_name(self) -> str:
    return f"embed-pdf-{self.task_type}"


class PDFEmbedding(PDFEmbedderContent, EmbedderEmbedding):
  pass


class EmbedResponse(BaseModel):
  vector_struct: dict[str, models.Vector]


class QueryTuning(BaseModel):
  score_threshold: float = Field(
    default=_QUERY_TUNING_SCORE_THRESHOLD_DEFAULT, ge=_QUERY_TUNING_SCORE_THRESHOLD_MIN
  )
  prefetch_limit: int = Field(
    default=_QUERY_TUNING_PREFETCH_LIMIT_DEFAULT,
    ge=_QUERY_TUNING_PREFETCH_LIMIT_MIN,
    le=_QUERY_TUNING_PREFETCH_LIMIT_MAX,
  )
  query_limit: int = Field(
    default=_QUERY_TUNING_QUERY_LIMIT_DEFAULT,
    ge=_QUERY_TUNING_QUERY_LIMIT_MIN,
    le=_QUERY_TUNING_QUERY_LIMIT_MAX,
  )
  remove_isolates: bool = True
  avg_weight_threshold: float = Field(
    default=_QUERY_TUNING_AVG_WEIGHT_THRESHOLD_DEFAULT,
  )


class QueryPeriod(BaseModel):
  from_datetime: UTCTimestampT
  to_datetime: UTCTimestampT

  @property
  def period_key(self) -> str:
    return (
      f"{self.from_datetime.strftime('%Y%m%d%H%M%S')}"
      f"_"
      f"{self.to_datetime.strftime('%Y%m%d%H%M%S')}"
    )


class QueryParam(BaseModel):
  datetime_filter_field: str
  payload_sort_by: str
  page_size: int = Field(ge=_QUERY_PARAM_PAGE_SIZE_MIN, le=_QUERY_PARAM_PAGE_SIZE_MAX)
  with_payloads: list[str] = Field(min_length=1)
  with_vectors: list[VectorNameStrEnum] = Field(min_length=1)


class PointGroup(BaseModel):
  group_type: PointGroupT
  group_index: int = Field(ge=-1)
  count: int = Field(ge=0)
  avg_weight: float | None = None
  point_ids: list | None = None

  @model_validator(mode="after")
  def validate_group_index(self) -> Self:
    if self.group_type == "isolates" and self.group_index != -1:
      raise ValueError(
        f"Group index for {self.group_type} group type must be -1, but got: {self.group_index}."
      )

    return self


class QueryBase(BaseModel):
  query_period: QueryPeriod
  query_tuning: QueryTuning


class QueryInput(QueryBase):
  collection_name: CollectionNameT
  query: QueryT


class UserQueryInput(QueryInput):
  auth_uid: AuthUIDT

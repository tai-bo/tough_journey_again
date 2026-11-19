from abc import ABC, abstractmethod

import restate
from google.genai import types
from google.genai.client import AsyncClient
from google.genai.types import PartMediaResolutionLevel
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from .enums import VectorNameStrEnum
from .models import (
  EmbedResponse,
  ImageEmbedderContent,
  ImageEmbedderInput,
  ImageEmbedding,
  PDFEmbedderContent,
  PDFEmbedderInput,
  PDFEmbedding,
  TextEmbedderContent,
  TextEmbedderInput,
  TextEmbedding,
  VideoEmbedderContent,
  VideoEmbedderInput,
  VideoEmbedding,
)
from .types import (
  AsymmetricTaskTypeT,
  SymmetricTaskTypeT,
  TaskTypeT,
)

_DEFAULT_OUTPUT_DIMENSIONALITY = 768
_EMBEDDING_MODEL = "gemini-embedding-2"

EmbedderContentT = (
  TextEmbedderContent | ImageEmbedderContent | PDFEmbedderContent | VideoEmbedderContent
)

EmbedderEmbeddingT = TextEmbedding | ImageEmbedding | PDFEmbedding | VideoEmbedding


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class TAIEmbedder[
  ContentT: EmbedderContentT,
  EmbeddingT: EmbedderEmbeddingT,
](ABC):
  genai_client: AsyncClient
  ctx: restate.Context
  output_dimensionality: int = _DEFAULT_OUTPUT_DIMENSIONALITY

  @abstractmethod
  def _get_contents(self) -> list[ContentT]: ...

  @abstractmethod
  def _process_embedding(
    self, embedding: list[float], content: ContentT
  ) -> EmbeddingT: ...

  async def _embed(self, content: types.Content) -> types.EmbedContentResponse:
    return await self.genai_client.models.embed_content(
      model=_EMBEDDING_MODEL,
      contents=content,
      config=types.EmbedContentConfig(
        output_dimensionality=self.output_dimensionality, auto_truncate=True
      ),
    )

  async def _embed_contents(
    self, contents: list[ContentT]
  ) -> list[types.EmbedContentResponse]:
    futures = [
      self.ctx.run_typed(
        content.restate_action_name, self._embed, content=content.content
      )
      for content in contents
    ]
    results = await restate.gather(*futures)
    return [await result for result in results]

  async def _get_embeddings(self) -> list[EmbeddingT]:
    embeddings: list[EmbeddingT] = []
    contents = self._get_contents()
    responses = await self._embed_contents(contents)
    for content, response in zip(contents, responses):
      response_embeddings = response.embeddings
      if response_embeddings is None or response_embeddings[0].values is None:
        raise restate.TerminalError(
          message=(
            f"Missing embeddings for content:{content.model_dump_json()}, its response was: {response.model_dump_json()}."
          ),
          status_code=404,
        )

      embeddings.append(
        self._process_embedding(
          embedding=response_embeddings[0].values, content=content
        )
      )
    return embeddings

  async def get_embed_response(self) -> EmbedResponse:
    embeddings = await self._get_embeddings()
    return EmbedResponse(vector_struct={e.task_type: e.embedding for e in embeddings})


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class TextEmbedder(TAIEmbedder[TextEmbedderContent, TextEmbedding]):
  text_embedder_input: TextEmbedderInput

  @property
  def _get_type(self) -> AsymmetricTaskTypeT:
    if self.text_embedder_input.get_type is None:
      raise restate.TerminalError(
        message=(
          f"Missing a get type for embed action {self.text_embedder_input.embed_action}."
        ),
        status_code=400,
      )
    return self.text_embedder_input.get_type

  def _get_asymmetric_task_instruction(self) -> str:
    if self.text_embedder_input.embed_action == "set":
      return f"title: {self.text_embedder_input.title} | text: {self.text_embedder_input.input}"
    else:
      return f"task: {self._get_type} | query: {self.text_embedder_input.input}"

  def _get_symmetric_task_instruction(self, task_type: SymmetricTaskTypeT) -> str:
    return f"task: {task_type} | query: {self.text_embedder_input.input}"

  def _get_task_types(self) -> list[tuple[TaskTypeT, str]]:
    task_types: list[tuple[TaskTypeT, str]] = []

    if VectorNameStrEnum.SEARCH in self.text_embedder_input.task_types:
      task_types.append((
        VectorNameStrEnum.SEARCH,
        self._get_asymmetric_task_instruction(),
      ))

    if VectorNameStrEnum.CLASSIFICATION in self.text_embedder_input.task_types:
      task_types.append((
        VectorNameStrEnum.CLASSIFICATION,
        self._get_symmetric_task_instruction(VectorNameStrEnum.CLASSIFICATION),
      ))

    if VectorNameStrEnum.CLUSTERING in self.text_embedder_input.task_types:
      task_types.append((
        VectorNameStrEnum.CLUSTERING,
        self._get_symmetric_task_instruction(VectorNameStrEnum.CLUSTERING),
      ))

    return task_types

  def _get_contents(self) -> list[TextEmbedderContent]:
    return [
      TextEmbedderContent(
        content=types.Content(parts=[types.Part.from_text(text=text)]),
        task_type=task_type,
        embed_action=self.text_embedder_input.embed_action,
      )
      for task_type, text in self._get_task_types()
    ]

  def _process_embedding(
    self, embedding: list[float], content: TextEmbedderContent
  ) -> TextEmbedding:
    return TextEmbedding(
      embedding=embedding,
      task_type=content.task_type,
      content=content.content,
      embed_action=content.embed_action,
    )


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class ImageEmbedder(TAIEmbedder[ImageEmbedderContent, ImageEmbedding]):
  image_embedder_input: ImageEmbedderInput

  def _get_contents(self) -> list[ImageEmbedderContent]:
    return [
      ImageEmbedderContent(
        content=types.Content(
          parts=[
            types.Part.from_uri(
              file_uri=self.image_embedder_input.image_input_file.uri,
              mime_type=self.image_embedder_input.image_input_file.content_type,
              media_resolution=PartMediaResolutionLevel.MEDIA_RESOLUTION_HIGH,
            ),
          ]
        )
      )
    ]

  def _process_embedding(
    self, embedding: list[float], content: ImageEmbedderContent
  ) -> ImageEmbedding:
    return ImageEmbedding(embedding=embedding, content=content.content)


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class VideoEmbedder(TAIEmbedder[VideoEmbedderContent, VideoEmbedding]):
  video_embedder_input: VideoEmbedderInput

  def _get_contents(self) -> list[VideoEmbedderContent]:
    return [
      VideoEmbedderContent(
        content=types.Content(
          parts=[
            types.Part.from_uri(
              file_uri=self.video_embedder_input.video_input_file.uri,
              mime_type=self.video_embedder_input.video_input_file.content_type,
              media_resolution=PartMediaResolutionLevel.MEDIA_RESOLUTION_HIGH,
            ),
          ]
        )
      )
    ]

  def _process_embedding(
    self, embedding: list[float], content: VideoEmbedderContent
  ) -> VideoEmbedding:
    return VideoEmbedding(embedding=embedding, content=content.content)


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class PDFEmbedder(TAIEmbedder[PDFEmbedderContent, PDFEmbedding]):
  pdf_embedder_input: PDFEmbedderInput

  def _get_contents(self) -> list[PDFEmbedderContent]:
    return [
      PDFEmbedderContent(
        content=types.Content(
          parts=[
            types.Part.from_uri(
              file_uri=self.pdf_embedder_input.pdf_input_file.uri,
              mime_type=self.pdf_embedder_input.pdf_input_file.content_type,
              media_resolution=PartMediaResolutionLevel.MEDIA_RESOLUTION_HIGH,
            ),
          ]
        )
      )
    ]

  def _process_embedding(
    self, embedding: list[float], content: PDFEmbedderContent
  ) -> PDFEmbedding:
    return PDFEmbedding(embedding=embedding, content=content.content)

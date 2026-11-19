from pathlib import Path
from typing import Any

import restate
from agent.image_describer.models import ImageDescriberAgentDeps
from agent.transcriber.models import TranscriptioAgentDeps
from agent.video_describer.models import VideoDescriberAgentDeps
from lib.utils import (
  get_restate_identity_keys,
  get_restate_invocation_retry_policy,
  get_settings,
)
from storage.models import (
  AudioInputFile,
  ImageInputFile,
  TextInputFile,
  VideoInputFile,
)
from storage.storage import (
  AudioInputBlob,
  ImageInputBlob,
  TextInputBlob,
  VideoInputBlob,
)
from storage.utils import get_storage_client
from sv_agent import (
  ImageInput,
  TextInput,
  TranscriberInput,
  VideoInput,
  image_describer,
  title_generator,
  transcriber,
  video_describer,
)
from sv_vector_db import (
  ImagePayload,
  TextPayload,
  TranscriptionPayload,
  UpsertImageInput,
  UpsertTextInput,
  UpsertTranscriptionInput,
  UpsertVideoInput,
  VideoPayload,
  embed_image,
  embed_text,
  embed_video,
  query_point_groups,
  upsert_image,
  upsert_text,
  upsert_transcription,
  upsert_video,
)
from vector_db.enums import VectorNameStrEnum
from vector_db.models import (
  ImageEmbedderInput,
  QueryInput,
  TextEmbedderInput,
  VideoEmbedderInput,
)
from vo_user import Request, add_request

from .models import SummariseMomentsInput

SERVICE_NAME = Path(__file__).parent.name


settings = get_settings()
storage_client = get_storage_client()

service = restate.Service(
  SERVICE_NAME,
  invocation_retry_policy=get_restate_invocation_retry_policy(),
)


@service.handler()
async def summarise_moments(ctx: restate.Context, input: SummariseMomentsInput) -> Any:

  point_groups = await ctx.service_call(
    query_point_groups,
    arg=QueryInput(
      query_period=input.query_base.query_period,
      query_tuning=input.query_base.query_tuning,
      collection_name="moment",
      query="moment_group",
    ),
    idempotency_key=input.idempotency_key,
  )

  # Step 99: End
  # input_response.status = StatusStrEnum.INPUT_1000
  return point_groups

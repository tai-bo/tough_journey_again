from pathlib import Path

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
  MomentPayload,
  UpsertMomentInput,
  embed_image,
  embed_text,
  embed_video,
  upsert_moment,
)
from vector_db.enums import VectorNameStrEnum
from vector_db.models import (
  ImageEmbedderInput,
  TextEmbedderInput,
  VideoEmbedderInput,
)
from vo_user import Request, add_request

from .enums import ErrorStatusStrEnum, StatusStrEnum
from .models import Error, Response

SERVICE_NAME = Path(__file__).parent.name


settings = get_settings()
storage_client = get_storage_client()

service = restate.Service(
  SERVICE_NAME,
  invocation_retry_policy=get_restate_invocation_retry_policy(),
)


@service.handler()
async def audio(ctx: restate.Context, audio_input_file: AudioInputFile) -> Response:
  # Step 0: Start
  audio_blob = AudioInputBlob(
    client=storage_client,
    settings=settings,
    input_file=audio_input_file,
  )

  input_response = Response(
    input_file=audio_blob.blob_base.blob_name,
    status=StatusStrEnum.INPUT_1001,
    errors=[],
  )

  await ctx.object_call(
    add_request,
    key=audio_blob.auth_uid,
    arg=Request(group="input", type="audio"),
    idempotency_key=audio_blob.idempotency_key,
  )

  # Step 1: Transcribe
  agent_output = await ctx.service_call(
    transcriber,
    arg=TranscriberInput(
      audio_uri=audio_blob.uri,
      audio_media_type=audio_blob.blob.content_type,
      agent_deps=TranscriptioAgentDeps(
        created_at_local=audio_blob.metadata.created_at_local,
        location=audio_blob.metadata.location,
      ),
    ),
    idempotency_key=audio_blob.idempotency_key,
  )

  if not agent_output.has_human_spoken_words:
    input_response.status = StatusStrEnum.INPUT_9000
    input_response.errors.append(Error(status=ErrorStatusStrEnum.INPUT_ERROR_1000))

    return input_response

  # Step 2: Embed
  embed_response = await ctx.service_call(
    embed_text,
    arg=TextEmbedderInput(
      embed_action="set", input=agent_output.transcription, title=agent_output.title
    ),
    idempotency_key=audio_blob.idempotency_key,
  )

  # Step 3: Save Vectors
  vector_struct = embed_response.vector_struct

  await ctx.service_call(
    upsert_moment,
    arg=UpsertMomentInput(
      vector=vector_struct,
      id=audio_blob.idempotency_key,
      payload=MomentPayload(
        auth_uid=audio_blob.auth_uid,
        timestamp=audio_blob.metadata.recording_start,
        location=audio_blob.metadata.location,
        description=agent_output.transcription,
        input_type="audio",
      ),
    ),
    idempotency_key=audio_blob.idempotency_key,
  )

  # Step 99: End
  input_response.status = StatusStrEnum.INPUT_1000
  return input_response


@service.handler()
async def image(ctx: restate.Context, image_input_file: ImageInputFile) -> Response:
  # Step 0: Start
  image_blob = ImageInputBlob(
    client=storage_client,
    settings=settings,
    input_file=image_input_file,
  )

  input_response = Response(
    input_file=image_blob.blob_base.blob_name,
    status=StatusStrEnum.INPUT_1001,
    errors=[],
  )

  await ctx.object_call(
    add_request,
    key=image_blob.auth_uid,
    arg=Request(group="input", type="image"),
    idempotency_key=image_blob.idempotency_key,
  )

  # Step 1: Describe Image
  agent_output = ctx.service_call(
    image_describer,
    arg=ImageInput(
      image_uri=image_blob.uri,
      image_media_type=image_blob.blob.content_type,
      agent_deps=ImageDescriberAgentDeps(
        created_at_local=image_blob.metadata.created_at_local,
        location=image_blob.metadata.location,
      ),
    ),
    idempotency_key=image_blob.idempotency_key,
  )

  # Step 2: Embed
  image_description = (await agent_output).description

  text_embedder = ctx.service_call(
    embed_text,
    arg=TextEmbedderInput(
      embed_action="set",
      input=image_description,
      task_types=[VectorNameStrEnum.CLASSIFICATION, VectorNameStrEnum.CLUSTERING],
    ),
    idempotency_key=image_blob.idempotency_key,
  )

  image_embedder = ctx.service_call(
    embed_image,
    arg=ImageEmbedderInput(image_input_file=image_input_file),
    idempotency_key=image_blob.idempotency_key,
  )

  # Step 3: Save Vectors
  text_vector_struct = (await text_embedder).vector_struct
  image_vector_struct = (await image_embedder).vector_struct

  vector_struct = text_vector_struct | image_vector_struct

  await ctx.service_call(
    upsert_moment,
    arg=UpsertMomentInput(
      vector=vector_struct,
      id=image_blob.idempotency_key,
      payload=MomentPayload(
        auth_uid=image_blob.auth_uid,
        timestamp=image_blob.metadata.created_at,
        location=image_blob.metadata.location,
        description=image_description,
        input_type="image",
      ),
    ),
    idempotency_key=image_blob.idempotency_key,
  )

  # Step 99: End
  input_response.status = StatusStrEnum.INPUT_1000
  return input_response


@service.handler()
async def video(ctx: restate.Context, video_input_file: VideoInputFile) -> Response:
  # Step 0: Start
  video_blob = VideoInputBlob(
    client=storage_client,
    settings=settings,
    input_file=video_input_file,
  )

  input_response = Response(
    input_file=video_blob.blob_base.blob_name,
    status=StatusStrEnum.INPUT_1001,
    errors=[],
  )

  await ctx.object_call(
    add_request,
    key=video_blob.auth_uid,
    arg=Request(group="input", type="video"),
    idempotency_key=video_blob.idempotency_key,
  )

  # Step 1: Describe Video
  agent_output = ctx.service_call(
    video_describer,
    arg=VideoInput(
      video_uri=video_blob.uri,
      video_media_type=video_blob.blob.content_type,
      agent_deps=VideoDescriberAgentDeps(
        created_at_local=video_blob.metadata.created_at_local,
        location=video_blob.metadata.location,
      ),
    ),
    idempotency_key=video_blob.idempotency_key,
  )

  # Step 2: Embed
  video_description = (await agent_output).description

  text_embedder = ctx.service_call(
    embed_text,
    arg=TextEmbedderInput(
      embed_action="set",
      input=video_description,
      task_types=[VectorNameStrEnum.CLASSIFICATION, VectorNameStrEnum.CLUSTERING],
    ),
    idempotency_key=video_blob.idempotency_key,
  )

  video_embedder = ctx.service_call(
    embed_video,
    arg=VideoEmbedderInput(video_input_file=video_input_file),
    idempotency_key=video_blob.idempotency_key,
  )

  # Step 3: Save Vectors
  text_vector_struct = (await text_embedder).vector_struct
  video_vector_struct = (await video_embedder).vector_struct

  vector_struct = text_vector_struct | video_vector_struct

  await ctx.service_call(
    upsert_moment,
    arg=UpsertMomentInput(
      vector=vector_struct,
      id=video_blob.idempotency_key,
      payload=MomentPayload(
        auth_uid=video_blob.auth_uid,
        timestamp=video_blob.metadata.recording_start,
        location=video_blob.metadata.location,
        description=video_description,
        input_type="video",
      ),
    ),
    idempotency_key=video_blob.idempotency_key,
  )

  # Step 99: End
  input_response.status = StatusStrEnum.INPUT_1000
  return input_response


@service.handler()
async def text(ctx: restate.Context, text_input_file: TextInputFile) -> Response:
  # Step 0: Start
  text_blob = TextInputBlob(
    client=storage_client,
    settings=settings,
    input_file=text_input_file,
  )

  input_response = Response(
    input_file=text_blob.blob_base.blob_name,
    status=StatusStrEnum.INPUT_1001,
    errors=[],
  )

  text = text_blob.blob.download_as_text()

  await ctx.object_call(
    add_request,
    key=text_blob.auth_uid,
    arg=Request(group="input", type="text"),
    idempotency_key=text_blob.idempotency_key,
  )

  # Step 1: Generate Title
  agent_output = await ctx.service_call(
    title_generator,
    arg=TextInput(text_uri=text_blob.uri, text_media_type=text_blob.blob.content_type),
    idempotency_key=text_blob.idempotency_key,
  )

  # Step 2: Embed
  embed_response = await ctx.service_call(
    embed_text,
    arg=TextEmbedderInput(embed_action="set", input=text, title=agent_output.title),
    idempotency_key=text_blob.idempotency_key,
  )

  # Step 3: Save Vectors
  vector_struct = embed_response.vector_struct

  await ctx.service_call(
    upsert_moment,
    arg=UpsertMomentInput(
      vector=vector_struct,
      id=text_blob.idempotency_key,
      payload=MomentPayload(
        auth_uid=text_blob.auth_uid,
        timestamp=text_blob.metadata.created_at,
        location=text_blob.metadata.location,
        description=text,
        input_type="text",
      ),
    ),
    idempotency_key=text_blob.idempotency_key,
  )

  # Step 99: End
  input_response.status = StatusStrEnum.INPUT_1000
  return input_response


# @service.handler()
# async def pdf(ctx: restate.Context, pdf_input_file: PDFInputFile) -> Response:
#   try:
#     # Step 0: Start
#     pdf_blob = PDFInputBlob(
#       client=storage_client,
#       settings=settings,
#       input_file=pdf_input_file,
#     )

#     input_response = Response(
#       input_file=pdf_blob.blob_base.blob_name,
#       status=StatusStrEnum.INPUT_1001,
#       errors=[],
#     )

#     await ctx.object_call(
#       add_request,
#       key=pdf_blob.auth_uid,
#       arg=Request(group="input", type="pdf"),
#       idempotency_key=pdf_blob.idempotency_key,
#     )

#     # Step 1: Describe PDF
#     agent_output = ctx.service_call(
#       pdf_describer,
#       arg=PDFInput(pdf_uri=pdf_blob.uri),
#       idempotency_key=pdf_blob.idempotency_key,
#     )

#     # Step 2: Embed
#     pdf_description = (await agent_output).description

#     text_embedder = ctx.service_call(
#       embed_text,
#       arg=TextEmbedderInput(
#         embed_action="set",
#         input=pdf_description,
#         task_types=[VectorNameStrEnum.CLASSIFICATION, VectorNameStrEnum.CLUSTERING],
#       ),
#       idempotency_key=pdf_blob.idempotency_key,
#     )

#     pdf_embedder = ctx.service_call(
#       embed_pdf,
#       arg=PDFEmbedderInput(pdf_input_file=pdf_input_file),
#       idempotency_key=pdf_blob.idempotency_key,
#     )

#     # Step 3: Save Vectors
#     text_vector_struct = (await text_embedder).vector_struct
#     pdf_vector_struct = (await pdf_embedder).vector_struct

#     vector_struct = text_vector_struct | pdf_vector_struct

#     pdf_payload = PDFPayload(
#       auth_uid=pdf_blob.auth_uid,
#       pdf_description=pdf_description,
#       pdf_input_file_metadata=pdf_blob.metadata,
#     )

#     await ctx.service_call(
#       upsert_pdf,
#       arg=UpsertPDFInput(
#         vector=vector_struct,
#         id=pdf_blob.idempotency_key,
#         pdf_payload=pdf_payload,
#       ),
#       idempotency_key=pdf_blob.idempotency_key,
#     )

#     # Step 99: End
#     input_response.status = StatusStrEnum.INPUT_1000
#     return input_response
#   except restate.TerminalError:
#     raise


app = restate.app(
  services=[service],
  identity_keys=get_restate_identity_keys(settings),
)

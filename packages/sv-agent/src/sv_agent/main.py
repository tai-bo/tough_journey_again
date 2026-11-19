from pathlib import Path

import logfire
import restate
from agent.agent import (
  ImageDescriberAgent,
  TitleGeneratorAgent,
  TranscriptionAgent,
  VideoDescriberAgent,
)
from agent.image_describer.models import (
  ImageDescriberAgentDeps,
  ImageDescriberAgentOutput,
)
from agent.title_generator.models import TitleGeneratorAgentOutput
from agent.transcriber.models import TranscriptioAgentDeps, TranscriptionAgentOutput
from agent.video_describer.models import (
  VideoDescriberAgentDeps,
  VideoDescriberAgentOutput,
)
from lib.utils import (
  get_restate_identity_keys,
  get_restate_invocation_retry_policy,
  get_settings,
)
from pydantic_ai import AudioUrl, DocumentUrl, ImageUrl, VideoUrl
from pydantic_ai.exceptions import ContentFilterError

from .models import ImageInput, TextInput, TranscriberInput, VideoInput

SERVICE_NAME = Path(__file__).parent.name

settings = get_settings()

logfire.configure(
  service_name=SERVICE_NAME,
  token=settings.other.logfire_token.get_secret_value(),
  environment=settings.env,
  distributed_tracing=False,
  min_level=settings.log_level,
)

logfire.instrument_pydantic_ai()

service = restate.Service(
  SERVICE_NAME,
  invocation_retry_policy=get_restate_invocation_retry_policy(),
  ingress_private=True,
)


@service.handler()
async def transcriber(
  ctx: restate.Context, input: TranscriberInput
) -> TranscriptionAgentOutput:
  try:
    restate_agent = TranscriptionAgent().restate_agent
    return (
      await restate_agent.run(
        user_prompt=[
          AudioUrl(
            url=input.audio_uri,
            media_type=input.audio_media_type,
          )
        ],
        deps=TranscriptioAgentDeps(
          created_at_local=input.agent_deps.created_at_local,
          location=input.agent_deps.location,
        ),
      )
    ).output
  except ContentFilterError as e:
    raise restate.TerminalError(
      message=(f"Content filter error: {e.message}."),
      status_code=400,
      metadata={"response_body": e.body if e.body else ""},
    )
  except restate.TerminalError:
    raise


@service.handler()
async def image_describer(
  ctx: restate.Context, input: ImageInput
) -> ImageDescriberAgentOutput:
  try:
    restate_agent = ImageDescriberAgent().restate_agent
    return (
      await restate_agent.run(
        user_prompt=[
          ImageUrl(
            url=input.image_uri,
            media_type=input.image_media_type,
          )
        ],
        deps=ImageDescriberAgentDeps(
          created_at_local=input.agent_deps.created_at_local,
          location=input.agent_deps.location,
        ),
      )
    ).output
  except ContentFilterError as e:
    raise restate.TerminalError(
      message=(f"Content filter error: {e.message}."),
      status_code=400,
      metadata={"response_body": e.body if e.body else ""},
    )
  except restate.TerminalError:
    raise


@service.handler()
async def video_describer(
  ctx: restate.Context, input: VideoInput
) -> VideoDescriberAgentOutput:
  try:
    restate_agent = VideoDescriberAgent().restate_agent
    return (
      await restate_agent.run(
        user_prompt=[
          VideoUrl(
            url=input.video_uri,
            media_type=input.video_media_type,
          )
        ],
        deps=VideoDescriberAgentDeps(
          created_at_local=input.agent_deps.created_at_local,
          location=input.agent_deps.location,
        ),
      )
    ).output
  except ContentFilterError as e:
    raise restate.TerminalError(
      message=(f"Content filter error: {str(e)}."),
      status_code=400,
    )
  except restate.TerminalError:
    raise


@service.handler()
async def title_generator(
  ctx: restate.Context, input: TextInput
) -> TitleGeneratorAgentOutput:
  try:
    restate_agent = TitleGeneratorAgent().restate_agent

    return (
      await restate_agent.run([
        DocumentUrl(
          url=input.text_uri,
          media_type=input.text_media_type,
        )
      ])
    ).output
  except ContentFilterError as e:
    raise restate.TerminalError(
      message=(f"Content filter error: {str(e)}."),
      status_code=400,
    )
  except restate.TerminalError:
    raise


# @service.handler()
# async def pdf_describer(
#   ctx: restate.Context, input: PDFInput
# ) -> PDFDescriberAgentOutput:
#   try:
#     restate_agent = PDFDescriberAgent().restate_agent
#     return (
#       await restate_agent.run([
#         DocumentUrl(
#           url=input.pdf_uri,
#           media_type=input.pdf_media_type,
#         )
#       ])
#     ).output
#   except ContentFilterError as e:
#     raise restate.TerminalError(
#       message=(f"Content filter error: {str(e)}."),
#       status_code=400,
#     )
#   except restate.TerminalError:
#     raise


# @service.handler()
# async def moderator(ctx: restate.Context, input: TextInput) -> ModeratorAgentOutput:
#   try:
#     restate_agent = ModeratorAgent().restate_agent

#     harm_types = "\n".join(f"- {harm.name}: {harm.value}" for harm in HarmTypeStrEnum)

#     return (
#       await restate_agent.run(
#         [DocumentUrl(url=input.text_uri, media_type=input.text_media_type)],
#         deps=ModeratorAgentDeps(harm_types=harm_types),
#       )
#     ).output
#   except restate.TerminalError:
#     raise


app = restate.app(
  services=[service],
  identity_keys=get_restate_identity_keys(settings),
)

from pathlib import Path
from types import NoneType
from typing import assert_never, cast

import yaml
from google.genai.types import HarmBlockThreshold, HarmCategory
from lib.utils import get_restate_run_options
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.providers.google_cloud import GoogleCloudProvider
from restate.ext.pydantic import RestateAgent

from .image_describer.models import ImageDescriberAgentDeps, ImageDescriberAgentOutput
from .models import AgentConfig

# from .moderator.models import ModeratorAgentDeps, ModeratorAgentOutput
from .pdf_describer.models import PDFDescriberAgentOutput
from .title_generator.models import TitleGeneratorAgentOutput
from .transcriber.models import TranscriptioAgentDeps, TranscriptionAgentOutput
from .types import AgentDepsT, AgentNameT, AgentOutputT, ModelProviderT, ModelT
from .video_describer.models import VideoDescriberAgentDeps, VideoDescriberAgentOutput

_AGENT_DIR = Path(__file__).parent


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class TAIAgent[
  DepsT: AgentDepsT,
  OutputT: AgentOutputT,
]:
  _model_provider: ModelProviderT
  _agent_name: AgentNameT
  _deps_type: type[DepsT]
  _output_type: type[OutputT]

  @property
  def _spec_path(self) -> Path:
    return _AGENT_DIR / self._agent_name / "specs.yaml"

  @property
  def _config(self) -> AgentConfig:
    with open(_AGENT_DIR / self._agent_name / "configs.yaml", "r") as f:
      return AgentConfig.model_validate(yaml.safe_load(f))

  @property
  def _google_model(self) -> GoogleModel:
    return GoogleModel(
      model_name=self._config.model_name,
      provider=GoogleCloudProvider(location="global"),
      settings=GoogleModelSettings(
        temperature=self._config.temperature,
        timeout=self._config.timeout,
        max_tokens=self._config.max_tokens,
        google_safety_settings=[
          {
            "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
            "threshold": HarmBlockThreshold.BLOCK_NONE,
          },
          {
            "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            "threshold": HarmBlockThreshold.BLOCK_NONE,
          },
          {
            "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            "threshold": HarmBlockThreshold.BLOCK_NONE,
          },
          {
            "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            "threshold": HarmBlockThreshold.BLOCK_NONE,
          },
        ],
      ),
    )

  @property
  def _model(self) -> ModelT:
    match self._model_provider:
      case "google":
        return self._google_model
      case _:
        assert_never(self._model_provider)

  @property
  def restate_agent(self) -> RestateAgent[DepsT, OutputT]:
    return RestateAgent(
      cast(
        Agent[DepsT, OutputT],
        Agent.from_file(
          path=self._spec_path,
          model=self._model,
          deps_type=self._deps_type,
          output_type=self._output_type,
        ),
      ),
      run_options=get_restate_run_options(),
    )


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class TranscriptionAgent(TAIAgent[TranscriptioAgentDeps, TranscriptionAgentOutput]):
  _model_provider: ModelProviderT = "google"
  _agent_name: AgentNameT = "transcriber"
  _deps_type: type[TranscriptioAgentDeps] = TranscriptioAgentDeps
  _output_type: type[TranscriptionAgentOutput] = TranscriptionAgentOutput


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class ImageDescriberAgent(TAIAgent[ImageDescriberAgentDeps, ImageDescriberAgentOutput]):
  _model_provider: ModelProviderT = "google"
  _agent_name: AgentNameT = "image_describer"
  _deps_type: type[ImageDescriberAgentDeps] = ImageDescriberAgentDeps
  _output_type: type[ImageDescriberAgentOutput] = ImageDescriberAgentOutput


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class VideoDescriberAgent(TAIAgent[VideoDescriberAgentDeps, VideoDescriberAgentOutput]):
  _model_provider: ModelProviderT = "google"
  _agent_name: AgentNameT = "video_describer"
  _deps_type: type[VideoDescriberAgentDeps] = VideoDescriberAgentDeps
  _output_type: type[VideoDescriberAgentOutput] = VideoDescriberAgentOutput


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class PDFDescriberAgent(TAIAgent[None, PDFDescriberAgentOutput]):
  _model_provider: ModelProviderT = "google"
  _agent_name: AgentNameT = "pdf_describer"
  _deps_type: type[None] = NoneType
  _output_type: type[PDFDescriberAgentOutput] = PDFDescriberAgentOutput


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class TitleGeneratorAgent(TAIAgent[None, TitleGeneratorAgentOutput]):
  _model_provider: ModelProviderT = "google"
  _agent_name: AgentNameT = "title_generator"
  _deps_type: type[None] = NoneType
  _output_type: type[TitleGeneratorAgentOutput] = TitleGeneratorAgentOutput


# @dataclass(kw_only=True,config=ConfigDict(arbitrary_types_allowed=True))
# class ModeratorAgent(TAIAgent[ModeratorAgentDeps, ModeratorAgentOutput]):
#   _model_provider: ModelProviderT = "google"
#   _agent_name: AgentNameT = "moderator"

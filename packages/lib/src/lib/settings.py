from logfire import LevelName
from pydantic import BaseModel, Field, HttpUrl, SecretStr, computed_field
from pydantic_settings import (
  BaseSettings,
  GoogleSecretManagerSettingsSource,
  PydanticBaseSettingsSource,
  SettingsConfigDict,
)

TAI_NAMING_PATTERN = r"^tai-.*$"


class QdrantSetting(BaseModel):
  url: HttpUrl
  api_key: SecretStr


class AISetting(BaseModel):
  pydantic_ai_gateway_api_key: SecretStr
  alibaba_api_key: SecretStr


class OtherSertting(BaseModel):
  logfire_token: SecretStr


class Settings(BaseSettings):
  model_config = SettingsConfigDict(frozen=True)

  is_local: bool = Field(validation_alias="TAI_IS_LOCAL")

  project: str = Field(
    validation_alias="GOOGLE_CLOUD_PROJECT", pattern=TAI_NAMING_PATTERN
  )

  restate_identity_key: str

  qdrant: QdrantSetting
  ai: AISetting
  other: OtherSertting

  @computed_field
  @property
  def env(self) -> str:
    return self.project.split("-")[-1]

  @computed_field
  @property
  def log_level(self) -> LevelName:
    match self.env:
      case "dev":
        return "info"
      case "tst":
        return "debug"
      case "prd":
        return "error"
      case _:
        return "error"

  @computed_field
  @property
  def service_account(self) -> str:
    return f"{self.project}-sa-cloud-run"

  @classmethod
  def settings_customise_sources(
    cls,
    settings_cls: type[BaseSettings],
    init_settings: PydanticBaseSettingsSource,
    env_settings: PydanticBaseSettingsSource,
    dotenv_settings: PydanticBaseSettingsSource,
    file_secret_settings: PydanticBaseSettingsSource,
  ) -> tuple[PydanticBaseSettingsSource, ...]:
    return (
      init_settings,
      env_settings,
      dotenv_settings,
      file_secret_settings,
      GoogleSecretManagerSettingsSource(settings_cls),
    )

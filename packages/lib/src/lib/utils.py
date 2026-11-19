from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_DNS, UUID, uuid4, uuid5

from google.genai.client import AsyncClient, Client
from restate import InvocationRetryPolicy, RunOptions

from .settings import Settings

_DOMAIN = "themselves.ai"
_NAMESPACE = uuid5(NAMESPACE_DNS, _DOMAIN)
_DEFAULT_MAX_ATTEMPTS = 2
_DEFAULT_INITIAL_RETRY_INTERVAL_SECONDS = 30


def get_settings() -> Settings:
  return Settings()  # type:ignore[reportCallIssue]


def generate_uuid(value: str | None = None) -> UUID:
  if value:
    uuid = uuid5(_NAMESPACE, value)
  else:
    uuid = uuid4()

  return uuid


def get_genai_client(location: str = "global") -> AsyncClient:
  return Client(enterprise=True, location=location).aio


def get_restate_run_options(
  max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
  initial_retry_interval_seconds: int = _DEFAULT_INITIAL_RETRY_INTERVAL_SECONDS,
) -> RunOptions:
  return RunOptions(
    max_attempts=max_attempts,
    initial_retry_interval=timedelta(seconds=initial_retry_interval_seconds),
  )


def get_restate_invocation_retry_policy(
  max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
) -> InvocationRetryPolicy:
  return InvocationRetryPolicy(max_attempts=max_attempts, on_max_attempts="pause")


def get_restate_identity_keys(settings: Settings) -> list[str] | None:
  if settings.is_local:
    return None
  else:
    return [settings.restate_identity_key]


def get_ingress_private(settings: Settings) -> bool:
  return not settings.is_local


def get_now_utc() -> datetime:
  return datetime.now(UTC)

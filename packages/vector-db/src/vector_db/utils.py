from pathlib import Path

import yaml
from lib.settings import Settings
from qdrant_client import AsyncQdrantClient

from .models import CollectionConfig
from .types import CollectionNameT

_COLLECTION_CONFIGS_DIR = Path(__file__).parent / "collection_configs"
_QDRANT_TIMEOUT_DEFAULT = 180  # seconds


def get_qdrant_client(settings: Settings) -> AsyncQdrantClient:
  return AsyncQdrantClient(
    url=settings.qdrant.url.unicode_string(),
    api_key=settings.qdrant.api_key.get_secret_value(),
    timeout=_QDRANT_TIMEOUT_DEFAULT,
    prefer_grpc=True,
  )


def load_config(collection_name: CollectionNameT) -> CollectionConfig:
  with open(_COLLECTION_CONFIGS_DIR / f"{collection_name}.yaml", "r") as f:
    return CollectionConfig.model_validate(yaml.safe_load(f))

from pathlib import Path

import restate
from lib.utils import (
  get_genai_client,
  get_ingress_private,
  get_restate_identity_keys,
  get_restate_invocation_retry_policy,
  get_settings,
)
from qdrant_client import models
from vector_db.embed import ImageEmbedder, PDFEmbedder, TextEmbedder, VideoEmbedder
from vector_db.models import (
  EmbedResponse,
  ImageEmbedderInput,
  PDFEmbedderInput,
  TextEmbedderInput,
  UserQueryInput,
  VideoEmbedderInput,
)
from vector_db.qdrant import Collection, UserQuery
from vector_db.utils import get_qdrant_client

from .models import (
  CreateCollectionInput,
  CreateCollectionPayloadIndexInput,
  CreateCollectionResponse,
  QueryGroupPointsResponse,
  UpsertMomentInput,
)

SERVICE_NAME = Path(__file__).parent.name

settings = get_settings()

genai_client = get_genai_client()
qdrant_client = get_qdrant_client(settings)

service = restate.Service(
  SERVICE_NAME,
  invocation_retry_policy=get_restate_invocation_retry_policy(),
  ingress_private=get_ingress_private(settings),
)


@service.handler()
async def query_point_groups(
  ctx: restate.Context, input: UserQueryInput
) -> QueryGroupPointsResponse:
  query = UserQuery(
    client=qdrant_client,
    settings=settings,
    collection_name=input.collection_name,
    query=input.query,
    query_period=input.query_period,
    query_tuning=input.query_tuning,
    auth_uid=input.auth_uid,
  )

  point_groups = [group async for group in query.group_points()]

  return QueryGroupPointsResponse(point_groups=point_groups)


@service.handler()
async def embed_text(ctx: restate.Context, input: TextEmbedderInput) -> EmbedResponse:
  return await TextEmbedder(
    genai_client=genai_client, ctx=ctx, text_embedder_input=input
  ).get_embed_response()


@service.handler()
async def embed_image(ctx: restate.Context, input: ImageEmbedderInput) -> EmbedResponse:
  return await ImageEmbedder(
    genai_client=genai_client, ctx=ctx, image_embedder_input=input
  ).get_embed_response()


@service.handler()
async def embed_video(ctx: restate.Context, input: VideoEmbedderInput) -> EmbedResponse:
  return await VideoEmbedder(
    genai_client=genai_client, ctx=ctx, video_embedder_input=input
  ).get_embed_response()


@service.handler()
async def embed_pdf(ctx: restate.Context, input: PDFEmbedderInput) -> EmbedResponse:
  return await PDFEmbedder(
    genai_client=genai_client, ctx=ctx, pdf_embedder_input=input
  ).get_embed_response()


@service.handler()
async def upsert_moment(
  ctx: restate.Context, input: UpsertMomentInput
) -> models.UpdateResult:
  collection = Collection(
    client=qdrant_client, settings=settings, collection_name="moment"
  )

  return await collection.upsert_point(
    vector=input.vector,
    payload=input.payload.model_dump(mode="json"),
    id=input.id,
  )


@service.handler()
async def create_collection(
  ctx: restate.Context, input: CreateCollectionInput
) -> CreateCollectionResponse:
  collection = Collection(
    client=qdrant_client, settings=settings, collection_name=input.collection_name
  )

  if await collection.exists():
    return CreateCollectionResponse(exists=True, created=False)

  await collection.create_collection()

  return CreateCollectionResponse(exists=False, created=True)


@service.handler()
async def create_collection_payload_index(
  ctx: restate.Context, input: CreateCollectionPayloadIndexInput
) -> models.UpdateResult:
  collection = Collection(
    client=qdrant_client, settings=settings, collection_name=input.collection_name
  )

  return await collection.create_payload_index(input.payload_index_schema)


app = restate.app(
  services=[service],
  identity_keys=get_restate_identity_keys(settings),
)

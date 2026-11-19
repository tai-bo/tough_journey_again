from collections.abc import AsyncIterator
from functools import lru_cache
from pathlib import Path

import networkx as nx
import yaml
from lib.models import UpdateRecordBase
from lib.settings import Settings
from lib.utils import generate_uuid, get_now_utc
from networkx.algorithms.community import louvain_communities
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass
from pyvis.network import Network
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.conversions.common_types import QueryResponse
from user.types import AuthUIDT

from .models import (
  CollectionConfig,
  FullTextIndexSchema,
  PayloadIndexSchema,
  PointGroup,
  QueryParam,
  QueryPeriod,
  QueryTuning,
)
from .types import CollectionNameT, QueryT
from .utils import load_config

_QUERY_YAML_DIR = Path(__file__).parent / "queries"
_ALL_POINTS_SOFT_CAP = 30_000
_DEFAULT_AVG_WEIGHT = 0.0
_LOUVAIN_COMMUNITIES_RESOLUTION = 1.0
_LOUVAIN_COMMUNITIES_SEED = 3
_WEIGHT_KEY = "weight"
_GROUP_KEY = "group"


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class Collection:
  client: AsyncQdrantClient
  settings: Settings
  collection_name: CollectionNameT
  _config: CollectionConfig = Field(init=False)

  def __post_init__(self):
    self._config = load_config(self.collection_name)

  @property
  def _vectors_config(self) -> dict[str, models.VectorParams]:
    vector_config_dict = {}
    for vector_config in self._config.vector_configs:
      vector_config_dict[vector_config.name] = models.VectorParams(
        size=vector_config.size, distance=vector_config.distance, on_disk=True
      )
    return vector_config_dict

  async def exists(self) -> bool:
    return await self.client.collection_exists(self.collection_name)

  async def create_collection(self) -> None:
    collection_created = await self.client.create_collection(
      collection_name=self.collection_name,
      vectors_config=self._vectors_config,
      quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
          type=models.ScalarType.INT8, quantile=0.99, always_ram=True
        )
      ),
    )

    if collection_created:
      if self._config.index_auth_uid:
        await self.client.create_payload_index(
          collection_name=self.collection_name,
          field_name="auth_uid",
          field_schema=models.KeywordIndexParams(
            type=models.KeywordIndexType.KEYWORD, is_tenant=True
          ),
        )

      for schema in self._config.payload_index_schemas:
        await self.create_payload_index(schema)

      for schema in self._config.full_text_index_schemas:
        await self.create_full_text_index(schema)

  async def create_payload_index(
    self, payload_index_schema: PayloadIndexSchema
  ) -> models.UpdateResult:
    return await self.client.create_payload_index(
      collection_name=self.collection_name,
      field_name=payload_index_schema.field_name,
      field_schema=payload_index_schema.field_schema,
    )

  async def create_full_text_index(
    self, full_text_index_schema: FullTextIndexSchema
  ) -> models.UpdateResult:
    return await self.client.create_payload_index(
      collection_name=self.collection_name,
      field_name=full_text_index_schema.field_name,
      field_schema=models.TextIndexParams(
        on_disk=True,
        type=models.TextIndexType.TEXT,
        tokenizer=models.TokenizerType.MULTILINGUAL,
        ascii_folding=True,
        stemmer=models.SnowballParams(
          type=models.Snowball.SNOWBALL, language=models.SnowballLanguage.ENGLISH
        ),
        stopwords=models.StopwordsSet(
          languages=[models.Language.ENGLISH, models.Language.CHINESE]
        ),
        phrase_matching=True,
      ),
    )

  async def upsert_point(
    self,
    vector: models.VectorStruct,
    payload: models.Payload,
    id: models.ExtendedPointId | None = None,
  ) -> models.UpdateResult:
    if id is None:
      id = generate_uuid()

    upsert_payload = payload | UpdateRecordBase(
      updated_at=get_now_utc(), updated_by=self.settings.service_account
    ).model_dump(mode="json")

    return await self.client.upsert(
      collection_name=self.collection_name,
      points=[models.PointStruct(id=id, vector=vector, payload=upsert_payload)],
    )


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class Query(Collection):
  query: QueryT
  query_period: QueryPeriod
  query_tuning: QueryTuning
  _graph: nx.Graph = Field(default_factory=nx.Graph, init=False)

  @staticmethod
  @lru_cache
  def _load_query_param(query: QueryT) -> QueryParam:
    with open(f"{_QUERY_YAML_DIR}/{query}.yaml", "r") as f:
      yaml_data = yaml.safe_load(f)

    yaml_data["query"] = query

    return QueryParam.model_validate(yaml_data)

  @property
  def _query_param(self) -> QueryParam:
    return self._load_query_param(self.query)

  @property
  def _field_condition_date_range(self) -> models.Condition:
    return models.FieldCondition(
      key=self._query_param.datetime_filter_field,
      range=models.DatetimeRange(
        gte=self.query_period.from_datetime, lte=self.query_period.to_datetime
      ),
    )

  @property
  def _must_filters(self) -> list[models.Condition]:
    must_filters = [self._field_condition_date_range]

    return must_filters

  async def _query_batch_points(
    self, requests: list[models.QueryRequest]
  ) -> list[QueryResponse]:
    return await self.client.query_batch_points(
      collection_name=self.collection_name, requests=requests
    )

  async def get_point_payloads(
    self, point_ids: list
  ) -> list[dict[models.ExtendedPointId, models.Payload]]:
    points = await self.client.retrieve(
      collection_name=self.collection_name,
      ids=point_ids,
      with_payload=self._query_param.with_payloads,
      with_vectors=False,
    )

    return [{p.id: p.payload} for p in points if p.payload]

  # TODO Add a `soft_cap_hit` bool in the return?
  async def _get_all_points(self) -> AsyncIterator[list[models.Record]]:
    total_point_count = 0
    next_page_offset = None

    while total_point_count < _ALL_POINTS_SOFT_CAP:
      points, next_page_offset = await self.client.scroll(
        collection_name=self.collection_name,
        scroll_filter=models.Filter(must=self._must_filters),
        limit=self._query_param.page_size,
        offset=next_page_offset,
        with_payload=False,
        with_vectors=False,
      )

      if not points:
        break

      yield points
      total_point_count += len(points)

      if next_page_offset is None:
        break

  def _get_nearest_points_requests(
    self, for_points: list[models.Record]
  ) -> list[models.QueryRequest]:
    requests = []

    for p in for_points:
      requests.append(
        models.QueryRequest(
          prefetch=[
            models.Prefetch(
              query=p.id,
              using=v,
              filter=models.Filter(
                must=self._must_filters, must_not=models.HasIdCondition(has_id=[p.id])
              ),
              score_threshold=self.query_tuning.score_threshold,
              limit=self.query_tuning.prefetch_limit,
            )
            for v in self._query_param.with_vectors
          ],
          query=models.RrfQuery(rrf=models.Rrf(k=60)),
          limit=self.query_tuning.query_limit,
          with_vector=False,
          with_payload=False,
        )
      )

    return requests

  async def _get_nearest_points(
    self,
  ) -> AsyncIterator[tuple[models.Record, list[models.ScoredPoint]]]:

    async for page_points in self._get_all_points():
      nearest_points_requests = self._get_nearest_points_requests(page_points)
      nearest_points = await self._query_batch_points(nearest_points_requests)

      for point, response in zip(page_points, nearest_points):
        yield point, response.points

  async def _build_graph(self) -> None:
    self._graph.clear()

    async for point, nearest_points in self._get_nearest_points():
      self._graph.add_node(point.id)

      for nearest_point in nearest_points:
        self._graph.add_edge(point.id, nearest_point.id, weight=nearest_point.score)

  def _get_sorted_payloads_for_nodes(self, payloads: dict, nodes: list | set) -> list:
    return sorted(
      [payloads[node] for node in nodes],
      key=lambda x: getattr(x, self._query_param.payload_sort_by),
    )

  def _get_avg_weight(self, nodes: set) -> float:
    subgraph = self._graph.subgraph(nodes)
    edge_weights = [d[_WEIGHT_KEY] for _, _, d in subgraph.edges(data=True)]
    return round(
      sum(edge_weights) / len(edge_weights) if edge_weights else _DEFAULT_AVG_WEIGHT, 3
    )

  def _get_payloads(
    self, for_points: list[models.Record]
  ) -> dict[models.ExtendedPointId, models.Payload]:
    return {
      point.id: point.payload for point in for_points if point.payload is not None
    }

  def generate_graph_html(self) -> str:
    nt = Network(height="100vh", width="100%", neighborhood_highlight=True)
    nt.from_nx(self._graph)

    return nt.generate_html()

  async def group_points(self) -> AsyncIterator[PointGroup]:
    # payloads = self._get_payloads(for_points)

    await self._build_graph()

    isolates = list(nx.isolates(self._graph))

    if self.query_tuning.remove_isolates:
      self._graph.remove_nodes_from(isolates)

    communities = louvain_communities(
      self._graph,
      resolution=_LOUVAIN_COMMUNITIES_RESOLUTION,
      seed=_LOUVAIN_COMMUNITIES_SEED,
      weight=_WEIGHT_KEY,
    )

    for i, nodes in enumerate(communities):
      avg_weight = self._get_avg_weight(nodes)

      for node_id in nodes:
        self._graph.nodes[node_id][_GROUP_KEY] = i

      if avg_weight >= self.query_tuning.avg_weight_threshold:
        yield PointGroup(
          group_type="communities",
          group_index=i,
          count=len(nodes),
          avg_weight=avg_weight,
          point_ids=list(nodes),
        )

    if isolates:
      yield PointGroup(
        group_type="isolates", group_index=-1, count=len(isolates), point_ids=isolates
      )


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class UserQuery(Query):
  auth_uid: AuthUIDT

  @property
  def _must_filters(self) -> list[models.Condition]:
    return [
      *super()._must_filters,
      models.FieldCondition(
        key="auth_uid", match=models.MatchValue(value=self.auth_uid)
      ),
    ]

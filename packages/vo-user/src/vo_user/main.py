from pathlib import Path

import restate
from lib.utils import (
  get_restate_identity_keys,
  get_restate_invocation_retry_policy,
  get_settings,
)

from .models import Isolates, IsolatesResponse, Request, RequestResponse

VO_NAME = Path(__file__).parent.name

settings = get_settings()

virtual_object = restate.VirtualObject(
  VO_NAME,
  invocation_retry_policy=get_restate_invocation_retry_policy(),
  ingress_private=True,
)


@virtual_object.handler()
async def add_request(ctx: restate.ObjectContext, request: Request) -> RequestResponse:
  current_count = (await ctx.get(request.vo_state_name, type_hint=int)) or 0
  new_count = current_count + 1
  ctx.set(request.vo_state_name, new_count)

  return RequestResponse(vo_state_name=request.vo_state_name, new_count=new_count)


@virtual_object.handler()
async def replace_isolates(
  ctx: restate.ObjectContext, isolates: Isolates
) -> IsolatesResponse:
  ctx.set("isolates", isolates)

  return IsolatesResponse(
    last_updated=isolates.last_updated,
    query_id=isolates.query_id,
    point_count=len(isolates.point_ids),
  )


app = restate.app(
  services=[virtual_object],
  identity_keys=get_restate_identity_keys(settings),
)

#!/bin/bash

# Kill anything already on 9080
lsof -ti :9080 | xargs kill -9 2>/dev/null || true

export GOOGLE_CLOUD_PROJECT=tai-pr-dev
export TAI_IS_LOCAL=1
export RESTATE_IDENTITY_KEY=publickeyv1_2U9tpRcJH8AJpBB7zm5CTfP77gYLGnF31onfwKBjEUhc

restate config use-env local

uv run hypercorn tests.local_server:app --config hypercorn-config.toml
# 4GOT

This is the backend for an app where people capture "moments" from their day as voice notes, photos, videos or text. Each moment is described by AI, turned into vectors so it can be searched by meaning, and stored with its time and place. Related moments are then grouped so they can be turned into useful outputs, such as material for a performance review.

It is a set of small Python services in one uv workspace. [Restate](https://restate.dev) runs the workflows, and each service runs on Google Cloud Run.

This is the second version of the idea. The first was a single FastAPI service for voice notes only.

## Services

| Service | What it does |
|---|---|
| `sv-input` | One workflow per input type (audio, image, video, text): describe → embed → save |
| `sv-agent` | AI agents: transcriber, image describer, video describer, title generator |
| `sv-vector-db` | Embeds text, images and video, saves moments to Qdrant and groups them |
| `vo-user` | Keeps a record of each user's requests, one user at a time |
| `sv-ouput` | Summarises groups of moments (in progress) |

Shared packages: `agent`, `vector-db`, `storage`, `user`, `lib`.

## Key strengths

- **Durable workflows:** each step in a workflow is a separate Restate service call. If a step fails, Restate retries it without redoing the steps that already finished, and idempotency keys stop the same input being processed twice.
- **Multimodal AI:** audio, image, video and text inputs each have their own pipeline, using Gemini models through pydantic-ai and Gemini embeddings.
- **Per-user consistency:** a Restate Virtual Object handles each user's requests one at a time, so they can't clash.
- **Search design:** each moment has three vectors (for search, classification and clustering), with indexes on time, tags, location and full text. Related moments are grouped by similarity.
- **Config over code:** each agent's model and settings, and each Qdrant collection and query, are defined in YAML files.
- **Monorepo and deployment:** 10 packages in one uv workspace, each service with its own Docker image. A tag in the commit message, such as `[deploy:sv-input]`, makes GitHub Actions build and deploy only that service to Cloud Run.
- **Observability:** Logfire traces the AI agent calls.

## Tech stack

Python 3.14 · Restate · pydantic-ai · Pydantic v2 · Gemini · Qdrant · Cloud Storage · Logfire · Docker · GitHub Actions · Cloud Run · uv

## Status

Paused. The audio, image, video and text pipelines work end to end. PDF input, content moderation and the summary service were started but not finished.

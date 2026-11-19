# ---------- Builder stage ----------
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

ENV UV_PYTHON_DOWNLOADS=0
ENV PYTHONUNBUFFERED=True

WORKDIR /app

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-install-workspace --no-editable --package sv-input

COPY . .
RUN uv sync --frozen --no-editable --package sv-input

# ---------- Final stage ----------
FROM python:3.14-slim
ENV PYTHONUNBUFFERED=True
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY hypercorn-config.toml /app/hypercorn-config.toml

EXPOSE 9080

CMD ["/app/.venv/bin/python", "-m", "hypercorn", "--config", "hypercorn-config.toml", "sv_input.main:app"]
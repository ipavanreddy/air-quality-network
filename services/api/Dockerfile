# VayuDrishti API (FastAPI) for Cloud Run.
# Build context is the REPOSITORY ROOT, because the API reads prompts/schemas from ai/ and adapters/sample
# data from data/ at runtime (app/config.py resolves them relative to the repo root):
#   docker build -f services/api/Dockerfile -t air-quality-network-api .
# The image keeps the repo layout under /srv so REPO_ROOT (= parents[3] of app/config.py) is /srv.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /srv/services/api
COPY services/api/pyproject.toml services/api/uv.lock services/api/.python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY services/api/app ./app
COPY ai/prompts /srv/ai/prompts
COPY ai/schemas /srv/ai/schemas
COPY data/adapters /srv/data/adapters
COPY data/schemas /srv/data/schemas
COPY data/sample /srv/data/sample

# Run as an unprivileged user; .localdata is the (ephemeral) local store used alongside BigQuery / GCS.
RUN useradd --system --uid 10001 app && mkdir -p /srv/services/api/.localdata && chown -R app /srv/services/api/.localdata
USER app

EXPOSE 8080
CMD ["sh", "-c", "exec /srv/services/api/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]

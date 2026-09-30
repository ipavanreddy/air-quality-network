#!/usr/bin/env bash
# Deploy VayuDrishti to Cloud Run (asia-south1). Run by the project lead, not by CI.
#
#   CORS_ORIGINS="https://<citizen>.vercel.app,https://<officer>.vercel.app" \
#   CORS_ORIGIN_REGEX='https://.*\.vercel\.app' \
#   infrastructure/cloud-run/deploy.sh api
#
# DRY_RUN=1 builds the staged source with local Docker and prints the env file instead of deploying.
#
# Targets: api  (the two Next.js apps go to Vercel; see infrastructure/vercel/README.md)
#
# It stages exactly the files services/api/Dockerfile needs (services/api, ai/, data/) into a temp dir with
# the Dockerfile at its root, then `gcloud run deploy --source` builds it with Cloud Build. No .env,
# credentials or node_modules are uploaded. API keys come from Secret Manager; Gemini runs on Vertex AI
# with the service account (no Gemini key needed).
set -euo pipefail

TARGET="${1:-}"
PROJECT="${GOOGLE_CLOUD_PROJECT:-spontom-build-with-ai}"
REGION="${REGION:-asia-south1}"
SERVICE="${SERVICE:-air-quality-network-api}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-hackathon-dev@spontom-build-with-ai.iam.gserviceaccount.com}"
BIGQUERY_DATASET="${BIGQUERY_DATASET:-air_quality_network}"
GCS_BUCKET="${GCS_BUCKET:-spontom-build-with-ai-media}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-flash}"
CORS_ORIGINS="${CORS_ORIGINS:-}"
CORS_ORIGIN_REGEX="${CORS_ORIGIN_REGEX:-}"
SENSOR_INGEST_TOKEN="${SENSOR_INGEST_TOKEN:-}"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

usage() {
  sed -n '2,15p' "$0"
  exit 1
}

deploy_api() {
  if [[ -z "$CORS_ORIGINS" && -z "$CORS_ORIGIN_REGEX" ]]; then
    echo "error: set CORS_ORIGINS (comma-separated Vercel URLs) and/or CORS_ORIGIN_REGEX" >&2
    exit 1
  fi
  for v in CORS_ORIGINS CORS_ORIGIN_REGEX SENSOR_INGEST_TOKEN; do
    if [[ "${!v}" == *"'"* ]]; then
      echo "error: $v must not contain a single quote" >&2
      exit 1
    fi
  done

  local work stage envfile
  work="$(mktemp -d)"
  trap "rm -rf '$work'" EXIT
  stage="$work/src"
  envfile="$work/env.yaml"

  mkdir -p "$stage/services/api" "$stage/ai" "$stage/data"
  cp "$ROOT/services/api/Dockerfile" "$stage/Dockerfile"
  cp "$ROOT/.dockerignore" "$stage/.dockerignore"
  cp "$ROOT/services/api/pyproject.toml" "$ROOT/services/api/uv.lock" "$ROOT/services/api/.python-version" \
    "$stage/services/api/"
  rsync -a --exclude '__pycache__' --exclude '*.pyc' "$ROOT/services/api/app" "$stage/services/api/"
  rsync -a "$ROOT/ai/prompts" "$ROOT/ai/schemas" "$stage/ai/"
  rsync -a "$ROOT/data/adapters" "$ROOT/data/schemas" "$ROOT/data/sample" "$stage/data/"

  # Guard: never upload anything that looks like a key.
  if grep -rIlE 'AIza[0-9A-Za-z_-]{20,}|PRIVATE KEY' "$stage" >/dev/null 2>&1; then
    echo "error: staged files contain something that looks like a key; aborting" >&2
    exit 1
  fi

  # YAML env file: avoids gcloud's comma splitting for CORS_ORIGINS and keeps regex backslashes literal.
  {
    echo "GOOGLE_CLOUD_PROJECT: '$PROJECT'"
    echo "BIGQUERY_DATASET: '$BIGQUERY_DATASET'"
    echo "GCS_BUCKET: '$GCS_BUCKET'"
    echo "GEMINI_MODEL: '$GEMINI_MODEL'"
    echo "GOOGLE_GENAI_USE_VERTEXAI: 'true'"
    echo "GOOGLE_CLOUD_LOCATION: 'global'"
    echo "CORS_ORIGINS: '$CORS_ORIGINS'"
    echo "CORS_ORIGIN_REGEX: '$CORS_ORIGIN_REGEX'"
    if [[ -n "$SENSOR_INGEST_TOKEN" ]]; then
      echo "SENSOR_INGEST_TOKEN: '$SENSOR_INGEST_TOKEN'"
    fi
  } >"$envfile"

  if [[ "${DRY_RUN:-}" == "1" ]]; then
    echo "--- env.yaml"; cat "$envfile"
    echo "--- staged files: $(find "$stage" -type f | wc -l | tr -d ' ')"
    docker build -q -t "$SERVICE:dry-run" "$stage"
    echo "DRY_RUN: built $SERVICE:dry-run locally; nothing deployed."
    return
  fi

  # One instance on purpose: the MVP's operational store is an in-process JSON file (mirrored to BigQuery
  # and Cloud Storage), so a single warm instance keeps the demo consistent. See README "Deployment".
  gcloud run deploy "$SERVICE" \
    --project "$PROJECT" \
    --region "$REGION" \
    --source "$stage" \
    --service-account "$SERVICE_ACCOUNT" \
    --allow-unauthenticated \
    --env-vars-file "$envfile" \
    --set-secrets "MAPS_API_KEY=maps-api-key:latest,GOOGLE_CLOUD_API_KEY=google-api-key:latest" \
    --min-instances 1 \
    --max-instances 1 \
    --concurrency 40 \
    --cpu 1 \
    --memory 1Gi \
    --timeout 300 \
    --cpu-boost \
    --quiet

  local url
  url="$(gcloud run services describe "$SERVICE" --project "$PROJECT" --region "$REGION" \
    --format 'value(status.url)')"
  echo "Deployed: $url"
  echo "Smoke test: curl -s $url/health && curl -s $url/api/config"
}

case "$TARGET" in
  api) deploy_api ;;
  *) usage ;;
esac

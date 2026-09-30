#!/usr/bin/env bash
# Deploy one Next.js app to Cloud Run (public, asia-south1), as an alternative to Vercel.
#
#   infrastructure/cloud-run/deploy-web.sh <app-folder> [<app-folder> ...]
#
# Each app builds on its own (no workspace deps), so the app folder is staged into a temp dir with a
# generated Dockerfile and deployed with `gcloud run deploy --source` (Cloud Build). NEXT_PUBLIC_* values
# are baked in at build time from a generated .env.production that exists only in the staging dir:
#   NEXT_PUBLIC_API_URL       <- URL of the deployed API service
#   NEXT_PUBLIC_MAPS_API_KEY  <- $NEXT_PUBLIC_MAPS_API_KEY, else apps/<app>/.env.local (browser key,
#                                HTTP-referrer restricted; never committed)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

SLUG="$(basename "$ROOT")"
PROJECT="${GOOGLE_CLOUD_PROJECT:-spontom-build-with-ai}"
REGION="${REGION:-asia-south1}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-hackathon-dev@${PROJECT}.iam.gserviceaccount.com}"
API_SERVICE="${API_SERVICE:-${SLUG}-api}"

[ $# -gt 0 ] || { echo "usage: $0 <app-folder> [...]   (apps: $(ls apps | tr '\n' ' '))" >&2; exit 2; }

API_URL="${NEXT_PUBLIC_API_URL:-$(gcloud run services describe "$API_SERVICE" --project "$PROJECT" --region "$REGION" --format='value(status.url)')}"
[ -n "$API_URL" ] || { echo "API service $API_SERVICE not found; deploy the API first" >&2; exit 1; }

deploy_web() {
  local app="$1" stage key url
  [ -d "apps/$app" ] || { echo "no such app: apps/$app" >&2; exit 2; }
  stage="$(mktemp -d)"
  trap 'rm -rf "$stage"' RETURN
  rsync -a --exclude node_modules --exclude .next --exclude '.env*' "apps/$app/" "$stage/"
  key="${NEXT_PUBLIC_MAPS_API_KEY:-$(grep -s '^NEXT_PUBLIC_MAPS_API_KEY=' "apps/$app/.env.local" | cut -d= -f2- || true)}"
  printf 'NEXT_PUBLIC_API_URL=%s\nNEXT_PUBLIC_MAPS_API_KEY=%s\n' "$API_URL" "$key" >"$stage/.env.production"
  printf 'allowBuilds:\n  sharp: false\n  unrs-resolver: false\n' >"$stage/pnpm-workspace.yaml"
  printf 'node_modules\n.next\n' >"$stage/.dockerignore"
  printf 'node_modules/\n.next/\n' >"$stage/.gcloudignore"
  cat >"$stage/Dockerfile" <<'DOCKER'
FROM node:22-slim
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm install -g pnpm@11.13.0
WORKDIR /app
COPY package.json pnpm-workspace.yaml ./
RUN pnpm install --no-frozen-lockfile
COPY . .
RUN pnpm build
ENV NODE_ENV=production PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "exec node_modules/.bin/next start -H 0.0.0.0 -p ${PORT}"]
DOCKER

  gcloud run deploy "${SLUG}-${app}" --project "$PROJECT" --region "$REGION" --quiet \
    --source "$stage" --service-account "$SERVICE_ACCOUNT" --allow-unauthenticated \
    --port 8080 --cpu 1 --memory 512Mi --min-instances 0 --max-instances 3 \
    --labels "app=${SLUG},component=${app}"
  url="$(gcloud run services describe "${SLUG}-${app}" --project "$PROJECT" --region "$REGION" --format='value(status.url)')"
  echo "${app}: ${url}  (API: ${API_URL})"
}

for app in "$@"; do deploy_web "$app"; done

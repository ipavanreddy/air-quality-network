#!/usr/bin/env bash
# Deploy services/api to Cloud Run (asia-south1). Secrets come from Secret Manager.
set -euo pipefail
: "${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT}"
cd "$(dirname "$0")/../../services/api"
gcloud run deploy air-quality-network-api \
  --source . \
  --project "$GOOGLE_CLOUD_PROJECT" \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=asia-south1 \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest,MAPS_API_KEY=maps-api-key:latest

#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${1:-evb-flyboard}"
REGION="${2:-us-central1}"

echo "Enabling Cloud Run, Cloud Build, and Artifact Registry APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

echo "Deploying ${SERVICE_NAME} to Cloud Run (${REGION})..."
gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 1 \
  --cpu 1 \
  --memory 256Mi \
  --cpu-throttling \
  --port 8080

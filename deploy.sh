#!/bin/bash

PROJECT_ID=$(gcloud config get-value project)

IMAGE_NAME="gcr.io/${PROJECT_ID}/book-agent"
SERVICE_NAME="book-agent-server"
REGION="us-west1"

echo "  Deploying MCP Server to Google Cloud Run"

echo "Building container image: ${IMAGE_NAME}..."
gcloud builds submit --tag ${IMAGE_NAME}

if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
    echo "Error: GOOGLE_MAPS_API_KEY environment variable is not set."
    echo "Please run: export GOOGLE_MAPS_API_KEY='your_key_here'"
    exit 1
fi

echo ""
echo "Deploying service: ${SERVICE_NAME}..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}

echo ""
echo "Deployment Complete."
#!/bin/sh
# Sync PDFs from S3 if S3_DATA_BUCKET is configured
if [ -n "$S3_DATA_BUCKET" ]; then
  echo "[entrypoint] Syncing PDFs from s3://${S3_DATA_BUCKET}/pdfs/ → /app/data/"
  aws s3 sync "s3://${S3_DATA_BUCKET}/pdfs/" /app/data/ \
    --region "${AWS_REGION:-ap-northeast-2}" \
    --no-progress
  echo "[entrypoint] S3 sync complete."
fi

exec uvicorn server.main:app --host 0.0.0.0 --port 8000

#!/usr/bin/env sh
# Creates the buckets the PoC needs in local MinIO. Idempotent.
# Run as a one-shot mc-init container after MinIO comes up healthy.

set -eu

ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
ACCESS_KEY="${MINIO_ROOT_USER:-vindata}"
SECRET_KEY="${MINIO_ROOT_PASSWORD:-vindatadev}"

echo "Configuring mc alias 'local' -> ${ENDPOINT}"
mc alias set local "${ENDPOINT}" "${ACCESS_KEY}" "${SECRET_KEY}"

for bucket in "${MINIO_RAW_BUCKET:-vindata-raw}" "${MINIO_CURATED_BUCKET:-vindata-curated}"; do
    if mc ls "local/${bucket}" >/dev/null 2>&1; then
        echo "Bucket ${bucket} already exists."
    else
        echo "Creating bucket ${bucket}"
        mc mb "local/${bucket}"
    fi
done

echo "MinIO bootstrap complete."

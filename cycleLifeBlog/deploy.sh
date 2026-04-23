#!/bin/bash
# Deploy cycleLifeBlog checker to AWS Lambda
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1. Install dependencies into src/ so they are bundled in the Lambda zip
pip install -r "$SCRIPT_DIR/requirements.txt" \
    -t "$SCRIPT_DIR/src/" \
    --upgrade \
    --quiet

# 2. Create build dir (Terraform archive_file writes here)
mkdir -p "$SCRIPT_DIR/build"

# 3. Terraform deploy
cd "$SCRIPT_DIR/terraform"
terraform init -upgrade
terraform apply -auto-approve \
    -var="state_bucket_name=${STATE_BUCKET_NAME:?Set STATE_BUCKET_NAME env var}"

echo "Deploy complete."

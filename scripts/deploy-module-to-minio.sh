#!/usr/bin/env bash
# Deploy Odoo module IIFE bundle to MinIO (Nekazari frontend).
# Complies with CLAUDE.md and .antigravity/devops-protocol.md:
#   - Never write to MinIO filesystem directly; use S3 API (mc).
#   - Module frontends are NOT deployed as K8s pods.
#
# Usage:
#   On server (after build): ./scripts/deploy-module-to-minio.sh
#   From local (build + scp + deploy): ./scripts/deploy-module-to-minio.sh --remote USER@HOST
#
set -euo pipefail
MODULE_ID="odoo-erp"
BUNDLE="nkz-module.js"
BUCKET_PATH="nekazari-frontend/modules/${MODULE_ID}/${BUNDLE}"

run_on_server() {
  local server="$1"
  echo "Building bundle..."
  pnpm run build:module
  echo "Copying bundle to server..."
  scp "dist/${BUNDLE}" "${server}:/tmp/${BUNDLE}"
  echo "Uploading to MinIO from server..."
  ssh "$server" "bash -s" -- << REMOTE
    set -euo pipefail
    sudo kubectl port-forward -n nekazari svc/minio-service 9000:9000 &
    PF_PID=\$!
    sleep 3
    mc alias set minio http://localhost:9000 minioadmin minioadmin
    mc cp "/tmp/${BUNDLE}" "minio/${BUCKET_PATH}"
    kill \$PF_PID 2>/dev/null || true
    echo "Done: minio/${BUCKET_PATH}"
REMOTE
}

run_local() {
  if [[ ! -f "dist/${BUNDLE}" ]]; then
    echo "Run from repo root and build first: pnpm run build:module"
    exit 1
  fi
  echo "Port-forwarding MinIO (requires sudo on server)..."
  sudo kubectl port-forward -n nekazari svc/minio-service 9000:9000 &
  PF_PID=$!
  sleep 3
  mc alias set minio http://localhost:9000 minioadmin minioadmin
  mc cp "dist/${BUNDLE}" "minio/${BUCKET_PATH}"
  kill $PF_PID 2>/dev/null || true
  echo "Done: minio/${BUCKET_PATH}"
}

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [[ "${1:-}" == "--remote" && -n "${2:-}" ]]; then
  run_on_server "$2"
else
  run_local
fi

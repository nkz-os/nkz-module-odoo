#!/usr/bin/env bash
# Add odoo-admin-password to existing odoo-secret (run on server with kubectl).
# Then update the Odoo template DB admin user to this password (one-off via Odoo UI or XML-RPC).
# Usage: ./scripts/patch-odoo-admin-secret.sh [--force]
# Author: Robotika | License: AGPL-3.0
set -euo pipefail
NAMESPACE="${NAMESPACE:-nekazari}"
SECRET_NAME="${SECRET_NAME:-odoo-secret}"
KEY_NAME="odoo-admin-password"
FORCE="${FORCE:-false}"
[[ "${1:-}" == "--force" ]] && FORCE="true"

if ! kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" &>/dev/null; then
  echo "Secret $SECRET_NAME not found in $NAMESPACE. Create it first (e.g. with master-password)."
  exit 1
fi

EXISTING=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath="{.data.${KEY_NAME}}" 2>/dev/null || true)
if [[ -n "$EXISTING" && "$FORCE" != "true" ]]; then
  echo "Key $KEY_NAME already set. Use --force to overwrite."
  exit 0
fi

NEW_PASS=$(openssl rand -base64 24)
B64=$(echo -n "$NEW_PASS" | base64 -w0 2>/dev/null || echo -n "$NEW_PASS" | base64)

kubectl patch secret "$SECRET_NAME" -n "$NAMESPACE" --type=json \
  -p="[{\"op\":\"add\",\"path\":\"/data/$KEY_NAME\",\"value\":\"$B64\"}]" 2>/dev/null || \
kubectl patch secret "$SECRET_NAME" -n "$NAMESPACE" --type=json \
  -p="[{\"op\":\"replace\",\"path\":\"/data/$KEY_NAME\",\"value\":\"$B64\"}]"

echo "Added $KEY_NAME to $SECRET_NAME. Store this password and set it for the Odoo template admin user:"
echo "$NEW_PASS"

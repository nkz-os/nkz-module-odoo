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

# Get all existing keys from the secret
EXISTING_ARGS=()
while IFS= read -r key; do
  val=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath="{.data.${key}}" 2>/dev/null || true)
  [[ -n "$val" ]] && EXISTING_ARGS+=(--from-literal="$key=$(echo "$val" | base64 -d)")
done < <(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data}' | jq -r 'keys[]' 2>/dev/null || true)

# Recreate secret with existing keys + new key using kubectl apply
kubectl create secret generic "$SECRET_NAME" -n "$NAMESPACE" \
  "${EXISTING_ARGS[@]}" \
  --from-literal="$KEY_NAME=$NEW_PASS" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Added $KEY_NAME to $SECRET_NAME. Store this password and set it for the Odoo template admin user:"
echo "$NEW_PASS"

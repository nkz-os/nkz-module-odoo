#!/bin/bash
# Nekazari Odoo 16.0 Entrypoint
#
# Handles database initialization and tenant provisioning.
#
# Author: Kate Benetis <kate@robotika.cloud>
# Company: Robotika
# License: AGPL-3.0

set -e

# Export variables for the official Odoo entrypoint
# The official entrypoint expects HOST, USER, PASSWORD (without DB_ prefix)
export HOST="${DB_HOST:-postgres-odoo-service}"
export USER="${DB_USER:-odoo}"
export PASSWORD="${DB_PASSWORD}"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h "${HOST}" -p "${DB_PORT:-5432}" -U "${USER}" -q; do
    sleep 2
done
echo "PostgreSQL is ready!"

# Check if template database exists
TEMPLATE_DB="${ODOO_TEMPLATE_DB:-nkz_odoo_template}"

if ! PGPASSWORD="${PASSWORD}" psql -h "${HOST}" -U "${USER}" -lqt | cut -d \| -f 1 | grep -qw "$TEMPLATE_DB"; then
    echo "Creating template database: $TEMPLATE_DB"

    # Create template database with base modules
    # Note: We use --db-template=template1 to avoid circular reference
    # Include auth_oauth for Keycloak SSO integration
    odoo --db_host="${HOST}" \
         --db_port="${DB_PORT:-5432}" \
         --db_user="${USER}" \
         --db_password="${PASSWORD}" \
         --db-template=template1 \
         -d "$TEMPLATE_DB" \
         -i base,web,sale,purchase,stock,account,maintenance,auth_oauth \
         --stop-after-init \
         --without-demo=all

    echo "Template database created!"

    # Try to install energy modules if available
    echo "Installing energy modules..."
    odoo --db_host="${HOST}" \
         --db_port="${DB_PORT:-5432}" \
         --db_user="${USER}" \
         --db_password="${PASSWORD}" \
         -d "$TEMPLATE_DB" \
         -i nekazari_connector \
         --stop-after-init || echo "Warning: Some modules could not be installed"

    echo "Template database initialization complete!"
else
    echo "Template database already exists: $TEMPLATE_DB"
fi

# Execute the original Odoo entrypoint
exec /entrypoint.sh "$@"

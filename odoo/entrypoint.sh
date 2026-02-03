#!/bin/bash
# Nekazari Odoo 16.0 Entrypoint
#
# Handles database initialization and tenant provisioning.
#
# Author: Kate Benetis <kate@robotika.cloud>
# Company: Robotika
# License: AGPL-3.0

set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h "${DB_HOST:-postgres-odoo-service}" -p "${DB_PORT:-5432}" -U "${DB_USER:-odoo}" -q; do
    sleep 2
done
echo "PostgreSQL is ready!"

# Check if template database exists
TEMPLATE_DB="${ODOO_TEMPLATE_DB:-nkz_odoo_template}"

if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST:-postgres-odoo-service}" -U "${DB_USER:-odoo}" -lqt | cut -d \| -f 1 | grep -qw "$TEMPLATE_DB"; then
    echo "Creating template database: $TEMPLATE_DB"

    # Create template database with base modules
    # Note: We use --db-template=template1 to avoid circular reference
    odoo --db_host="${DB_HOST:-postgres-odoo-service}" \
         --db_port="${DB_PORT:-5432}" \
         --db_user="${DB_USER:-odoo}" \
         --db_password="${DB_PASSWORD}" \
         --db-template=template1 \
         -d "$TEMPLATE_DB" \
         -i base,web,sale,purchase,stock,account,maintenance \
         --stop-after-init \
         --without-demo=all

    echo "Template database created!"

    # Try to install energy modules if available
    echo "Installing energy modules..."
    odoo --db_host="${DB_HOST:-postgres-odoo-service}" \
         --db_port="${DB_PORT:-5432}" \
         --db_user="${DB_USER:-odoo}" \
         --db_password="${DB_PASSWORD}" \
         -d "$TEMPLATE_DB" \
         -i nekazari_connector \
         --stop-after-init || echo "Warning: Some modules could not be installed"

    echo "Template database initialization complete!"
else
    echo "Template database already exists: $TEMPLATE_DB"
fi

# Execute the original Odoo entrypoint
exec /entrypoint.sh "$@"

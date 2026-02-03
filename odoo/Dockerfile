# Nekazari Odoo ERP Module - Odoo 16.0 Dockerfile
#
# Based on official Odoo 16.0 with Som Comunitats energy modules.
#
# Author: Kate Benetis <kate@robotika.cloud>
# Company: Robotika
# License: AGPL-3.0

FROM odoo:16.0

# Switch to root for installation
USER root

# Install additional system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create custom addons directory
RUN mkdir -p /mnt/extra-addons/nekazari_connector \
    && mkdir -p /mnt/extra-addons/som_comunitats

# Clone Som Comunitats energy modules from Coopdevs
# Note: These are the energy community modules from git.coopdevs.org
RUN git clone --depth 1 --branch 16.0 \
    https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce.git \
    /tmp/odoo-ce \
    && cp -r /tmp/odoo-ce/energy_* /mnt/extra-addons/som_comunitats/ \
    && rm -rf /tmp/odoo-ce \
    || echo "Warning: Could not clone Som Comunitats modules"

# Copy custom Nekazari connector module
COPY addons/nekazari_connector /mnt/extra-addons/nekazari_connector

# Copy Odoo configuration
COPY odoo.conf /etc/odoo/odoo.conf

# Copy entrypoint script
COPY entrypoint.sh /entrypoint-nkz.sh
RUN chmod +x /entrypoint-nkz.sh

# Set proper permissions
RUN chown -R odoo:odoo /mnt/extra-addons \
    && chown odoo:odoo /etc/odoo/odoo.conf

# Switch back to odoo user
USER odoo

# Expose Odoo ports
EXPOSE 8069 8071 8072

# Use custom entrypoint
ENTRYPOINT ["/entrypoint-nkz.sh"]
CMD ["odoo"]

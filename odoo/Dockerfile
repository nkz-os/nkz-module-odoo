# Nekazari Odoo ERP Module - Odoo 16.0 Dockerfile
#
# Based on official Odoo 16.0 with Som Comunitats energy modules
# and OCA dependencies.
#
# Author: Kate Benetis <kate@robotika.cloud>
# Company: Robotika
# License: AGPL-3.0

FROM odoo:16.0

USER root

# System deps for building Python packages and git for cloning repos
RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Fix broken pip in Odoo 16 base image (pyOpenSSL incompatibility)
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel pyOpenSSL

# Python deps required by energy modules
RUN pip3 install --no-cache-dir \
    pandas>=2.0.3 \
    numpy>=1.24.4 \
    openupgradelib>=3.12.0 \
    python-keycloak \
    python-jose[cryptography]

# OCA dependencies (pip installs them into odoo/addons/ in the Python path,
# which is already in addons_path via /usr/lib/python3/dist-packages/odoo/addons)
RUN pip3 install --no-cache-dir \
    odoo-addon-contract==16.0.* \
    odoo-addon-queue-job==16.0.* \
    odoo-addon-base-rest==16.0.* \
    odoo-addon-auth-api-key==16.0.* \
    odoo-addon-auth-oidc==16.0.* \
    odoo-addon-base-user-role==16.0.* \
    odoo-addon-account-banking-mandate==16.0.* \
    odoo-addon-account-payment-order==16.0.* \
    odoo-addon-web-m2x-options==16.0.* \
    odoo-addon-report-csv==16.0.* \
    odoo-addon-l10n-es-aeat==16.0.* \
    || echo "Warning: Some OCA packages may not be available on PyPI"

# Contract sub-modules (depend on base contract, install after)
RUN pip3 install --no-cache-dir \
    odoo-addon-contract-mandate==16.0.* \
    odoo-addon-contract-variable-quantity==16.0.* \
    || echo "Warning: Some contract sub-modules not available"

# /mnt/extra-addons is declared as VOLUME in the base Odoo image,
# so anything written there during build is lost at runtime.
# We use /opt/odoo/custom-addons instead.
RUN mkdir -p /opt/odoo/custom-addons && \
    git clone --depth 1 --branch 16.0 \
        https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce.git \
        /tmp/odoo-ce && \
    for mod in /tmp/odoo-ce/*/; do \
        basename="$(basename "$mod")" && \
        case "$basename" in energy_*|community_*) cp -r "$mod" /opt/odoo/custom-addons/ ;; esac; \
    done && \
    ls /opt/odoo/custom-addons/ && \
    rm -rf /tmp/odoo-ce

COPY addons/nekazari_connector /opt/odoo/custom-addons/nekazari_connector

# Odoo configuration
COPY odoo.conf /etc/odoo/odoo.conf

# Custom entrypoint
COPY entrypoint.sh /entrypoint-nkz.sh
RUN chmod +x /entrypoint-nkz.sh

# Permissions
RUN chown -R odoo:odoo /opt/odoo/custom-addons \
    && chown odoo:odoo /etc/odoo/odoo.conf

USER odoo

EXPOSE 8069 8071 8072

ENTRYPOINT ["/entrypoint-nkz.sh"]
CMD ["odoo"]

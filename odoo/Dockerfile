# Nekazari Odoo ERP Module - Odoo 16.0 Dockerfile
#
# Based on official Odoo 16.0 with Som Comunitats energy community modules
# and OCA dependencies cloned via git (PyPI packages require Python >=3.10
# but the base image ships Python 3.9).
#
# Author: Kate Benetis <kate@robotika.cloud>
# Company: Robotika
# License: AGPL-3.0

FROM odoo:16.0

USER root

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
    python-jose[cryptography] \
    python-slugify \
    pydantic

# OCA addons via git clone (PyPI requires Python >=3.10, base image has 3.9).
# We clone each OCA repo at 16.0 branch and copy all addons into a flat directory.
# /mnt/extra-addons is declared as VOLUME in the base image and gets wiped at runtime.
RUN mkdir -p /opt/odoo/oca-addons /tmp/oca && \
    cd /tmp/oca && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/contract.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/queue.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/rest-framework.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/server-auth.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/server-backend.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/server-ux.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/bank-payment.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/l10n-spain.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/multi-company.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/partner-contact.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/web.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/reporting-engine.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/social.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/connector.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/account-financial-tools.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/account-reconcile.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/account-financial-reporting.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/bank-statement-import.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/cooperative.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/mis-builder.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/community-data-ownership.git && \
    for repo in /tmp/oca/*/; do \
        for mod in "$repo"*/; do \
            [ -f "$mod/__manifest__.py" ] && cp -r "$mod" /opt/odoo/oca-addons/; \
        done; \
    done && \
    rm -rf /tmp/oca

# Coopdevs energy community modules
RUN mkdir -p /opt/odoo/custom-addons && \
    git clone --depth 1 --branch 16.0 \
        https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce.git \
        /tmp/odoo-ce && \
    for mod in /tmp/odoo-ce/*/; do \
        basename="$(basename "$mod")" && \
        case "$basename" in energy_*|community_*) cp -r "$mod" /opt/odoo/custom-addons/ ;; esac; \
    done && \
    rm -rf /tmp/odoo-ce

COPY addons/nekazari_connector /opt/odoo/custom-addons/nekazari_connector

COPY odoo.conf /etc/odoo/odoo.conf

COPY entrypoint.sh /entrypoint-nkz.sh
RUN chmod +x /entrypoint-nkz.sh

RUN chown -R odoo:odoo /opt/odoo/custom-addons /opt/odoo/oca-addons \
    && chown odoo:odoo /etc/odoo/odoo.conf

USER odoo

EXPOSE 8069 8071 8072

ENTRYPOINT ["/entrypoint-nkz.sh"]
CMD ["odoo"]

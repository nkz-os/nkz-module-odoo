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
    git build-essential libffi-dev unzip \
    && rm -rf /var/lib/apt/lists/*

# The system pip (20.3.4) is broken due to pyOpenSSL/cryptography mismatch.
# Bootstrap a fresh pip without touching system pyOpenSSL (which Odoo needs).
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3 - --no-cache-dir

# Python deps required by energy modules and OCA addons.
# CRITICAL: pin cryptography<4 to preserve compatibility with system pyOpenSSL
# (Odoo's urllib3 imports from cryptography.hazmat.backends.openssl.x509 which
# was removed in cryptography >=37).
RUN pip3 install --no-cache-dir \
    "cryptography>=3.3,<4" \
    pandas>=2.0.3 \
    numpy>=1.24.4 \
    openupgradelib>=3.12.0 \
    python-keycloak \
    python-jose \
    python-slugify==8.0.1 \
    pydantic \
    extendable \
    marshmallow \
    cachetools \
    cerberus \
    pyquerystring \
    jsondiff \
    apispec \
    parse-accept-language \
    pyjwt \
    openpyxl \
    pycountry \
    python-dateutil \
    itsdangerous \
    faker

# OCA addons via git clone (PyPI requires Python >=3.10, base image has 3.9).
# Clone each OCA repo at 16.0 branch and copy all addons (with __manifest__.py)
# to a flat directory. /mnt/extra-addons is a VOLUME and gets wiped at runtime.
RUN mkdir -p /opt/odoo/oca-addons /tmp/oca && cd /tmp/oca && \
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
    git clone --depth 1 -b 16.0 https://github.com/OCA/account-invoicing.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/sale-workflow.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/server-tools.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/account-financial-tools.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/account-reconcile.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/account-financial-reporting.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/bank-statement-import.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/cooperative.git && \
    git clone --depth 1 -b 16.0 https://github.com/OCA/mis-builder.git && \
    for repo in /tmp/oca/*/; do \
        for mod in "$repo"*/; do \
            [ -f "$mod/__manifest__.py" ] && cp -r "$mod" /opt/odoo/oca-addons/ || true; \
        done; \
    done && \
    rm -rf /tmp/oca

# Coopdevs-specific modules not in standard OCA repos.
# Download PyPI wheels (bypassing Python >=3.10 check) and extract addon dirs.
# community_maps from somitcoop GitLab (PyPI wheels have version mismatches)
RUN git clone --depth 1 -b 16.0 \
        https://gitlab.com/somitcoop/erp-research/community-maps.git \
        /tmp/cmaps && \
    for mod in /tmp/cmaps/*/; do \
        [ -f "$mod/__manifest__.py" ] && cp -r "$mod" /opt/odoo/oca-addons/ || true; \
    done && \
    rm -rf /tmp/cmaps

# Other Coopdevs-specific modules via PyPI wheels
RUN mkdir -p /tmp/wheels /tmp/extracted && \
    pip3 download --no-deps --dest /tmp/wheels \
        --python-version 3.10 --only-binary=:all: \
        odoo-addon-metadata==16.0.1.0.0 \
        odoo-addon-crm-metadata==16.0.0.1.0 \
        odoo-addon-crm-metadata-rest-api==16.0.0.1.0 \
        odoo-addon-crm-rest-api==16.0.0.1.0 \
        odoo-addon-l10n-es-cooperator==16.0.1.0.0.4 \
        odoo-addon-sale-order-metadata==16.0.0.1.0 \
    && for whl in /tmp/wheels/*.whl; do \
        unzip -o -q "$whl" "odoo/addons/*" -d /tmp/extracted; \
    done \
    && cp -r /tmp/extracted/odoo/addons/* /opt/odoo/oca-addons/ \
    && rm -rf /tmp/wheels /tmp/extracted

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

# Fix energy_communities/hooks.py: api.Environment.manage() was removed in Odoo 16
COPY patches/energy_communities_hooks.py /opt/odoo/custom-addons/energy_communities/hooks.py

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

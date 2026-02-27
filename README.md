# Nekazari Odoo ERP Module

Multitenant Odoo ERP integration for the Nekazari FIWARE platform.

## Author

**Kate Benetis** - [kate@robotika.cloud](mailto:kate@robotika.cloud)
**Company**: [Robotika](https://robotika.cloud)

## Overview

This module integrates Odoo 16.0 ERP with the Nekazari platform, providing each tenant with their own isolated Odoo instance for farm and energy community management.

### Key Features

- **Multitenant Architecture**: Each tenant gets their own Odoo database (Multi-DB with dbfilter)
- **Farm Management**: Products, parcels, harvests, inventory
- **Energy Community**: Som Comunitats modules for solar installations and self-consumption
- **NGSI-LD Sync**: Event-driven synchronization via Orion-LD subscriptions
- **N8N Integration**: Workflow automation for invoicing, alerts, and more
- **Intelligence Integration**: AI predictions synced to Odoo reports

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Nekazari Platform                        │
├─────────────────────────────────────────────────────────────┤
│  Tenant A              │  Tenant B              │  Tenant C │
│  ─────────             │  ─────────             │  ───────  │
│  DB: nkz_odoo_a        │  DB: nkz_odoo_b        │  DB: ...  │
│  URL: a.odoo.nkz...    │  URL: b.odoo.nkz...    │           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Odoo 16.0 (Single Instance)                    │
│  - Multi-DB mode with dbfilter                              │
│  - Som Comunitats energy modules                            │
│  - Nekazari Connector module                                │
└─────────────────────────────────────────────────────────────┘
```

## Module Structure

```
nkz-module-odoo/
├── manifest.json          # Module metadata for Nekazari
├── src/                   # React frontend
│   ├── App.tsx           # Main application
│   ├── components/       # UI components
│   │   └── slots/        # Unified Viewer widgets
│   ├── services/         # API client & context
│   └── slots/            # Slot registration
├── backend/              # FastAPI orchestration
│   ├── app/
│   │   ├── routers/      # API endpoints
│   │   └── services/     # Business logic
│   └── Dockerfile
├── odoo/                 # Odoo configuration
│   ├── Dockerfile        # Odoo 16.0 + Som Comunitats
│   ├── odoo.conf         # Multi-DB config
│   └── addons/
│       └── nekazari_connector/  # Custom Odoo module
├── k8s/                  # Kubernetes manifests (backend, odoo, postgres-odoo; no frontend pod)
├── src/moduleEntry.ts    # IIFE entry for host (window.__NKZ__.register)
├── vite.module.config.ts # Build config for dist/nkz-module.js
└── docker-compose.yml    # Local development
```

## Quick Start

### Local Development

```bash
# Start all services
docker-compose up -d

# Access:
# - Odoo: http://localhost:8069
# - Backend API: http://localhost:8001/docs
# - Frontend: http://localhost:5010
```

### Production Deployment

Same pattern as other Nekazari modules: **frontend = IIFE bundle in MinIO** (no frontend pod). Backend + Odoo + Postgres run in K8s.

**1. Frontend (IIFE bundle → MinIO)**

```bash
# From repo root — build and deploy to MinIO via server (CLAUDE.md / .antigravity)
./scripts/deploy-module-to-minio.sh --remote USER@HOST

# Or on the server after build:
pnpm run build:module
./scripts/deploy-module-to-minio.sh
# Manual: mc cp dist/nkz-module.js minio/nekazari-frontend/modules/odoo-erp/nkz-module.js
```

Ensure the platform DB has `remote_entry_url = '/modules/odoo-erp/nkz-module.js'` for this module (see `k8s/registration.sql`).

**2. Backend + Odoo (K8s)**

```bash
# Build and push images (no frontend image)
docker build -f backend/Dockerfile -t ghcr.io/k8-benetis/nkz-module-odoo/odoo-backend:latest ./backend
docker build -f odoo/Dockerfile -t ghcr.io/k8-benetis/nkz-module-odoo/odoo:latest ./odoo
docker push ghcr.io/k8-benetis/nkz-module-odoo/odoo-backend:latest
docker push ghcr.io/k8-benetis/nkz-module-odoo/odoo:latest

# Create secrets if not already present (CHANGE PASSWORDS!)
kubectl create secret generic odoo-secret -n nekazari --from-literal=master-password='YOUR_SECURE_PASSWORD' --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic odoo-db-secret -n nekazari --from-literal=username='odoo' --from-literal=password='YOUR_DB_PASSWORD' --dry-run=client -o yaml | kubectl apply -f -

# Deploy (configmap, postgres-odoo, odoo, backend; no frontend resources)
kubectl apply -f k8s/
```

**3. Configuration**

- Replace `YOUR_DOMAIN` in `k8s/configmap.yaml` and `k8s/ingress.yaml` with your domain (Keycloak, CORS, ODOO_URL, API/Odoo hosts). No hardcoded production URLs in the repo.

### Configuration

- **Frontend**: API base URL is relative `/api/odoo` unless overridden by host-injected config or `VITE_API_URL`.
- **Backend**: `ODOO_URL` controls "Open in Odoo" links. When empty, links are relative (`/odoo/web?db=...`). Set it (e.g. `https://odoo.YOUR_DOMAIN`) when Odoo is on a separate subdomain.
- **K8s**: Ingress hosts, ConfigMap URLs and CORS origins should match your deployment domain. See `k8s/configmap.yaml` and `k8s/ingress.yaml`.

## Integrations

### NGSI-LD Synchronization

The module uses event-driven sync via Orion-LD subscriptions:

| NGSI-LD Type | Odoo Model | Fields Synced |
|--------------|------------|---------------|
| AgriParcel | product.template | name, area, crop_type, location |
| Device | maintenance.equipment | serial_no, status, device_type |
| Building | res.partner | address, floor_area |
| EnergyMeter | energy.meter | code, meter_type, cups |
| SolarPanel | energy.installation | power_peak, orientation |

### N8N Workflows

Supported webhook events:

- `odoo.invoice.create` - Create invoice from workflow
- `odoo.order.create` - Create sales order
- `odoo.energy.log` - Log energy production data
- `sync.request` - Trigger entity sync

### Intelligence Module

AI predictions are synced to Odoo:

- Yield predictions → `x_predicted_yield` on products
- Energy forecasts → Attached to installations

## Energy Community Modules

Includes Som Comunitats modules from [Coopdevs](https://git.coopdevs.org):

- **energy_community** - Core community management
- **energy_selfconsumption** - Self-consumption projects
- **energy_import_statement** - Data import utilities

## API Documentation

When running locally with `DEBUG=true`, access:

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Environment Variables

See [env.example](./env.example) for all configuration options.

## License

AGPL-3.0 - See [LICENSE](./LICENSE)

## Credits

- **Created by**: Kate Benetis ([kate@robotika.cloud](mailto:kate@robotika.cloud))
- **Company**: Robotika ([robotika.cloud](https://robotika.cloud))
- **Som Comunitats modules**: [Coopdevs](https://coopdevs.org)
- **Odoo**: [Odoo S.A.](https://www.odoo.com)

## Support

For issues and feature requests, please use the GitHub issue tracker:
https://github.com/k8-benetis/nkz-module-odoo/issues

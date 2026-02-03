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
├── frontend/
│   ├── Dockerfile
│   └── nginx.conf
├── k8s/                  # Kubernetes manifests
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

```bash
# 1. Build images
docker build -f frontend/Dockerfile -t ghcr.io/k8-benetis/nkz-module-odoo/odoo-frontend:latest .
docker build -f backend/Dockerfile -t ghcr.io/k8-benetis/nkz-module-odoo/odoo-backend:latest ./backend
docker build -f odoo/Dockerfile -t ghcr.io/k8-benetis/nkz-module-odoo/odoo:latest ./odoo

# 2. Push to registry
docker push ghcr.io/k8-benetis/nkz-module-odoo/odoo-frontend:latest
docker push ghcr.io/k8-benetis/nkz-module-odoo/odoo-backend:latest
docker push ghcr.io/k8-benetis/nkz-module-odoo/odoo:latest

# 3. Create secrets (CHANGE PASSWORDS!)
kubectl create secret generic odoo-secret \
  --namespace=nekazari \
  --from-literal=master-password='YOUR_SECURE_PASSWORD'

kubectl create secret generic odoo-db-secret \
  --namespace=nekazari \
  --from-literal=username='odoo' \
  --from-literal=password='YOUR_DB_PASSWORD'

# 4. Deploy
kubectl apply -f k8s/
```

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

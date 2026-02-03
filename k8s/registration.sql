-- =============================================================================
-- K8s Module Registration SQL - Odoo ERP Integration
-- =============================================================================
-- Registers the Odoo ERP module in the Core Platform database
-- for Kubernetes deployment.
--
-- USAGE:
-- Execute this SQL in the Core Platform database (nekazari_core schema)
-- after deploying the module to Kubernetes.
--
-- PREREQUISITES:
-- - Module backend deployed to K8s (service: odoo-backend-service)
-- - Module frontend deployed to K8s (service: odoo-frontend-service)
-- - Odoo deployed to K8s (service: odoo-service)
-- - PostgreSQL for Odoo deployed (service: postgres-odoo-service)
-- =============================================================================

-- Insert module registration
INSERT INTO marketplace_modules (
    id,
    name,
    display_name,
    description,
    remote_entry_url,
    scope,
    exposed_module,
    version,
    author,
    category,
    icon_url,
    route_path,
    label,
    module_type,
    required_plan_type,
    pricing_tier,
    is_local,
    is_active,
    required_roles,
    metadata
) VALUES (
    'odoo-erp',                                                                  -- Module ID
    'odoo-erp',                                                                  -- Internal name
    'Odoo ERP Integration',                                                      -- Display name
    'Multitenant Odoo ERP integration for farm and energy community management. Includes Som Comunitats modules for solar installations and energy self-consumption projects.',
    'https://nekazari.artotxiki.com/modules/odoo-erp/assets/remoteEntry.js',     -- Remote entry URL (public, via ingress)
    'odoo_erp_module',                                                           -- Module Federation scope (must match vite.config.ts)
    './App',                                                                     -- Exposed module path (must match vite.config.ts)
    '1.0.0',                                                                     -- Version
    'Kate Benetis - Robotika',                                                   -- Author
    'integration',                                                               -- Category
    NULL,                                                                        -- Icon URL (optional)
    '/odoo',                                                                     -- Frontend route path
    'Odoo ERP',                                                                  -- Menu label
    'ADDON_PAID',                                                                -- Module type
    'premium',                                                                   -- Required plan type
    'PAID',                                                                      -- Pricing tier
    false,                                                                       -- Is local (external module)
    true,                                                                        -- Is active
    ARRAY['TenantAdmin', 'PlatformAdmin', 'Manager'],                           -- Required roles
    '{
        "icon": "🏢",
        "color": "#714B67",
        "shortDescription": "Multitenant Odoo ERP for farm and energy management",
        "features": [
            "Multitenant Odoo ERP (one DB per tenant)",
            "Farm management (products, parcels, harvests)",
            "Solar installation management",
            "Energy self-consumption tracking",
            "Invoicing and accounting",
            "CRM and inventory",
            "N8N workflow automation",
            "AI-powered predictions integration"
        ],
        "backend_services": ["odoo-backend-service", "odoo-service"],
        "external_dependencies": ["Odoo 16.0", "PostgreSQL"],
        "contextPanel": {
            "description": "Link Nekazari entities with Odoo records for ERP integration",
            "instructions": "Select an entity to link it with Odoo or view existing ERP data",
            "entityTypes": ["AgriParcel", "Device", "Building", "EnergyMeter"]
        },
        "integrations": {
            "n8n": ["odoo.invoice.created", "odoo.order.confirmed", "odoo.energy.production"],
            "intelligence": ["yield_prediction_to_odoo", "energy_forecast_to_odoo"],
            "ngsi_ld": ["AgriParcel", "Device", "Building", "EnergyMeter"]
        },
        "permissions": {
            "api_access": true,
            "external_requests": true,
            "storage": true
        }
    }'::jsonb
) ON CONFLICT (id) DO UPDATE SET
    version = EXCLUDED.version,
    description = EXCLUDED.description,
    remote_entry_url = EXCLUDED.remote_entry_url,
    scope = EXCLUDED.scope,
    exposed_module = EXCLUDED.exposed_module,
    route_path = EXCLUDED.route_path,
    label = EXCLUDED.label,
    module_type = EXCLUDED.module_type,
    required_plan_type = EXCLUDED.required_plan_type,
    pricing_tier = EXCLUDED.pricing_tier,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- =============================================================================
-- NOTES:
-- =============================================================================
-- 1. REMOTE_ENTRY_URL: Must be the public URL accessible through ingress
--    Format: https://nekazari.artotxiki.com/modules/{module-id}/assets/remoteEntry.js
--
-- 2. SCOPE: Must match the 'name' field in vite.config.ts federation plugin
--    Current: 'odoo_erp_module'
--
-- 3. EXPOSED_MODULE: Must match the key in vite.config.ts federation exposes
--    Current: './App'
--
-- 4. MODULE_TYPE: 
--    - 'ADDON_FREE': Free for all tenants
--    - 'ADDON_PAID': Requires subscription (monetization enabled)
--    - 'ENTERPRISE': Enterprise-only features
--
-- 5. After registration, the Core Platform will:
--    - Load the module frontend via Module Federation from remote_entry_url
--    - Display the module in the marketplace/admin panel
--
-- 6. To activate for a specific tenant:
--    INSERT INTO tenant_installed_modules (tenant_id, module_id, is_enabled)
--    VALUES ('your-tenant-id', 'odoo-erp', true)
--    ON CONFLICT (tenant_id, module_id) DO UPDATE SET is_enabled = true;
--
-- 7. ODOO-SPECIFIC:
--    - Each tenant gets their own Odoo database: nkz_odoo_{tenant_id}
--    - The backend orchestrator handles database provisioning
--    - Energy modules (Som Comunitats) installed by default
-- =============================================================================

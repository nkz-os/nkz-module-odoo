-- =============================================================================
-- Odoo 16 OAuth Provider Setup for Keycloak SSO
-- =============================================================================
-- Configures Odoo to show "Login with Nekazari" button on the login page.
-- Execute AFTER auth_oauth module is installed in the target database.
--
-- This is already applied to nkz_odoo_template — new tenant DBs cloned from
-- the template inherit this row automatically. Only run manually if the
-- provider was deleted or the template was recreated.
--
-- USAGE:
--   Replace AUTH_DOMAIN with your Keycloak host (e.g. auth.example.com).
--   psql -U odoo -d <database> -f keycloak-oauth-setup.sql
--
-- PREREQUISITES:
--   1. auth_oauth module installed (odoo -d <db> -i auth_oauth --stop-after-init)
--   2. Keycloak client "nekazari-odoo" created (see nekazari-odoo-client.json)
-- =============================================================================

INSERT INTO auth_oauth_provider (
    name, client_id, enabled, body,
    auth_endpoint, scope, validation_endpoint, data_endpoint,
    css_class, sequence, create_uid, create_date, write_uid, write_date
) VALUES (
    'Nekazari (Keycloak)',
    'nekazari-odoo',
    true,
    '{"en_US": "Login with Nekazari", "es_ES": "Iniciar sesión con Nekazari"}'::jsonb,
    'https://AUTH_DOMAIN/auth/realms/nekazari/protocol/openid-connect/auth',
    'openid email profile',
    -- validation uses userinfo (works with public clients; introspect needs client_secret)
    'https://AUTH_DOMAIN/auth/realms/nekazari/protocol/openid-connect/userinfo',
    'https://AUTH_DOMAIN/auth/realms/nekazari/protocol/openid-connect/userinfo',
    'fa fa-fw fa-sign-in text-primary',
    10, 1, NOW(), 1, NOW()
) ON CONFLICT DO NOTHING;

-- =============================================================================
-- NOTES (Odoo 16 specific):
-- =============================================================================
-- 1. Odoo 16 does NOT have a "flow" column (added in v17). Remove it if
--    migrating this SQL from a v17+ reference.
-- 2. The "body" column is jsonb — value must be a valid JSON string literal.
-- 3. validation_endpoint: we use /userinfo instead of /token/introspect because
--    introspection requires client authentication (client_id + client_secret as
--    Basic Auth). The userinfo endpoint accepts a Bearer access_token directly,
--    which is what Odoo sends in the access_token flow.
-- 4. Users logging in via OAuth are auto-created in Odoo with minimal rights.
--    To grant admin access, manually assign the "Settings" group in Odoo.
-- =============================================================================

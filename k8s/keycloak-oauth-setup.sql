-- =============================================================================
-- Odoo OAuth Provider Setup for Keycloak SSO
-- =============================================================================
-- This script configures Odoo to use Keycloak as OAuth2/OpenID Connect provider.
-- Execute this AFTER the database is created and auth_oauth module is installed.
--
-- USAGE:
-- Execute in the Odoo PostgreSQL database (postgres-odoo-service)
-- for each tenant database: nkz_odoo_{tenant_id}
--
-- PREREQUISITES:
-- 1. Create a Keycloak client for Odoo (see below)
-- 2. Have the client_id ready
-- =============================================================================

-- Insert Keycloak as OAuth Provider
INSERT INTO auth_oauth_provider (
    name,
    flow,
    client_id,
    enabled,
    body,
    auth_endpoint,
    scope,
    validation_endpoint,
    data_endpoint,
    css_class,
    sequence,
    create_uid,
    create_date,
    write_uid,
    write_date
) VALUES (
    'Nekazari (Keycloak)',                                           -- Provider name
    'access_token',                                                  -- OAuth flow
    'nekazari-odoo',                                                 -- Client ID (must match Keycloak client)
    true,                                                            -- Enabled
    'Login with Nekazari',                                           -- Button text
    'https://auth.artotxiki.com/auth/realms/nekazari/protocol/openid-connect/auth',
    'openid email profile',                                          -- Scopes
    'https://auth.artotxiki.com/auth/realms/nekazari/protocol/openid-connect/token/introspect',
    'https://auth.artotxiki.com/auth/realms/nekazari/protocol/openid-connect/userinfo',
    'fa fa-fw fa-sign-in text-primary',                              -- CSS class for button
    10,                                                              -- Sequence (order in login page)
    1,                                                               -- create_uid (admin)
    NOW(),
    1,                                                               -- write_uid
    NOW()
) ON CONFLICT DO NOTHING;

-- =============================================================================
-- KEYCLOAK CLIENT CONFIGURATION
-- =============================================================================
-- Create a client in Keycloak with these settings:
--
-- Client ID: nekazari-odoo
-- Client Protocol: openid-connect
-- Access Type: confidential (or public for simpler setup)
-- Valid Redirect URIs:
--   - https://odoo.nkz.artotxiki.com/*
--   - https://nekazari.artotxiki.com/modules/odoo-erp/*
-- Web Origins:
--   - https://odoo.nkz.artotxiki.com
--   - https://nekazari.artotxiki.com
--
-- Mappers (add these to include user info in token):
-- 1. email -> claim name: email
-- 2. given name -> claim name: name (or create full name mapper)
--
-- =============================================================================
-- NOTES:
-- =============================================================================
-- 1. The client_id must match exactly what's configured in Keycloak
-- 2. For production, use 'access_token_api' flow with client secret
-- 3. Users logging in via OAuth will be auto-created in Odoo
-- 4. To link existing users: match by email
-- =============================================================================

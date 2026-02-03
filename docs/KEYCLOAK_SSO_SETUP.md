# Keycloak SSO Setup for Odoo

This document describes how to configure Single Sign-On (SSO) between Keycloak and Odoo.

## Prerequisites

- Odoo module deployed and running
- Keycloak configured with `nekazari` realm
- Tenant provisioned with Odoo database

## Step 1: Create Keycloak Client for Odoo

1. Access Keycloak Admin Console: `https://auth.artotxiki.com/auth/admin/`
2. Select realm: `nekazari`
3. Go to **Clients** → **Create client**
4. Configure:

```
Client ID: nekazari-odoo
Client Protocol: openid-connect
Client Authentication: ON (confidential)
Valid Redirect URIs:
  - https://odoo.nkz.artotxiki.com/*
  - https://nekazari.artotxiki.com/modules/odoo-erp/*
Web Origins:
  - https://odoo.nkz.artotxiki.com
  - https://nekazari.artotxiki.com
```

5. Go to **Credentials** tab and copy the **Client Secret**

## Step 2: Configure OAuth Provider in Odoo

### Option A: Via Odoo UI

1. Access Odoo Admin: `https://odoo.nkz.artotxiki.com/web`
2. Login as admin
3. Go to **Settings** → **General Settings** → **Integrations**
4. Enable **OAuth Authentication**
5. Go to **Settings** → **Users & Companies** → **OAuth Providers**
6. Create new provider:

```
Provider Name: Nekazari (Keycloak)
Client ID: nekazari-odoo
Allowed: Yes
Login Button Label: Login with Nekazari
Authorization URL: https://auth.artotxiki.com/auth/realms/nekazari/protocol/openid-connect/auth
Scope: openid email profile
Validation URL: https://auth.artotxiki.com/auth/realms/nekazari/protocol/openid-connect/token/introspect
Data URL: https://auth.artotxiki.com/auth/realms/nekazari/protocol/openid-connect/userinfo
```

### Option B: Via SQL

Execute in each tenant's Odoo database:

```sql
INSERT INTO auth_oauth_provider (
    name, flow, client_id, enabled, body,
    auth_endpoint, scope, validation_endpoint, data_endpoint,
    css_class, sequence, create_uid, create_date, write_uid, write_date
) VALUES (
    'Nekazari (Keycloak)',
    'access_token',
    'nekazari-odoo',
    true,
    'Login with Nekazari',
    'https://auth.artotxiki.com/auth/realms/nekazari/protocol/openid-connect/auth',
    'openid email profile',
    'https://auth.artotxiki.com/auth/realms/nekazari/protocol/openid-connect/token/introspect',
    'https://auth.artotxiki.com/auth/realms/nekazari/protocol/openid-connect/userinfo',
    'fa fa-fw fa-sign-in text-primary',
    10, 1, NOW(), 1, NOW()
) ON CONFLICT DO NOTHING;
```

## Step 3: Provision Tenant with Odoo

For the Platform Admin tenant:

```bash
# Via API
curl -X POST https://nkz.artotxiki.com/api/odoo/tenant/provision \
  -H "Authorization: Bearer <KEYCLOAK_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"enableEnergyModules": true}'
```

Or use the Nekazari UI to activate the Odoo module for the tenant.

## Step 4: Link Users

Users logging in via OAuth for the first time will be auto-created in Odoo.
To link existing Odoo users with Keycloak accounts:

1. Ensure the email addresses match
2. User logs in via "Login with Nekazari" button
3. Odoo matches by email and links the accounts

## Automatic Login Flow

Once configured:

1. User logs into Nekazari via Keycloak
2. User navigates to Odoo module
3. Odoo iframe loads with OAuth login
4. User clicks "Login with Nekazari"
5. Since user is already authenticated with Keycloak, automatic redirect happens
6. User is logged into Odoo

## Troubleshooting

### OAuth Provider not visible
- Ensure `auth_oauth` module is installed: Settings → Apps → Search "auth_oauth" → Install

### Token validation fails
- Check Keycloak client credentials
- Verify redirect URIs are correct
- Check CORS settings in Keycloak

### User not found
- Verify email matches between Keycloak and Odoo
- Check that OAuth provider is enabled

## Security Notes

- Never expose client secrets in frontend code
- Use HTTPS for all OAuth endpoints
- Regularly rotate Keycloak client secrets

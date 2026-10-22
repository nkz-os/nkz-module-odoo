# Keycloak SSO Setup for Odoo

Single Sign-On between Keycloak and Odoo. Users logged into Nekazari access Odoo
without a second login.

## Prerequisites

- Odoo module deployed and running
- Keycloak configured with `nekazari` realm
- `KEYCLOAK_PUBLIC_URL` and `ODOO_OAUTH_CLIENT_ID` set in ConfigMap

## Step 1: Create Keycloak Client for Odoo

1. Access Keycloak Admin Console: `https://auth.YOUR_DOMAIN/auth/admin/`
2. Select realm: `nekazari`
3. Go to **Clients** → **Create client**
4. Configure:

```
Client ID: nekazari-odoo
Client Protocol: openid-connect
Client Authentication: ON (confidential)
Implicit Flow: ENABLED (required for Odoo 16 auth_oauth)
Valid Redirect URIs:
  - https://odoo.YOUR_DOMAIN/*
Web Origins:
  - https://odoo.YOUR_DOMAIN
  - https://frontend.YOUR_DOMAIN
```

5. Go to **Credentials** tab and copy the **Client Secret** (needed if using authorization code flow in future)

## Step 2: Deploy with Configuration

Replace `YOUR_DOMAIN` in `k8s/configmap.yaml`:

```yaml
KEYCLOAK_PUBLIC_URL: "https://auth.YOUR_DOMAIN/auth"
ODOO_OAUTH_CLIENT_ID: "nekazari-odoo"
ODOO_URL: "https://odoo.YOUR_DOMAIN"
```

Replace `YOUR_DOMAIN` in `k8s/ingress.yaml` for both API and Odoo direct ingresses.

## Step 3: Automatic OAuth Configuration

When a tenant provisions Odoo (`POST /api/odoo/tenant/provision`), the backend
**automatically** creates the Keycloak OAuth provider in the tenant's Odoo database
via XML-RPC. No manual setup per tenant is needed.

The provisioning response includes `odooLoginUrl` — a direct SSO URL that skips the
Odoo login page entirely.

## SSO Flow

1. User logs into Nekazari via Keycloak
2. User navigates to Odoo module in Nekazari
3. Clicks "Open Odoo ERP" → browser navigates to `odooLoginUrl`
4. Odoo redirects to Keycloak → user already has session → auto-redirect back
5. Odoo creates/matches user by email → user is logged in

## User Matching

Users are matched by email address. The `auth_oauth_nekazari_fix` addon overrides
Odoo's signup to use email as login (not UUID), ensuring consistent matching.

## Troubleshooting

### OAuth Provider not visible in Odoo
- Ensure `auth_oauth` module is installed: Settings → Apps → Search "auth_oauth"
- Check backend logs for "OAuth provider setup failed"

### Token validation fails
- Verify Keycloak client has Implicit Flow enabled
- Check redirect URIs match exactly (including trailing slash)
- Check CORS settings in Keycloak

### User not created/matched
- Verify email in Keycloak matches Odoo (case-sensitive)
- Check that `auth_oauth_nekazari_fix` addon is installed

### SSO URL missing (odooLoginUrl is null)
- Verify `KEYCLOAK_PUBLIC_URL` is set in ConfigMap (not empty)
- Check that `ODOO_URL` is set (SSO requires an absolute URL)
- Re-provision or restart backend to retry OAuth provider creation

## Security Notes

- Client secrets are not needed on the Odoo side for implicit flow
- Use HTTPS for all OAuth endpoints
- The `list_db = True` setting in `odoo.conf` is restricted by blocking `/web/database/manager` in the ingress

# Odoo Module — Deploy Plan (4 steps, strict order)

Run on the server. Replace `YOUR_DOMAIN` with your actual domain where needed. No secrets or sensitive values in this doc.

## Paso 1: Resolución del Ingress (platform)

Remove the odoo host from the platform ingress so only the module's `odoo-direct-ingress` serves Odoo.

```bash
cd ~/nkz
git pull
chmod +x scripts/remove-odoo-from-platform-ingress.sh
sudo ./scripts/remove-odoo-from-platform-ingress.sh
```

Verify: `sudo kubectl get ingress nekazari-ingress -n nekazari -o yaml | grep -A2 odoo` should show nothing.

## Paso 2: dbfilter (Odoo server config)

```bash
cd ~/nkz-module-odoo
git pull
sudo kubectl apply -f k8s/odoo-server-config.yaml
sudo kubectl apply -f k8s/odoo-deployment.yaml
sudo kubectl rollout status deployment/odoo -n nekazari
```

## Paso 3: Bloqueo Database Manager + secret admin

3a) Apply 403 responder and updated ingress:

```bash
sudo kubectl apply -f k8s/odoo-forbidden-responder.yaml
# If ingress uses odoo.YOUR_DOMAIN, replace with your host then:
sudo kubectl apply -f k8s/ingress.yaml
```

3b) Add `odoo-admin-password` to `odoo-secret` (run once). Then set the same password for the Odoo template DB admin user.

```bash
chmod +x scripts/patch-odoo-admin-secret.sh
./scripts/patch-odoo-admin-secret.sh
```

3c) Rebuild backend image, then on server: `sudo kubectl apply -f k8s/backend-deployment.yaml` and `sudo kubectl rollout restart deployment/odoo-backend -n nekazari`.

## Paso 4: Estado

CURRENT_STATE.md updated in repos. No server action.

## Verification

- `/web?db=nkz_odoo_<tenant>` → Odoo login (no DB creation form).
- `/web/database/manager` and `/web/database/selector` → 403.
- Platform ingress has no rule for odoo subdomain.

"""
Nekazari Odoo ERP Module - Lifecycle Webhook Router

Handles module activation/deactivation events from entity-manager.
Called automatically when a tenant toggles the Odoo module.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

import hmac
import hashlib
import json
import logging
import os
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.services.odoo_client import OdooClient
from app.services.database import get_tenant_odoo_info, save_tenant_odoo_info

logger = logging.getLogger(__name__)
router = APIRouter()

LIFECYCLE_SECRET = os.environ.get("LIFECYCLE_WEBHOOK_SECRET", "")


class LifecycleEvent(BaseModel):
    event: str
    tenant_id: str
    module_id: str
    user_email: Optional[str] = None
    timestamp: Optional[str] = None


def _verify_hmac(body: bytes, signature_header: Optional[str]) -> bool:
    """Verify HMAC-SHA256 signature from entity-manager."""
    if not LIFECYCLE_SECRET:
        logger.warning("LIFECYCLE_WEBHOOK_SECRET not set — skipping signature check")
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        LIFECYCLE_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    received = signature_header[len("sha256="):]
    return hmac.compare_digest(expected, received)


@router.post("/internal/lifecycle")
async def handle_lifecycle(request: Request):
    """
    Handle module lifecycle events from entity-manager.

    - module.enabled  -> provision or reactivate tenant DB
    - module.disabled -> mark tenant DB as inactive (preserve data)
    """
    body = await request.body()
    sig = request.headers.get("X-Nekazari-Signature")

    if not _verify_hmac(body, sig):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        event = LifecycleEvent(**json.loads(body))
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed payload")

    logger.info(f"[lifecycle] event={event.event} tenant={event.tenant_id}")

    if event.event == "module.enabled":
        return await _handle_enable(event)
    elif event.event == "module.disabled":
        return await _handle_disable(event)
    else:
        return {"status": "ignored", "reason": f"Unknown event: {event.event}"}


async def _handle_enable(event: LifecycleEvent) -> dict:
    """Provision or reactivate a tenant's Odoo database."""
    tenant_id = event.tenant_id
    db_name = f"nkz_odoo_{tenant_id}"

    existing = await get_tenant_odoo_info(tenant_id)

    if existing:
        current_status = existing.get("status")

        if current_status == "active":
            logger.info(f"[lifecycle] Tenant {tenant_id} already active — noop")
            return {"status": "already_active", "database": db_name}

        if current_status == "inactive":
            logger.info(f"[lifecycle] Reactivating tenant {tenant_id}")
            await save_tenant_odoo_info(tenant_id, {
                "status": "active",
                "database": existing.get("database") or db_name,
            })
            return {"status": "reactivated", "database": db_name}

        if current_status == "provisioning":
            logger.info(f"[lifecycle] Tenant {tenant_id} already provisioning — noop")
            return {"status": "provisioning", "database": db_name}

    # First-time provisioning
    logger.info(f"[lifecycle] Provisioning new Odoo DB for tenant {tenant_id}")
    await save_tenant_odoo_info(tenant_id, {
        "status": "provisioning",
        "database": db_name,
        "name": tenant_id,
    })

    try:
        odoo = OdooClient()

        # Duplicate template (skip if DB already exists from a previous partial attempt)
        if await odoo.database_exists(db_name):
            logger.info(f"[lifecycle] DB {db_name} already exists — skipping clone")
        else:
            await odoo.duplicate_database(
                source_db=settings.ODOO_TEMPLATE_DB,
                target_db=db_name,
            )

        # Energy modules are pre-installed in the template; install extras if needed
        energy_modules = [
            "energy_communities",
            "energy_selfconsumption",
        ]
        try:
            await odoo.install_modules(db_name, energy_modules)
        except Exception as mod_err:
            logger.warning(f"[lifecycle] Non-fatal: could not install energy extras: {mod_err}")

        # Create admin user for tenant (from the Keycloak email)
        admin_email = event.user_email or f"admin@{tenant_id}.nkz"
        try:
            await odoo.create_user(
                db_name=db_name,
                email=admin_email,
                name=event.user_email or tenant_id,
                is_admin=True,
            )
        except Exception as usr_err:
            logger.warning(f"[lifecycle] Non-fatal: could not create admin user: {usr_err}")

        await save_tenant_odoo_info(tenant_id, {
            "name": tenant_id,
            "database": db_name,
            "status": "active",
            "energy_modules_enabled": True,
            "installed_modules": energy_modules,
            "admin_email": admin_email,
            "created_at": datetime.utcnow(),
        })

        # Register NGSI-LD subscriptions
        try:
            from app.services.ngsi_sync import register_tenant_subscriptions
            await register_tenant_subscriptions(tenant_id)
        except Exception as sub_err:
            logger.warning(f"[lifecycle] Non-fatal: NGSI-LD subscriptions failed: {sub_err}")

        logger.info(f"[lifecycle] Provisioned {db_name} for tenant {tenant_id}")
        return {"status": "provisioned", "database": db_name}

    except Exception as exc:
        logger.error(f"[lifecycle] Provisioning failed for {tenant_id}: {exc}")
        await save_tenant_odoo_info(tenant_id, {
            "status": "error",
            "database": db_name,
            "error": str(exc),
        })
        raise HTTPException(status_code=500, detail=f"Provisioning failed: {exc}")


async def _handle_disable(event: LifecycleEvent) -> dict:
    """Mark a tenant's Odoo database as inactive (never delete)."""
    tenant_id = event.tenant_id
    existing = await get_tenant_odoo_info(tenant_id)

    if not existing:
        logger.info(f"[lifecycle] No Odoo DB for tenant {tenant_id} — nothing to disable")
        return {"status": "not_found"}

    db_name = existing.get("database") or f"nkz_odoo_{tenant_id}"
    logger.info(f"[lifecycle] Deactivating tenant {tenant_id} (DB {db_name} preserved)")

    await save_tenant_odoo_info(tenant_id, {
        "status": "inactive",
        "database": db_name,
    })

    return {"status": "deactivated", "database": db_name}

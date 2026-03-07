"""
Nekazari Odoo ERP Module - Tenant Management Router

Handles provisioning and management of tenant-specific Odoo databases.
Uses Multi-DB architecture: one Odoo database per tenant.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.config import settings
from app.middleware.auth import get_current_tenant, get_current_user
from app.services.odoo_client import OdooClient
from app.services.database import get_tenant_odoo_info, save_tenant_odoo_info

logger = logging.getLogger(__name__)
router = APIRouter()


class TenantOdooInfo(BaseModel):
    """Tenant Odoo information model."""
    id: str
    name: str
    odooDatabase: str
    odooUrl: str
    odooLoginUrl: Optional[str] = None  # Direct SSO login URL (skips Odoo login page)
    status: str  # active, provisioning, error
    lastSync: Optional[str] = None
    energyModulesEnabled: bool = False
    installedModules: list[str] = []


class ProvisionRequest(BaseModel):
    """Request to provision Odoo for a tenant."""
    enableEnergyModules: bool = True
    additionalModules: list[str] = []


@router.get("/info", response_model=TenantOdooInfo)
async def get_tenant_info(
    response: Response,
    tenant_id: str = Depends(get_current_tenant),
    user: dict = Depends(get_current_user)
):
    """
    Get Odoo information for the current tenant.

    Returns the Odoo database name, URL, status, and installed modules.
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    logger.info(f"Getting Odoo info for tenant: {tenant_id}")

    try:
        info = await get_tenant_odoo_info(tenant_id)

        if not info:
            raise HTTPException(status_code=404, detail="Odoo not provisioned for this tenant")

        # Build direct SSO login URL if OAuth is configured
        login_url = await _build_sso_login_url(tenant_id, info)

        return TenantOdooInfo(
            id=tenant_id,
            name=info.get("name") or tenant_id,
            odooDatabase=info.get("database") or f"nkz_odoo_{tenant_id}",
            odooUrl=_build_tenant_odoo_url(tenant_id),
            odooLoginUrl=login_url,
            status=info.get("status") or "unknown",
            lastSync=info.get("last_sync"),
            energyModulesEnabled=info.get("energy_modules_enabled") or False,
            installedModules=info.get("installed_modules") or []
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tenant info")


@router.post("/provision", response_model=TenantOdooInfo)
async def provision_tenant(
    request: ProvisionRequest = ProvisionRequest(),
    tenant_id: str = Depends(get_current_tenant),
    user: dict = Depends(get_current_user)
):
    """
    Provision a new Odoo database for the tenant.

    Creates a new PostgreSQL database from the template and installs
    required modules including energy community modules if requested.
    """
    logger.info(f"Provisioning Odoo for tenant: {tenant_id}")

    # Check if already exists
    existing = await get_tenant_odoo_info(tenant_id)
    if existing and existing.get("status") == "active":
        raise HTTPException(status_code=409, detail="Odoo already provisioned for this tenant")

    try:
        # Mark as provisioning
        await save_tenant_odoo_info(tenant_id, {
            "status": "provisioning",
            "started_at": datetime.utcnow().isoformat()
        })

        # Create database using Odoo client
        odoo_client = OdooClient()
        db_name = f"nkz_odoo_{tenant_id}"

        # Duplicate from template
        await odoo_client.duplicate_database(
            source_db=settings.ODOO_TEMPLATE_DB,
            target_db=db_name
        )

        # Install modules
        modules_to_install = ["base", "sale", "purchase", "stock", "account"]

        if request.enableEnergyModules:
            modules_to_install.extend([
                "energy_community",
                "energy_selfconsumption",
                "energy_import_statement"
            ])

        modules_to_install.extend(request.additionalModules)

        await odoo_client.install_modules(db_name, modules_to_install)

        # Create admin user for tenant
        admin_email = user.get("email", f"admin@{tenant_id}.nkz")
        await odoo_client.create_user(
            db_name=db_name,
            email=admin_email,
            name=user.get("name", "Admin"),
            is_admin=True
        )

        # Configure Keycloak OAuth SSO provider
        oauth_provider_id = None
        if settings.KEYCLOAK_PUBLIC_URL and settings.ODOO_OAUTH_CLIENT_ID:
            try:
                oauth_provider_id = await odoo_client.configure_oauth_provider(
                    db_name=db_name,
                    keycloak_public_url=settings.KEYCLOAK_PUBLIC_URL,
                    realm=settings.KEYCLOAK_REALM,
                    client_id=settings.ODOO_OAUTH_CLIENT_ID,
                )
            except Exception as oauth_err:
                logger.warning(f"OAuth provider setup failed (non-fatal): {oauth_err}")

        # Register NGSI-LD subscriptions for this tenant
        from app.services.ngsi_sync import register_tenant_subscriptions
        await register_tenant_subscriptions(tenant_id)

        logger.info(f"Successfully provisioned Odoo for tenant: {tenant_id}")

        # Save tenant info including OAuth provider ID
        await save_tenant_odoo_info(tenant_id, {
            "name": tenant_id,
            "database": db_name,
            "status": "active",
            "energy_modules_enabled": request.enableEnergyModules,
            "installed_modules": modules_to_install,
            "created_at": datetime.utcnow().isoformat(),
            "admin_email": admin_email,
            "oauth_provider_id": oauth_provider_id,
        })

        login_url = _build_sso_login_url_sync(tenant_id, oauth_provider_id)

        return TenantOdooInfo(
            id=tenant_id,
            name=tenant_id,
            odooDatabase=db_name,
            odooUrl=_build_tenant_odoo_url(tenant_id),
            odooLoginUrl=login_url,
            status="active",
            lastSync=None,
            energyModulesEnabled=request.enableEnergyModules,
            installedModules=modules_to_install
        )

    except Exception as e:
        logger.error(f"Failed to provision Odoo for tenant {tenant_id}: {e}")

        # Mark as error
        await save_tenant_odoo_info(tenant_id, {
            "status": "error",
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        })

        raise HTTPException(status_code=500, detail=f"Failed to provision Odoo: {str(e)}")


@router.delete("/delete")
async def delete_tenant_odoo(
    tenant_id: str = Depends(get_current_tenant),
    user: dict = Depends(get_current_user)
):
    """
    Delete Odoo database for the tenant.

    WARNING: This permanently deletes all tenant data in Odoo.
    """
    logger.warning(f"Deleting Odoo for tenant: {tenant_id} by user: {user.get('email')}")

    try:
        info = await get_tenant_odoo_info(tenant_id)
        if not info:
            raise HTTPException(status_code=404, detail="Odoo not found for this tenant")

        db_name = info.get("database", f"nkz_odoo_{tenant_id}")

        # Delete database
        odoo_client = OdooClient()
        await odoo_client.delete_database(db_name)

        # Remove from our records
        await save_tenant_odoo_info(tenant_id, None)

        # Remove NGSI-LD subscriptions
        from app.services.ngsi_sync import remove_tenant_subscriptions
        await remove_tenant_subscriptions(tenant_id)

        logger.info(f"Successfully deleted Odoo for tenant: {tenant_id}")

        return {"status": "deleted", "tenant_id": tenant_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete Odoo for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete Odoo: {str(e)}")


def _build_tenant_odoo_url(tenant_id: str) -> str:
    """Build the Odoo web URL for a tenant."""
    db_name = f"nkz_odoo_{tenant_id}"
    base = (settings.ODOO_URL or "").strip().rstrip("/")
    if not base:
        return f"/web?db={db_name}"
    return f"{base}/web?db={db_name}"


def _build_sso_login_url_sync(
    tenant_id: str,
    oauth_provider_id: Optional[int],
) -> Optional[str]:
    """Build the direct SSO login URL (skips Odoo login page)."""
    if not oauth_provider_id:
        return None
    db_name = f"nkz_odoo_{tenant_id}"
    base = (settings.ODOO_URL or "").strip().rstrip("/")
    if not base:
        return None
    return f"{base}/auth_oauth/signin?p={oauth_provider_id}&d={db_name}&redirect=%2Fweb"


async def _build_sso_login_url(
    tenant_id: str,
    info: dict,
) -> Optional[str]:
    """Build SSO login URL from stored tenant info, fetching provider ID if needed."""
    provider_id = info.get("oauth_provider_id")

    # If not stored, try to look it up from Odoo
    if not provider_id and settings.KEYCLOAK_PUBLIC_URL:
        try:
            db_name = info.get("database") or f"nkz_odoo_{tenant_id}"
            odoo_client = OdooClient()
            provider_id = await odoo_client.get_oauth_provider_id(
                db_name, settings.ODOO_OAUTH_CLIENT_ID
            )
            if provider_id:
                # Cache it for next time
                await save_tenant_odoo_info(tenant_id, {
                    **info,
                    "oauth_provider_id": provider_id,
                })
        except Exception as e:
            logger.warning(f"Could not fetch OAuth provider ID: {e}")

    return _build_sso_login_url_sync(tenant_id, provider_id)

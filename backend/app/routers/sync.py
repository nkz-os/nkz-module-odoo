"""
Nekazari Odoo ERP Module - Synchronization Router

Handles entity synchronization between NGSI-LD and Odoo.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.middleware.auth import get_current_tenant, get_current_user
from app.services.ngsi_sync import NgsildSyncService
from app.services.database import (
    get_entity_mappings,
    get_entity_mapping_by_ngsi_id,
    create_entity_mapping,
    get_sync_status as db_get_sync_status,
    update_sync_status
)

logger = logging.getLogger(__name__)
router = APIRouter()


class SyncResult(BaseModel):
    """Result of a sync operation."""
    success: bool
    entitiesSynced: int
    errors: list[str]
    timestamp: str


class SyncStatus(BaseModel):
    """Current sync status."""
    status: str
    lastSync: Optional[str] = None


class OdooEntity(BaseModel):
    """Mapped Odoo entity."""
    odooId: int
    odooModel: str
    odooName: str
    ngsiLdId: str
    ngsiLdType: str
    lastSync: str


class CreateFromNgsiRequest(BaseModel):
    """Request to create Odoo entity from NGSI-LD."""
    ngsiLdId: str
    ngsiLdType: str


@router.post("/trigger", response_model=SyncResult)
async def trigger_sync(
    tenant_id: str = Depends(get_current_tenant),
    user: dict = Depends(get_current_user)
):
    """
    Trigger full synchronization between NGSI-LD and Odoo.

    This will:
    1. Fetch all subscribed entities from Orion-LD
    2. Upsert corresponding records in Odoo
    3. Update sync mappings in database
    """
    logger.info(f"Triggering sync for tenant: {tenant_id}")

    try:
        sync_service = NgsildSyncService(tenant_id)
        result = await sync_service.full_sync()

        await update_sync_status(tenant_id, {
            "status": "synced",
            "last_sync": datetime.utcnow().isoformat(),
            "entities_synced": result["synced"],
            "errors": result["errors"]
        })

        return SyncResult(
            success=len(result["errors"]) == 0,
            entitiesSynced=result["synced"],
            errors=result["errors"],
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Sync failed for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/status", response_model=SyncStatus)
async def get_sync_status(
    tenant_id: str = Depends(get_current_tenant)
):
    """Get current sync status for the tenant."""
    try:
        status = await db_get_sync_status(tenant_id)

        return SyncStatus(
            status=status.get("status", "unknown") if status else "never_synced",
            lastSync=status.get("last_sync") if status else None
        )

    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sync status")


@router.get("/mappings", response_model=list[OdooEntity])
async def get_mappings(
    type: Optional[str] = None,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Get entity mappings between NGSI-LD and Odoo.

    Optionally filter by NGSI-LD entity type.
    """
    try:
        mappings = await get_entity_mappings(tenant_id, ngsi_type=type)

        return [
            OdooEntity(
                odooId=m["odoo_id"],
                odooModel=m["odoo_model"],
                odooName=m["odoo_name"],
                ngsiLdId=m["ngsi_id"],
                ngsiLdType=m["ngsi_type"],
                lastSync=m["last_sync"]
            )
            for m in mappings
        ]

    except Exception as e:
        logger.error(f"Failed to get mappings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mappings")


@router.get("/entity/by-ngsi/{ngsi_id}", response_model=Optional[OdooEntity])
async def get_entity_by_ngsi_id(
    ngsi_id: str,
    tenant_id: str = Depends(get_current_tenant)
):
    """Get Odoo entity mapping by NGSI-LD ID."""
    try:
        mapping = await get_entity_mapping_by_ngsi_id(tenant_id, ngsi_id)

        if not mapping:
            return None

        return OdooEntity(
            odooId=mapping["odoo_id"],
            odooModel=mapping["odoo_model"],
            odooName=mapping["odoo_name"],
            ngsiLdId=mapping["ngsi_id"],
            ngsiLdType=mapping["ngsi_type"],
            lastSync=mapping["last_sync"]
        )

    except Exception as e:
        logger.error(f"Failed to get entity mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to get entity mapping")


@router.post("/entity/create-from-ngsi", response_model=OdooEntity)
async def create_entity_from_ngsi(
    request: CreateFromNgsiRequest,
    tenant_id: str = Depends(get_current_tenant),
    user: dict = Depends(get_current_user)
):
    """
    Create an Odoo entity from an NGSI-LD entity.

    Fetches the entity from Orion-LD and creates the corresponding
    record in Odoo.
    """
    logger.info(f"Creating Odoo entity from NGSI-LD: {request.ngsiLdId}")

    try:
        sync_service = NgsildSyncService(tenant_id)

        # Fetch entity from Orion-LD
        entity = await sync_service.fetch_entity(request.ngsiLdId)

        if not entity:
            raise HTTPException(status_code=404, detail="NGSI-LD entity not found")

        # Create in Odoo
        odoo_entity = await sync_service.sync_entity_to_odoo(entity)

        # Save mapping
        await create_entity_mapping(tenant_id, {
            "ngsi_id": request.ngsiLdId,
            "ngsi_type": request.ngsiLdType,
            "odoo_id": odoo_entity["id"],
            "odoo_model": odoo_entity["model"],
            "odoo_name": odoo_entity["name"],
            "last_sync": datetime.utcnow().isoformat()
        })

        return OdooEntity(
            odooId=odoo_entity["id"],
            odooModel=odoo_entity["model"],
            odooName=odoo_entity["name"],
            ngsiLdId=request.ngsiLdId,
            ngsiLdType=request.ngsiLdType,
            lastSync=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create Odoo entity: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create entity: {str(e)}")


@router.get("/entity/open/{odoo_model}/{odoo_id}")
async def get_odoo_entity_url(
    odoo_model: str,
    odoo_id: int,
    tenant_id: str = Depends(get_current_tenant)
):
    """Get URL to open an Odoo entity in the web interface."""
    # Build Odoo URL with action to open the record
    base_url = f"https://{tenant_id}.odoo.nkz.artotxiki.com"
    model_to_action = {
        "product.template": "product.product_template_action",
        "maintenance.equipment": "maintenance.hr_equipment_action",
        "res.partner": "base.action_partner_form",
        "energy.installation": "energy_community.action_energy_installation",
        "energy.meter": "energy_community.action_energy_meter"
    }

    action = model_to_action.get(odoo_model, "")

    return {
        "url": f"{base_url}/web#id={odoo_id}&model={odoo_model}&action={action}&view_type=form"
    }

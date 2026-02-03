"""
Nekazari Odoo ERP Module - Webhook Router

Handles incoming webhooks from NGSI-LD subscriptions and N8N.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

import logging
import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

from app.config import settings
from app.services.ngsi_sync import NgsildSyncService
from app.services.n8n_integration import N8NIntegration

logger = logging.getLogger(__name__)
router = APIRouter()


class NGSILDNotification(BaseModel):
    """NGSI-LD subscription notification format."""
    id: str
    type: str = "Notification"
    subscriptionId: str
    notifiedAt: str
    data: list[dict[str, Any]]


class N8NWebhookPayload(BaseModel):
    """N8N webhook payload format."""
    workflow_id: str
    execution_id: str
    event: str
    data: dict[str, Any]
    tenant_id: str


@router.post("/ngsi")
async def handle_ngsi_notification(
    notification: NGSILDNotification,
    request: Request
):
    """
    Handle NGSI-LD subscription notifications.

    This endpoint receives real-time notifications when subscribed
    entities are created, updated, or deleted in Orion-LD.

    The notification contains:
    - subscriptionId: ID of the subscription that triggered this
    - data: Array of entities that changed

    Flow:
    1. Parse notification
    2. Extract tenant ID from subscription metadata
    3. Sync each entity to Odoo
    """
    logger.info(f"Received NGSI-LD notification: {notification.id}")
    logger.debug(f"Subscription: {notification.subscriptionId}, Entities: {len(notification.data)}")

    try:
        # Extract tenant ID from subscription ID (format: nkz-odoo-{tenant_id}-{entity_type})
        # Or look it up from our subscription registry
        tenant_id = _extract_tenant_from_subscription(notification.subscriptionId)

        if not tenant_id:
            logger.warning(f"Could not determine tenant for subscription: {notification.subscriptionId}")
            return {"status": "ignored", "reason": "unknown_subscription"}

        sync_service = NgsildSyncService(tenant_id)

        synced = 0
        errors = []

        for entity in notification.data:
            try:
                entity_id = entity.get("id")
                entity_type = entity.get("type")

                logger.info(f"Syncing entity {entity_id} ({entity_type}) for tenant {tenant_id}")

                await sync_service.sync_entity_to_odoo(entity)
                synced += 1

            except Exception as e:
                error_msg = f"Failed to sync {entity.get('id')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        logger.info(f"NGSI-LD notification processed: {synced} synced, {len(errors)} errors")

        return {
            "status": "processed",
            "synced": synced,
            "errors": len(errors),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to process NGSI-LD notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process notification: {str(e)}")


@router.post("/n8n")
async def handle_n8n_webhook(
    payload: N8NWebhookPayload,
    x_n8n_signature: Optional[str] = Header(None)
):
    """
    Handle N8N workflow webhooks.

    Validates the webhook signature and processes events from N8N workflows.

    Supported events:
    - odoo.invoice.create: Create invoice in Odoo
    - odoo.order.create: Create sales order
    - odoo.energy.log: Log energy production data
    - sync.request: Request entity sync
    """
    logger.info(f"Received N8N webhook: {payload.event} from workflow {payload.workflow_id}")

    # Validate signature if configured
    if settings.N8N_WEBHOOK_SECRET:
        if not x_n8n_signature:
            raise HTTPException(status_code=401, detail="Missing webhook signature")

        if not _verify_n8n_signature(payload.model_dump_json(), x_n8n_signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        n8n_service = N8NIntegration(payload.tenant_id)

        result = await n8n_service.handle_event(
            event=payload.event,
            data=payload.data,
            workflow_id=payload.workflow_id,
            execution_id=payload.execution_id
        )

        return {
            "status": "processed",
            "event": payload.event,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to process N8N webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")


@router.post("/odoo")
async def handle_odoo_webhook(request: Request):
    """
    Handle webhooks from Odoo.

    Odoo can send webhooks when records are modified.
    This allows reverse sync from Odoo to NGSI-LD.
    """
    try:
        body = await request.json()
        logger.info(f"Received Odoo webhook: {body.get('event')}")

        event = body.get("event")
        model = body.get("model")
        record_id = body.get("record_id")
        tenant_db = body.get("database")

        # Extract tenant ID from database name (format: nkz_odoo_{tenant_id})
        tenant_id = tenant_db.replace("nkz_odoo_", "") if tenant_db else None

        if not tenant_id:
            return {"status": "ignored", "reason": "unknown_tenant"}

        # Handle different events
        if event == "record.create" or event == "record.write":
            # Sync back to NGSI-LD if this model is mapped
            sync_service = NgsildSyncService(tenant_id)
            await sync_service.sync_odoo_to_ngsi(model, record_id)

        return {
            "status": "processed",
            "event": event,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to process Odoo webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _extract_tenant_from_subscription(subscription_id: str) -> Optional[str]:
    """
    Extract tenant ID from subscription ID.

    Subscription IDs follow the pattern: urn:ngsi-ld:Subscription:nkz-odoo-{tenant_id}-{type}
    """
    try:
        # Format: urn:ngsi-ld:Subscription:nkz-odoo-{tenant_id}-{type}
        parts = subscription_id.split(":")
        if len(parts) >= 4:
            sub_name = parts[-1]  # nkz-odoo-{tenant_id}-{type}
            name_parts = sub_name.split("-")
            if len(name_parts) >= 4 and name_parts[0] == "nkz" and name_parts[1] == "odoo":
                # Tenant ID is everything between "odoo-" and the last part (type)
                return "-".join(name_parts[2:-1])
    except Exception as e:
        logger.error(f"Failed to extract tenant from subscription: {e}")

    return None


def _verify_n8n_signature(payload: str, signature: str) -> bool:
    """Verify N8N webhook signature using HMAC."""
    expected = hmac.new(
        settings.N8N_WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)

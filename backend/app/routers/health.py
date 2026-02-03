"""
Nekazari Odoo ERP Module - Health Check Router

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

import logging
from fastapi import APIRouter
import httpx

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns status of this service and connected services.
    """
    health_status = {
        "status": "healthy",
        "service": "odoo-module-backend",
        "version": settings.API_VERSION
    }

    # Check Odoo connection
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.odoo_url}/web/health")
            health_status["odoo"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        logger.warning(f"Odoo health check failed: {e}")
        health_status["odoo"] = "unreachable"

    # Check Orion-LD connection
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ORION_URL}/version")
            health_status["orion_ld"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        logger.warning(f"Orion-LD health check failed: {e}")
        health_status["orion_ld"] = "unreachable"

    # Overall status
    if health_status.get("odoo") != "healthy":
        health_status["status"] = "degraded"

    return health_status


@router.get("/stats")
async def get_stats():
    """
    Get module statistics.

    Returns counts of various entities and sync status.
    """
    # This would query the database for actual stats
    # For now, return placeholder
    return {
        "products": 0,
        "assets": 0,
        "invoices": 0,
        "energyInstallations": 0,
        "pendingSync": 0
    }

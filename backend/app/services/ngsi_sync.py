"""
Nekazari Odoo ERP Module - NGSI-LD Sync Service

Handles synchronization between NGSI-LD entities and Odoo records.
Uses event-driven approach via Orion-LD subscriptions.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

import logging
from typing import Optional, Any
from datetime import datetime
import httpx

from app.config import settings
from app.services.odoo_client import OdooClient
from app.services.database import (
    get_tenant_odoo_info,
    get_entity_mapping_by_ngsi_id,
    create_entity_mapping
)

logger = logging.getLogger(__name__)


# Mapping from NGSI-LD types to Odoo models
NGSI_TO_ODOO_MODEL = {
    "AgriParcel": "product.template",
    "Device": "maintenance.equipment",
    "Building": "res.partner",
    "EnergyMeter": "energy.meter",
    "SolarPanel": "energy.installation",
    "WeatherStation": "maintenance.equipment"
}


class NgsildSyncService:
    """Service for syncing NGSI-LD entities with Odoo."""

    def __init__(self, tenant_id: str):
        """
        Initialize sync service for a tenant.

        Args:
            tenant_id: Tenant ID
        """
        self.tenant_id = tenant_id
        self.orion_url = settings.ORION_URL

    async def _get_odoo_database(self) -> str:
        """Get Odoo database name for tenant."""
        info = await get_tenant_odoo_info(self.tenant_id)
        if not info:
            raise ValueError(f"No Odoo configured for tenant: {self.tenant_id}")
        return info.get("database", f"nkz_odoo_{self.tenant_id}")

    async def fetch_entity(self, entity_id: str) -> Optional[dict]:
        """
        Fetch an entity from Orion-LD.

        Args:
            entity_id: NGSI-LD entity ID

        Returns:
            Entity data or None if not found
        """
        url = f"{self.orion_url}/ngsi-ld/v1/entities/{entity_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Accept": "application/ld+json",
                    "NGSILD-Tenant": self.tenant_id
                }
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.error(f"Failed to fetch entity {entity_id}: {response.status_code}")
                raise Exception(f"Failed to fetch entity: {response.text}")

    async def fetch_entities_by_type(self, entity_type: str) -> list[dict]:
        """
        Fetch all entities of a type from Orion-LD.

        Args:
            entity_type: NGSI-LD entity type

        Returns:
            List of entities
        """
        url = f"{self.orion_url}/ngsi-ld/v1/entities"
        params = {"type": entity_type, "limit": 1000}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers={
                    "Accept": "application/ld+json",
                    "NGSILD-Tenant": self.tenant_id
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch entities: {response.status_code}")
                return []

    async def sync_entity_to_odoo(self, entity: dict) -> dict:
        """
        Sync an NGSI-LD entity to Odoo.

        Creates or updates the corresponding Odoo record.

        Args:
            entity: NGSI-LD entity data

        Returns:
            Odoo record info (id, model, name)
        """
        entity_id = entity.get("id")
        entity_type = entity.get("type")

        logger.info(f"Syncing entity {entity_id} ({entity_type}) to Odoo")

        # Get Odoo model
        odoo_model = NGSI_TO_ODOO_MODEL.get(entity_type)
        if not odoo_model:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        # Get Odoo database
        db_name = await self._get_odoo_database()
        odoo_client = OdooClient()

        # Check if mapping exists
        existing = await get_entity_mapping_by_ngsi_id(self.tenant_id, entity_id)

        # Transform entity to Odoo values
        odoo_values = self._transform_to_odoo(entity, odoo_model)

        if existing:
            # Update existing record
            await odoo_client.update_record(
                db_name,
                odoo_model,
                existing["odoo_id"],
                odoo_values
            )
            odoo_id = existing["odoo_id"]
            logger.info(f"Updated Odoo record: {odoo_model}/{odoo_id}")

        else:
            # Create new record
            odoo_id = await odoo_client.create_record(
                db_name,
                odoo_model,
                odoo_values
            )
            logger.info(f"Created Odoo record: {odoo_model}/{odoo_id}")

        # Update mapping
        await create_entity_mapping(self.tenant_id, {
            "ngsi_id": entity_id,
            "ngsi_type": entity_type,
            "odoo_id": odoo_id,
            "odoo_model": odoo_model,
            "odoo_name": odoo_values.get("name", entity_id),
            "last_sync": datetime.utcnow().isoformat()
        })

        return {
            "id": odoo_id,
            "model": odoo_model,
            "name": odoo_values.get("name", entity_id)
        }

    async def sync_odoo_to_ngsi(self, odoo_model: str, odoo_id: int):
        """
        Sync an Odoo record back to NGSI-LD.

        Updates the corresponding NGSI-LD entity.

        Args:
            odoo_model: Odoo model name
            odoo_id: Odoo record ID
        """
        # This is for reverse sync when Odoo records are modified
        # Implementation depends on which fields should be synced back
        logger.info(f"Reverse sync requested: {odoo_model}/{odoo_id}")

        # TODO: Implement reverse sync if needed
        # For now, we only sync NGSI-LD -> Odoo
        pass

    async def full_sync(self) -> dict:
        """
        Perform full synchronization for all subscribed entity types.

        Returns:
            Sync result with counts
        """
        logger.info(f"Starting full sync for tenant: {self.tenant_id}")

        synced = 0
        errors = []

        for entity_type in NGSI_TO_ODOO_MODEL.keys():
            try:
                entities = await self.fetch_entities_by_type(entity_type)
                logger.info(f"Found {len(entities)} {entity_type} entities")

                for entity in entities:
                    try:
                        await self.sync_entity_to_odoo(entity)
                        synced += 1
                    except Exception as e:
                        error_msg = f"Failed to sync {entity.get('id')}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)

            except Exception as e:
                error_msg = f"Failed to fetch {entity_type}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        logger.info(f"Full sync complete: {synced} synced, {len(errors)} errors")

        return {"synced": synced, "errors": errors}

    def _transform_to_odoo(self, entity: dict, odoo_model: str) -> dict:
        """
        Transform NGSI-LD entity to Odoo record values.

        Args:
            entity: NGSI-LD entity
            odoo_model: Target Odoo model

        Returns:
            Dict of Odoo field values
        """
        entity_type = entity.get("type")
        entity_id = entity.get("id")

        # Base values
        values = {
            "name": self._get_property_value(entity, "name") or entity_id,
            "x_ngsi_id": entity_id  # Custom field to store NGSI-LD ID
        }

        # Type-specific transformations
        if entity_type == "AgriParcel":
            values.update(self._transform_agri_parcel(entity))
        elif entity_type == "Device":
            values.update(self._transform_device(entity))
        elif entity_type == "EnergyMeter":
            values.update(self._transform_energy_meter(entity))
        elif entity_type == "SolarPanel":
            values.update(self._transform_solar_panel(entity))
        elif entity_type == "Building":
            values.update(self._transform_building(entity))

        return values

    def _transform_agri_parcel(self, entity: dict) -> dict:
        """Transform AgriParcel to product.template."""
        return {
            "type": "product",
            "categ_id": 1,  # Default category, should be configured
            "description": self._get_property_value(entity, "description"),
            "x_area": self._get_property_value(entity, "area"),
            "x_crop_type": self._get_property_value(entity, "cropType"),
            "x_location": str(self._get_property_value(entity, "location"))
        }

    def _transform_device(self, entity: dict) -> dict:
        """Transform Device to maintenance.equipment."""
        return {
            "serial_no": self._get_property_value(entity, "serialNumber"),
            "note": self._get_property_value(entity, "description"),
            "x_device_type": self._get_property_value(entity, "deviceType"),
            "x_status": self._get_property_value(entity, "status")
        }

    def _transform_energy_meter(self, entity: dict) -> dict:
        """Transform EnergyMeter to energy.meter."""
        return {
            "code": self._get_property_value(entity, "meterCode"),
            "meter_type": self._get_property_value(entity, "meterType", "production"),
            "x_cups": self._get_property_value(entity, "cups")
        }

    def _transform_solar_panel(self, entity: dict) -> dict:
        """Transform SolarPanel to energy.installation."""
        return {
            "installation_type": "solar",
            "power_peak": self._get_property_value(entity, "peakPower"),
            "x_orientation": self._get_property_value(entity, "orientation"),
            "x_tilt": self._get_property_value(entity, "tilt")
        }

    def _transform_building(self, entity: dict) -> dict:
        """Transform Building to res.partner."""
        address = self._get_property_value(entity, "address") or {}
        return {
            "is_company": True,
            "street": address.get("streetAddress"),
            "city": address.get("addressLocality"),
            "zip": address.get("postalCode"),
            "country_id": False  # Would need to look up country
        }

    def _get_property_value(self, entity: dict, property_name: str, default: Any = None) -> Any:
        """
        Get value from NGSI-LD property.

        Handles both simple values and Property objects.
        """
        prop = entity.get(property_name)

        if prop is None:
            return default

        if isinstance(prop, dict):
            # NGSI-LD Property format
            if "value" in prop:
                return prop["value"]
            elif "@value" in prop:
                return prop["@value"]

        return prop


async def register_tenant_subscriptions(tenant_id: str):
    """
    Register NGSI-LD subscriptions for a tenant.

    Creates subscriptions for all entity types that should sync to Odoo.
    """
    logger.info(f"Registering NGSI-LD subscriptions for tenant: {tenant_id}")

    webhook_url = f"http://odoo-backend-service/api/odoo/webhook/ngsi"

    for entity_type in NGSI_TO_ODOO_MODEL.keys():
        subscription = {
            "id": f"urn:ngsi-ld:Subscription:nkz-odoo-{tenant_id}-{entity_type.lower()}",
            "type": "Subscription",
            "entities": [{"type": entity_type}],
            "notification": {
                "endpoint": {
                    "uri": webhook_url,
                    "accept": "application/json"
                }
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ORION_URL}/ngsi-ld/v1/subscriptions",
                json=subscription,
                headers={
                    "Content-Type": "application/ld+json",
                    "NGSILD-Tenant": tenant_id
                }
            )

            if response.status_code in [201, 409]:  # Created or already exists
                logger.info(f"Subscription registered for {entity_type}")
            else:
                logger.warning(f"Failed to register subscription for {entity_type}: {response.text}")


async def remove_tenant_subscriptions(tenant_id: str):
    """Remove all NGSI-LD subscriptions for a tenant."""
    logger.info(f"Removing NGSI-LD subscriptions for tenant: {tenant_id}")

    for entity_type in NGSI_TO_ODOO_MODEL.keys():
        sub_id = f"urn:ngsi-ld:Subscription:nkz-odoo-{tenant_id}-{entity_type.lower()}"

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{settings.ORION_URL}/ngsi-ld/v1/subscriptions/{sub_id}",
                headers={"NGSILD-Tenant": tenant_id}
            )

            if response.status_code in [204, 404]:
                logger.info(f"Subscription removed: {sub_id}")

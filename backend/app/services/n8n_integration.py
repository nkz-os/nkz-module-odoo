"""
Nekazari Odoo ERP Module - N8N Integration Service

Handles integration with N8N workflow automation platform.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

import logging
from typing import Any, Optional
from datetime import datetime
import httpx

from app.config import settings
from app.services.odoo_client import OdooClient
from app.services.database import get_tenant_odoo_info

logger = logging.getLogger(__name__)


class N8NIntegration:
    """Service for N8N workflow integration."""

    def __init__(self, tenant_id: str):
        """
        Initialize N8N integration for a tenant.

        Args:
            tenant_id: Tenant ID
        """
        self.tenant_id = tenant_id
        self.n8n_url = settings.N8N_URL

    async def _get_odoo_database(self) -> str:
        """Get Odoo database name for tenant."""
        info = await get_tenant_odoo_info(self.tenant_id)
        if not info:
            raise ValueError(f"No Odoo configured for tenant: {self.tenant_id}")
        return info.get("database", f"nkz_odoo_{self.tenant_id}")

    async def handle_event(
        self,
        event: str,
        data: dict,
        workflow_id: str,
        execution_id: str
    ) -> dict:
        """
        Handle an event from N8N workflow.

        Args:
            event: Event type (e.g., 'odoo.invoice.create')
            data: Event data
            workflow_id: N8N workflow ID
            execution_id: N8N execution ID

        Returns:
            Result of the operation
        """
        logger.info(f"Handling N8N event: {event} (workflow: {workflow_id})")

        handlers = {
            "odoo.invoice.create": self._handle_invoice_create,
            "odoo.order.create": self._handle_order_create,
            "odoo.energy.log": self._handle_energy_log,
            "odoo.product.update": self._handle_product_update,
            "sync.request": self._handle_sync_request
        }

        handler = handlers.get(event)
        if not handler:
            logger.warning(f"Unknown event type: {event}")
            return {"status": "ignored", "reason": f"Unknown event: {event}"}

        try:
            result = await handler(data)
            return {"status": "success", "result": result}

        except Exception as e:
            logger.error(f"Failed to handle event {event}: {e}")
            return {"status": "error", "error": str(e)}

    async def _handle_invoice_create(self, data: dict) -> dict:
        """
        Create an invoice in Odoo.

        Expected data:
            - partner_id or partner_email: Customer identifier
            - lines: List of invoice lines with product_id/name, quantity, price
            - date_invoice: Invoice date (optional)
        """
        logger.info("Creating invoice in Odoo from N8N")

        db_name = await self._get_odoo_database()
        odoo = OdooClient()

        # Find or create partner
        partner_id = data.get("partner_id")
        if not partner_id and data.get("partner_email"):
            partners = await odoo.search_records(
                db_name,
                "res.partner",
                [["email", "=", data["partner_email"]]],
                fields=["id"],
                limit=1
            )
            partner_id = partners[0]["id"] if partners else None

        if not partner_id:
            raise ValueError("Partner not found")

        # Prepare invoice lines
        invoice_lines = []
        for line in data.get("lines", []):
            product_id = line.get("product_id")
            if not product_id and line.get("product_name"):
                # Find product by name
                products = await odoo.search_records(
                    db_name,
                    "product.product",
                    [["name", "=", line["product_name"]]],
                    fields=["id"],
                    limit=1
                )
                product_id = products[0]["id"] if products else None

            invoice_lines.append((0, 0, {
                "product_id": product_id,
                "name": line.get("description", line.get("product_name", "Service")),
                "quantity": line.get("quantity", 1),
                "price_unit": line.get("price", 0)
            }))

        # Create invoice
        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": partner_id,
            "invoice_line_ids": invoice_lines,
            "invoice_date": data.get("date_invoice", datetime.now().strftime("%Y-%m-%d"))
        }

        invoice_id = await odoo.create_record(db_name, "account.move", invoice_vals)

        logger.info(f"Created invoice: {invoice_id}")
        return {"invoice_id": invoice_id}

    async def _handle_order_create(self, data: dict) -> dict:
        """
        Create a sales order in Odoo.

        Expected data:
            - partner_id or partner_email: Customer identifier
            - lines: List of order lines with product_id/name, quantity, price
        """
        logger.info("Creating sales order in Odoo from N8N")

        db_name = await self._get_odoo_database()
        odoo = OdooClient()

        # Find partner
        partner_id = data.get("partner_id")
        if not partner_id and data.get("partner_email"):
            partners = await odoo.search_records(
                db_name,
                "res.partner",
                [["email", "=", data["partner_email"]]],
                fields=["id"],
                limit=1
            )
            partner_id = partners[0]["id"] if partners else None

        if not partner_id:
            raise ValueError("Partner not found")

        # Prepare order lines
        order_lines = []
        for line in data.get("lines", []):
            product_id = line.get("product_id")
            if not product_id and line.get("product_name"):
                products = await odoo.search_records(
                    db_name,
                    "product.product",
                    [["name", "=", line["product_name"]]],
                    fields=["id"],
                    limit=1
                )
                product_id = products[0]["id"] if products else None

            order_lines.append((0, 0, {
                "product_id": product_id,
                "name": line.get("description", ""),
                "product_uom_qty": line.get("quantity", 1),
                "price_unit": line.get("price", 0)
            }))

        # Create order
        order_vals = {
            "partner_id": partner_id,
            "order_line": order_lines
        }

        order_id = await odoo.create_record(db_name, "sale.order", order_vals)

        logger.info(f"Created sales order: {order_id}")
        return {"order_id": order_id}

    async def _handle_energy_log(self, data: dict) -> dict:
        """
        Log energy production/consumption data in Odoo.

        Expected data:
            - installation_id or meter_id: Energy installation/meter identifier
            - value: Energy value (kWh)
            - timestamp: Reading timestamp
            - type: 'production' or 'consumption'
        """
        logger.info("Logging energy data in Odoo from N8N")

        db_name = await self._get_odoo_database()
        odoo = OdooClient()

        # Find installation or meter
        installation_id = data.get("installation_id")
        meter_id = data.get("meter_id")

        if not installation_id and not meter_id:
            raise ValueError("installation_id or meter_id required")

        # Create energy reading record
        # This depends on the Som Comunitats energy module structure
        reading_vals = {
            "installation_id": installation_id,
            "meter_id": meter_id,
            "value": data.get("value", 0),
            "reading_date": data.get("timestamp", datetime.now().isoformat()),
            "reading_type": data.get("type", "production")
        }

        # The actual model name depends on Som Comunitats module
        model = "energy.reading" if installation_id else "energy.meter.reading"

        try:
            reading_id = await odoo.create_record(db_name, model, reading_vals)
            logger.info(f"Created energy reading: {reading_id}")
            return {"reading_id": reading_id}

        except Exception as e:
            logger.warning(f"Energy reading model may not exist: {e}")
            return {"status": "skipped", "reason": "Energy module not installed"}

    async def _handle_product_update(self, data: dict) -> dict:
        """
        Update a product in Odoo.

        Expected data:
            - product_id or ngsi_id: Product identifier
            - values: Dict of fields to update
        """
        logger.info("Updating product in Odoo from N8N")

        db_name = await self._get_odoo_database()
        odoo = OdooClient()

        product_id = data.get("product_id")

        if not product_id and data.get("ngsi_id"):
            # Find by NGSI-LD ID custom field
            products = await odoo.search_records(
                db_name,
                "product.template",
                [["x_ngsi_id", "=", data["ngsi_id"]]],
                fields=["id"],
                limit=1
            )
            product_id = products[0]["id"] if products else None

        if not product_id:
            raise ValueError("Product not found")

        await odoo.update_record(
            db_name,
            "product.template",
            product_id,
            data.get("values", {})
        )

        logger.info(f"Updated product: {product_id}")
        return {"product_id": product_id}

    async def _handle_sync_request(self, data: dict) -> dict:
        """
        Handle sync request from N8N.

        Expected data:
            - entity_id: NGSI-LD entity ID to sync (optional)
            - entity_type: Type of entities to sync (optional)
            - full: Boolean for full sync (optional)
        """
        logger.info("Handling sync request from N8N")

        from app.services.ngsi_sync import NgsildSyncService

        sync_service = NgsildSyncService(self.tenant_id)

        if data.get("full"):
            result = await sync_service.full_sync()
            return {"synced": result["synced"], "errors": len(result["errors"])}

        elif data.get("entity_id"):
            entity = await sync_service.fetch_entity(data["entity_id"])
            if entity:
                odoo_record = await sync_service.sync_entity_to_odoo(entity)
                return {"synced": 1, "odoo_id": odoo_record["id"]}
            else:
                return {"synced": 0, "error": "Entity not found"}

        return {"status": "no_action"}

    async def trigger_workflow(
        self,
        webhook_url: str,
        payload: dict
    ) -> dict:
        """
        Trigger an N8N workflow via webhook.

        Args:
            webhook_url: N8N webhook URL
            payload: Data to send

        Returns:
            N8N response
        """
        logger.info(f"Triggering N8N workflow: {webhook_url}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json={
                    "tenant_id": self.tenant_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **payload
                },
                timeout=30.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"N8N webhook failed: {response.status_code}")
                raise Exception(f"N8N webhook failed: {response.text}")

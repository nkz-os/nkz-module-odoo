# -*- coding: utf-8 -*-
"""
Nekazari Connector - Work Order / AgriParcelOperation Sync

Publishes Odoo project tasks as NGSI-LD AgriParcelOperation entities
to the Orion-LD Context Broker.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

from odoo import api, fields, models
import logging
import requests

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    x_ngsi_id = fields.Char('NGSI-LD ID', readonly=True, copy=False)
    x_parcel_id = fields.Char('Parcel NGSI-LD ID')
    x_operation_type = fields.Selection([
        ('sowing', 'Sowing'),
        ('irrigation', 'Irrigation'),
        ('fertilization', 'Fertilization'),
        ('spraying', 'Spraying'),
        ('tillage', 'Tillage'),
        ('harvesting', 'Harvesting'),
    ], string='Operation Type')
    x_external_ref = fields.Char('External Reference')

    def _get_ngsi_headers(self, tenant_id):
        icp = self.env['ir.config_parameter'].sudo()
        return {
            "NGSILD-Tenant": tenant_id,
            "Fiware-Service": tenant_id,
            "Fiware-ServicePath": "/",
            "Content-Type": "application/ld+json",
            "Accept": "application/ld+json",
        }

    def action_publish_to_nekazari(self):
        """Publish this work order to Orion-LD as an AgriParcelOperation."""
        self.ensure_one()
        icp = self.env['ir.config_parameter'].sudo()
        orion_url = icp.get_param('nekazari.orion_url', 'http://orion-ld-service:1026')
        context_url = icp.get_param('nekazari.context_url', 'http://api-gateway-service:5000/ngsi-ld-context.json')
        tenant_id = icp.get_param('nekazari.tenant_id', self.env.cr.dbname.replace('nkz_odoo_', ''))

        headers = self._get_ngsi_headers(tenant_id)
        headers["Link"] = f'<{context_url}>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'

        payload = {
            "id": self.x_ngsi_id or f"urn:ngsi-ld:AgriParcelOperation:{tenant_id}:odoo-{self.id}",
            "type": "AgriParcelOperation",
            "operationType": {"type": "Property", "value": self.x_operation_type or "tillage"},
            "status": {"type": "Property", "value": "issued"},
            "workOrder": {"type": "Property", "value": self.name or f"ODT-{self.id}"},
            "source": {"type": "Property", "value": "odoo"},
            "externalRef": {"type": "Property", "value": f"ODT-{self.id}"},
            "dataSource": {"type": "Property", "value": "odoo"},
            "plannedDate": {"type": "Property", "value": {
                "@type": "DateTime",
                "@value": self.date_deadline.isoformat() if self.date_deadline else fields.Datetime.now().isoformat()
            }},
            "assignedTo": {"type": "Property", "value": self.user_id.email or ""},
            "hasAgriParcel": {"type": "Relationship", "object": self.x_parcel_id} if self.x_parcel_id else {},
            "@context": [context_url],
        }

        try:
            if self.x_ngsi_id:
                resp = requests.patch(
                    f"{orion_url}/ngsi-ld/v1/entities/{self.x_ngsi_id}/attrs",
                    json={k: v for k, v in payload.items() if k not in ('id', 'type', '@context')},
                    headers={**headers, "Content-Type": "application/json"},
                    timeout=10,
                )
            else:
                resp = requests.post(
                    f"{orion_url}/ngsi-ld/v1/entities",
                    json=payload,
                    headers=headers,
                    timeout=10,
                )

            if resp.status_code in (200, 201, 204):
                if not self.x_ngsi_id:
                    self.x_ngsi_id = payload["id"]
                _logger.info("Published work order %s to Orion-LD", self.id)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {'title': 'Published to Nekazari', 'type': 'success'},
                }
            else:
                _logger.error("Failed to publish: %s", resp.text)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {'title': f'Error: {resp.text}', 'type': 'danger'},
                }
        except Exception as e:
            _logger.error("Failed to publish work order: %s", e)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': str(e), 'type': 'danger'},
            }

    @api.model
    def cron_publish_pending_work_orders(self):
        """Cron job: publish work orders with op type but no NGSI ID."""
        pending = self.search([
            ('x_operation_type', '!=', False),
            ('x_ngsi_id', '=', False),
        ])
        count = 0
        for task in pending:
            try:
                task.action_publish_to_nekazari()
                count += 1
            except Exception as e:
                _logger.error("Failed to auto-publish task %s: %s", task.id, e)
        _logger.info("cron_publish_pending_work_orders: published %d tasks", count)
        return count

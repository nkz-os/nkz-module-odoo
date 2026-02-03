# -*- coding: utf-8 -*-
"""
Nekazari Connector - Product Template Extension

Extends product.template with NGSI-LD fields for AgriParcel sync.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # NGSI-LD Integration Fields
    x_ngsi_id = fields.Char(
        string='NGSI-LD ID',
        help='Unique identifier in Nekazari NGSI-LD Context Broker',
        index=True,
        copy=False
    )
    x_ngsi_type = fields.Char(
        string='NGSI-LD Type',
        help='Entity type in NGSI-LD (e.g., AgriParcel)',
        default='AgriParcel'
    )
    x_last_sync = fields.Datetime(
        string='Last Sync',
        help='Last synchronization with Nekazari platform',
        readonly=True
    )

    # AgriParcel specific fields
    x_area = fields.Float(
        string='Area (ha)',
        help='Parcel area in hectares'
    )
    x_crop_type = fields.Char(
        string='Crop Type',
        help='Type of crop planted'
    )
    x_location = fields.Text(
        string='GeoJSON Location',
        help='GeoJSON representation of parcel geometry'
    )
    x_soil_type = fields.Char(
        string='Soil Type',
        help='Classification of soil'
    )

    # Prediction fields (from Intelligence module)
    x_predicted_yield = fields.Float(
        string='Predicted Yield',
        help='AI-predicted yield for current season',
        readonly=True
    )
    x_yield_confidence = fields.Float(
        string='Yield Confidence',
        help='Confidence level of yield prediction (0-1)',
        readonly=True
    )

    @api.model
    def create(self, vals):
        """Override create to trigger Nekazari sync."""
        record = super().create(vals)
        if record.x_ngsi_id:
            record._trigger_nekazari_webhook('create')
        return record

    def write(self, vals):
        """Override write to trigger Nekazari sync."""
        result = super().write(vals)
        for record in self:
            if record.x_ngsi_id:
                record._trigger_nekazari_webhook('write')
        return result

    def _trigger_nekazari_webhook(self, event):
        """Trigger webhook to Nekazari backend."""
        try:
            # Get webhook URL from system parameters
            webhook_url = self.env['ir.config_parameter'].sudo().get_param(
                'nekazari.webhook_url',
                'http://odoo-backend-service/api/odoo/webhook/odoo'
            )

            import httpx

            payload = {
                'event': f'record.{event}',
                'model': 'product.template',
                'record_id': self.id,
                'database': self.env.cr.dbname,
                'ngsi_id': self.x_ngsi_id
            }

            # Fire and forget (async would be better but this is simpler)
            with httpx.Client(timeout=5.0) as client:
                client.post(webhook_url, json=payload)

            _logger.info(f"Nekazari webhook triggered: {event} for {self.x_ngsi_id}")

        except Exception as e:
            _logger.warning(f"Failed to trigger Nekazari webhook: {e}")

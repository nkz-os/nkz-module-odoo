# -*- coding: utf-8 -*-
"""
Nekazari Connector - Maintenance Equipment Extension

Extends maintenance.equipment with NGSI-LD fields for Device sync.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    # NGSI-LD Integration Fields
    x_ngsi_id = fields.Char(
        string='NGSI-LD ID',
        help='Unique identifier in Nekazari NGSI-LD Context Broker',
        index=True,
        copy=False
    )
    x_ngsi_type = fields.Char(
        string='NGSI-LD Type',
        help='Entity type in NGSI-LD (e.g., Device, WeatherStation)',
        default='Device'
    )
    x_last_sync = fields.Datetime(
        string='Last Sync',
        help='Last synchronization with Nekazari platform',
        readonly=True
    )

    # Device specific fields
    x_device_type = fields.Selection([
        ('sensor', 'Sensor'),
        ('actuator', 'Actuator'),
        ('gateway', 'Gateway'),
        ('weather_station', 'Weather Station'),
        ('solar_inverter', 'Solar Inverter'),
        ('energy_meter', 'Energy Meter'),
        ('other', 'Other')
    ], string='Device Type', default='sensor')

    x_status = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('maintenance', 'Maintenance'),
        ('error', 'Error')
    ], string='Device Status', default='offline')

    x_firmware_version = fields.Char(
        string='Firmware Version',
        help='Current firmware version of the device'
    )

    x_last_reading = fields.Datetime(
        string='Last Reading',
        help='Timestamp of last data reading from device',
        readonly=True
    )

    x_battery_level = fields.Float(
        string='Battery Level (%)',
        help='Current battery level if battery-powered'
    )

    x_location = fields.Text(
        string='GeoJSON Location',
        help='GeoJSON representation of device location'
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
            webhook_url = self.env['ir.config_parameter'].sudo().get_param(
                'nekazari.webhook_url',
                'http://odoo-backend-service/api/odoo/webhook/odoo'
            )

            import httpx

            payload = {
                'event': f'record.{event}',
                'model': 'maintenance.equipment',
                'record_id': self.id,
                'database': self.env.cr.dbname,
                'ngsi_id': self.x_ngsi_id
            }

            with httpx.Client(timeout=5.0) as client:
                client.post(webhook_url, json=payload)

            _logger.info(f"Nekazari webhook triggered: {event} for {self.x_ngsi_id}")

        except Exception as e:
            _logger.warning(f"Failed to trigger Nekazari webhook: {e}")

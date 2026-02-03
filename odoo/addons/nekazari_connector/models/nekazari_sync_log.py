# -*- coding: utf-8 -*-
"""
Nekazari Connector - Sync Log Model

Tracks synchronization events between Odoo and Nekazari.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class NekazariSyncLog(models.Model):
    _name = 'nekazari.sync.log'
    _description = 'Nekazari Sync Log'
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('nekazari.sync.log')
    )

    sync_type = fields.Selection([
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
        ('webhook', 'Webhook'),
        ('api', 'API')
    ], string='Sync Type', required=True, default='manual')

    direction = fields.Selection([
        ('odoo_to_ngsi', 'Odoo → NGSI-LD'),
        ('ngsi_to_odoo', 'NGSI-LD → Odoo')
    ], string='Direction', required=True)

    model = fields.Char(
        string='Model',
        help='Odoo model that was synced'
    )

    ngsi_type = fields.Char(
        string='NGSI-LD Type',
        help='NGSI-LD entity type'
    )

    record_count = fields.Integer(
        string='Records',
        help='Number of records synced'
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('error', 'Error')
    ], string='State', default='draft')

    error_message = fields.Text(
        string='Error Message',
        help='Error details if sync failed'
    )

    duration = fields.Float(
        string='Duration (s)',
        help='Sync duration in seconds'
    )

    start_date = fields.Datetime(
        string='Start Time',
        default=fields.Datetime.now
    )

    end_date = fields.Datetime(
        string='End Time'
    )

    @api.model
    def log_sync(self, sync_type, direction, model=None, ngsi_type=None,
                 record_count=0, state='done', error_message=None, duration=0):
        """
        Create a sync log entry.

        Args:
            sync_type: Type of sync (manual, scheduled, webhook, api)
            direction: Direction (odoo_to_ngsi, ngsi_to_odoo)
            model: Odoo model name
            ngsi_type: NGSI-LD entity type
            record_count: Number of records
            state: Sync state
            error_message: Error message if failed
            duration: Duration in seconds
        """
        return self.create({
            'sync_type': sync_type,
            'direction': direction,
            'model': model,
            'ngsi_type': ngsi_type,
            'record_count': record_count,
            'state': state,
            'error_message': error_message,
            'duration': duration,
            'end_date': fields.Datetime.now()
        })

    def action_retry(self):
        """Retry a failed sync."""
        self.ensure_one()
        if self.state == 'error':
            # Trigger re-sync based on sync type
            _logger.info(f"Retrying sync: {self.name}")
            # Implementation depends on what was being synced
            self.write({'state': 'draft'})

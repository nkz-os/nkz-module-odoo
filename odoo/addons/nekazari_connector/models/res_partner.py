# -*- coding: utf-8 -*-
"""
Nekazari Connector - Res Partner Extension

Extends res.partner with NGSI-LD fields for Building sync.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # NGSI-LD Integration Fields
    x_ngsi_id = fields.Char(
        string='NGSI-LD ID',
        help='Unique identifier in Nekazari NGSI-LD Context Broker',
        index=True,
        copy=False
    )
    x_ngsi_type = fields.Char(
        string='NGSI-LD Type',
        help='Entity type in NGSI-LD (e.g., Building)',
        default='Building'
    )
    x_last_sync = fields.Datetime(
        string='Last Sync',
        help='Last synchronization with Nekazari platform',
        readonly=True
    )

    # Building specific fields
    x_building_type = fields.Selection([
        ('farm', 'Farm Building'),
        ('warehouse', 'Warehouse'),
        ('greenhouse', 'Greenhouse'),
        ('solar_installation', 'Solar Installation'),
        ('office', 'Office'),
        ('residential', 'Residential'),
        ('other', 'Other')
    ], string='Building Type')

    x_floor_area = fields.Float(
        string='Floor Area (m²)',
        help='Total floor area of the building'
    )

    x_location = fields.Text(
        string='GeoJSON Location',
        help='GeoJSON representation of building location/footprint'
    )

    # Energy community fields
    x_is_energy_community_member = fields.Boolean(
        string='Energy Community Member',
        help='Is this partner a member of an energy community?'
    )

    x_energy_share = fields.Float(
        string='Energy Share (%)',
        help='Share of energy in the community (0-100)'
    )

    x_cups_code = fields.Char(
        string='CUPS Code',
        help='Universal Point of Supply Code (Spain)'
    )

# -*- coding: utf-8 -*-
{
    'name': 'Nekazari Connector',
    'version': '16.0.1.0.0',
    'category': 'Technical',
    'summary': 'Connect Odoo with Nekazari FIWARE platform',
    'description': """
Nekazari Connector
==================

This module connects Odoo with the Nekazari FIWARE-based platform.

Features:
---------
* Sync entities with NGSI-LD Context Broker
* Custom fields for NGSI-LD entity IDs
* Webhook endpoints for real-time sync
* Integration with energy community modules

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika

For more information, visit: https://nekazari.com
    """,
    'author': 'Kate Benetis / Robotika',
    'website': 'https://robotika.cloud',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'product',
        'sale',
        'purchase',
        'stock',
        'maintenance',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'data/cron_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'external_dependencies': {
        'python': ['httpx'],
    },
}

# -*- coding: utf-8 -*-
"""
Nekazari Connector - Webhook Controller

Handles incoming webhooks from Nekazari backend.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class NekazariWebhookController(http.Controller):
    """Controller for Nekazari webhooks."""

    @http.route(
        '/nekazari/webhook/sync',
        type='json',
        auth='none',
        methods=['POST'],
        csrf=False
    )
    def handle_sync_webhook(self, **kwargs):
        """
        Handle sync webhook from Nekazari backend.

        Expected payload:
        {
            "event": "sync.entity",
            "entity_id": "urn:ngsi-ld:AgriParcel:xxx",
            "entity_type": "AgriParcel",
            "data": {...}
        }
        """
        try:
            data = request.jsonrequest

            _logger.info(f"Received Nekazari webhook: {data.get('event')}")

            event = data.get('event')
            entity_id = data.get('entity_id')
            entity_type = data.get('entity_type')
            entity_data = data.get('data', {})

            if event == 'sync.entity':
                return self._handle_entity_sync(entity_id, entity_type, entity_data)
            elif event == 'sync.prediction':
                return self._handle_prediction_sync(entity_id, entity_data)
            else:
                return {'status': 'ignored', 'reason': f'Unknown event: {event}'}

        except Exception as e:
            _logger.error(f"Webhook error: {e}")
            return {'status': 'error', 'message': str(e)}

    def _handle_entity_sync(self, entity_id, entity_type, data):
        """
        Handle entity sync from NGSI-LD.

        Updates or creates the corresponding Odoo record.
        """
        # Map NGSI-LD types to Odoo models
        type_to_model = {
            'AgriParcel': 'product.template',
            'Device': 'maintenance.equipment',
            'Building': 'res.partner',
            'WeatherStation': 'maintenance.equipment'
        }

        model_name = type_to_model.get(entity_type)
        if not model_name:
            return {'status': 'ignored', 'reason': f'Unknown entity type: {entity_type}'}

        Model = request.env[model_name].sudo()

        # Find existing record by NGSI-LD ID
        record = Model.search([('x_ngsi_id', '=', entity_id)], limit=1)

        # Transform NGSI-LD data to Odoo values
        values = self._transform_ngsi_to_odoo(entity_type, data)
        values['x_ngsi_id'] = entity_id
        values['x_ngsi_type'] = entity_type
        values['x_last_sync'] = fields.Datetime.now()

        if record:
            record.write(values)
            _logger.info(f"Updated {model_name} from NGSI-LD: {entity_id}")
            return {'status': 'updated', 'odoo_id': record.id}
        else:
            record = Model.create(values)
            _logger.info(f"Created {model_name} from NGSI-LD: {entity_id}")
            return {'status': 'created', 'odoo_id': record.id}

    def _handle_prediction_sync(self, entity_id, data):
        """
        Handle prediction sync from Intelligence module.

        Updates prediction fields on the entity.
        """
        # Find record by NGSI-LD ID across all synced models
        for model_name in ['product.template', 'maintenance.equipment']:
            Model = request.env[model_name].sudo()
            record = Model.search([('x_ngsi_id', '=', entity_id)], limit=1)

            if record:
                values = {}

                if 'expected_yield' in data:
                    values['x_predicted_yield'] = data['expected_yield']
                if 'confidence' in data:
                    values['x_yield_confidence'] = data['confidence']

                if values:
                    record.write(values)
                    _logger.info(f"Updated predictions for {entity_id}")
                    return {'status': 'updated', 'odoo_id': record.id}

        return {'status': 'ignored', 'reason': 'Entity not found'}

    def _transform_ngsi_to_odoo(self, entity_type, data):
        """Transform NGSI-LD entity data to Odoo field values."""
        values = {}

        # Common fields
        if 'name' in data:
            values['name'] = self._get_value(data['name'])

        # Type-specific transformations
        if entity_type == 'AgriParcel':
            if 'area' in data:
                values['x_area'] = self._get_value(data['area'])
            if 'cropType' in data:
                values['x_crop_type'] = self._get_value(data['cropType'])
            if 'location' in data:
                values['x_location'] = json.dumps(self._get_value(data['location']))
            if 'soilType' in data:
                values['x_soil_type'] = self._get_value(data['soilType'])
            if 'description' in data:
                values['description'] = self._get_value(data['description'])

        elif entity_type == 'Device':
            if 'deviceType' in data:
                device_type = self._get_value(data['deviceType'])
                # Map to selection value
                type_map = {
                    'Sensor': 'sensor',
                    'Actuator': 'actuator',
                    'Gateway': 'gateway',
                    'WeatherStation': 'weather_station'
                }
                values['x_device_type'] = type_map.get(device_type, 'other')

            if 'status' in data:
                status = self._get_value(data['status']).lower()
                if status in ['online', 'offline', 'maintenance', 'error']:
                    values['x_status'] = status

            if 'serialNumber' in data:
                values['serial_no'] = self._get_value(data['serialNumber'])
            if 'location' in data:
                values['x_location'] = json.dumps(self._get_value(data['location']))

        elif entity_type == 'Building':
            if 'address' in data:
                address = self._get_value(data['address'])
                if isinstance(address, dict):
                    values['street'] = address.get('streetAddress')
                    values['city'] = address.get('addressLocality')
                    values['zip'] = address.get('postalCode')

            if 'floorArea' in data:
                values['x_floor_area'] = self._get_value(data['floorArea'])
            if 'location' in data:
                values['x_location'] = json.dumps(self._get_value(data['location']))

        return values

    def _get_value(self, prop):
        """Extract value from NGSI-LD property format."""
        if isinstance(prop, dict):
            return prop.get('value') or prop.get('@value')
        return prop


# Import fields for datetime
from odoo import fields

/**
 * Nekazari Odoo ERP Module - Slot Registration
 *
 * Exports viewerSlots for host integration with Unified Viewer.
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

import { ModuleViewerSlots } from './types';
import OdooEntityLink from '../components/slots/OdooEntityLink';
import OdooQuickActions from '../components/slots/OdooQuickActions';
import OdooStatusWidget from '../components/slots/OdooStatusWidget';
import { OdooProvider } from '../services/context';

const MODULE_ID = 'odoo-erp';

export const viewerSlots: ModuleViewerSlots = {
  'layer-toggle': [],

  'context-panel': [
    {
      id: 'odoo-entity-link',
      moduleId: MODULE_ID,
      component: 'OdooEntityLink',
      priority: 60,
      localComponent: OdooEntityLink,
      showWhen: {
        entityType: ['AgriParcel', 'Device', 'Building', 'EnergyMeter', 'SolarPanel']
      }
    },
    {
      id: 'odoo-status-widget',
      moduleId: MODULE_ID,
      component: 'OdooStatusWidget',
      priority: 70,
      localComponent: OdooStatusWidget,
      showWhen: {
        entityType: ['AgriParcel', 'Device', 'Building']
      }
    }
  ],

  'bottom-panel': [],

  'entity-tree': [
    {
      id: 'odoo-quick-actions',
      moduleId: MODULE_ID,
      component: 'OdooQuickActions',
      priority: 50,
      localComponent: OdooQuickActions
    }
  ],

  'map-layer': [],

  moduleProvider: OdooProvider
};

export default viewerSlots;

/**
 * Nekazari Odoo ERP Module - Slot Registration
 *
 * Exports viewerSlots for host integration with Unified Viewer.
 */

import { ModuleViewerSlots } from './types';
import OdooEntityLink from '../components/slots/OdooEntityLink';
import OdooStatusWidget from '../components/slots/OdooStatusWidget';
import OdooQuickActions from '../components/slots/OdooQuickActions';
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
    },
    {
      id: 'odoo-quick-actions',
      moduleId: MODULE_ID,
      component: 'OdooQuickActions',
      priority: 80,
      localComponent: OdooQuickActions,
    }
  ],

  'bottom-panel': [],

  'entity-tree': [],

  'map-layer': [],

  moduleProvider: OdooProvider
};

export default viewerSlots;

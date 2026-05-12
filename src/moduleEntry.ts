import { defineModule } from "@nekazari/module-kit";
/**
 * IIFE entry point — host loads this bundle via <script src="/modules/odoo-erp/nkz-module.js">.
 * Registers the module with window.__NKZ__ so slots appear in the viewer.
 * The main component is shown on the /odoo route (description + link to Odoo).
 *
 * Module id must match marketplace_modules.id exactly.
 */
import './i18n';
import { viewerSlots } from './slots';
import OdooModulePage from './OdooModulePage';

const MODULE_ID = 'odoo-erp';

if (typeof window !== 'undefined' && window.__NKZ__) {
  window.__NKZ__.register({
    id: MODULE_ID,
    viewerSlots,
    main: OdooModulePage,
    version: '1.0.0',
  });
}


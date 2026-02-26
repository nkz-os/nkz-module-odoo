/**
 * IIFE entry point — host loads this bundle via <script src="/modules/odoo-erp/nkz-module.js">.
 * Registers the module with window.__NKZ__ so slots appear in the viewer.
 *
 * Module id must match marketplace_modules.id exactly.
 */
import { viewerSlots } from './slots';

const MODULE_ID = 'odoo-erp';

if (typeof window !== 'undefined' && (window as any).__NKZ__) {
  (window as any).__NKZ__.register({
    id: MODULE_ID,
    viewerSlots,
    version: '1.0.0',
  });
}

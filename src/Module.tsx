import { defineModule, withModuleProvider } from '@nekazari/module-kit';
import React, { lazy, Suspense } from 'react';
import './i18n';
import { viewerSlots } from './slots';
import { OdooProvider } from './services/context';
import pkg from '../package.json';

const LazyApp = lazy(() => import('./OdooModulePage'));

const MainWrapper: React.FC = () => (
  <OdooProvider>
    <Suspense fallback={<div className="p-8 text-center">Loading Odoo ERP…</div>}>
      <LazyApp />
    </Suspense>
  </OdooProvider>
);

export default defineModule({
  id: 'odoo-erp',
  displayName: 'Odoo ERP',
  version: pkg.version,
  hostApiVersion: '^2.0.0',
  description: 'Multitenant farm and energy community management — Nekazari Platform Module',
  accent: { base: '#7C3AED', soft: '#EDE9FE', strong: '#5B21B6' },
  icon: 'briefcase',
  main: MainWrapper,
  api: { basePath: '/api/odoo' },
  slots: withModuleProvider(viewerSlots) as never,
});

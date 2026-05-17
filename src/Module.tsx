import { defineModule } from '@nekazari/module-kit';
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

// OdooProvider was previously slots.moduleProvider. SlotsSchema only allows slot
// arrays; federated widgets mount into their own React trees, so wrap each
// localComponent so widgets get the provider on mount.
const { moduleProvider: _moduleProvider, ...rawSlots } = viewerSlots as Record<string, unknown>;
const wrappedSlots = Object.fromEntries(
  Object.entries(rawSlots).map(([slot, entries]) => [
    slot,
    (entries as Array<Record<string, any>>).map((entry) => {
      const Inner = entry.localComponent as React.ComponentType<any> | undefined;
      if (!Inner) return entry;
      const Wrapped: React.FC<any> = (props) => (
        <OdooProvider>
          <Inner {...props} />
        </OdooProvider>
      );
      return { ...entry, localComponent: Wrapped };
    }),
  ]),
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
  slots: wrappedSlots as never,
});

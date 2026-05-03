/**
 * Nekazari Odoo ERP Module - Quick Actions Slot Widget
 *
 * Provides quick access to common Odoo operations.
 * Displayed in the entity tree panel.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useTranslation } from '@nekazari/sdk';
import { SlotShellCompact } from '@nekazari/viewer-kit';
import { Badge, Spinner, Stack, IconButton } from '@nekazari/ui-kit';
import {
  Building2,
  FileText,
  Package,
  Sun,
  TrendingUp,
  RefreshCw,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { SlotWidgetProps } from '../../slots/types';
import { odooApi, OdooStats } from '../../services/api';

const odooAccent = { base: '#6366F1', soft: '#E0E7FF', strong: '#4338CA' };

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  badge?: number;
}

const OdooQuickActions: React.FC<SlotWidgetProps> = () => {
  const { t } = useTranslation('odoo');
  const [stats, setStats] = useState<OdooStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [odooBaseUrl, setOdooBaseUrl] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const tenantInfo = await odooApi.getTenantInfo();
        setOdooBaseUrl(tenantInfo.odooUrl);

        if (tenantInfo.status === 'active') {
          const statsData = await odooApi.getStats();
          setStats(statsData);
        }
      } catch (err) {
        console.error('Failed to fetch Odoo data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const quickActions: QuickAction[] = useMemo(
    () => [
      {
        id: 'products',
        label: t('quickActions.products'),
        icon: <Package size={18} />,
        path: '/web#action=product.product_template_action',
        badge: stats?.products,
      },
      {
        id: 'invoices',
        label: t('quickActions.invoices'),
        icon: <FileText size={18} />,
        path: '/web#action=account.action_move_out_invoice_type',
        badge: stats?.invoices,
      },
      {
        id: 'assets',
        label: t('quickActions.assets'),
        icon: <Building2 size={18} />,
        path: '/web#action=maintenance.hr_equipment_action',
        badge: stats?.assets,
      },
      {
        id: 'energy',
        label: t('quickActions.energy'),
        icon: <Sun size={18} />,
        path: '/web#action=energy_community.action_energy_installation',
        badge: stats?.energyInstallations,
      },
      {
        id: 'reports',
        label: t('quickActions.reports'),
        icon: <TrendingUp size={18} />,
        path: '/web#action=account_reports.action_account_report_bs',
      },
    ],
    [t, stats]
  );

  const handleActionClick = (action: QuickAction) => {
    if (odooBaseUrl) {
      window.open(`${odooBaseUrl}${action.path}`, '_blank');
    }
  };

  if (isLoading) {
    return (
      <SlotShellCompact moduleId="odoo-erp" accent={odooAccent}>
        <div className="flex items-center gap-2">
          <Building2 size={20} className="text-nkz-accent-base" />
          <span className="text-nkz-sm font-medium text-nkz-text-primary">{t('quickActions.title')}</span>
        </div>
        <div className="flex items-center gap-2 p-nkz-inline">
          <Spinner size="sm" />
          <span className="text-nkz-sm text-nkz-text-secondary">{t('quickActions.loading')}</span>
        </div>
      </SlotShellCompact>
    );
  }

  if (!odooBaseUrl) {
    return (
      <SlotShellCompact moduleId="odoo-erp" accent={odooAccent}>
        <div className="flex items-center gap-2">
          <Building2 size={20} className="text-nkz-accent-base" />
          <span className="text-nkz-sm font-medium text-nkz-text-primary">{t('quickActions.title')}</span>
        </div>
        <div className="text-nkz-sm text-nkz-text-muted p-nkz-inline">
          {t('quickActions.notConfigured')}
        </div>
      </SlotShellCompact>
    );
  }

  return (
    <SlotShellCompact moduleId="odoo-erp" accent={odooAccent}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <Building2 size={20} className="text-nkz-accent-base" />
          <span className="text-nkz-sm font-medium text-nkz-text-primary">{t('quickActions.title')}</span>
        </div>
        <a
          href={odooBaseUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-nkz-text-muted hover:text-nkz-accent-base"
          title={t('quickActions.openOdooTitle')}
        >
          <ExternalLink size={16} />
        </a>
      </div>

      <Stack gap="tight">
        {quickActions.map((action) => (
          <div
            key={action.id}
            className="flex items-center justify-between p-nkz-inline bg-nkz-surface-sunken rounded-nkz-md hover:bg-nkz-surface transition-colors cursor-pointer"
            onClick={() => handleActionClick(action)}
          >
            <div className="flex items-center gap-2">
              <span className="text-nkz-accent-base">{action.icon}</span>
              <span className="text-nkz-sm text-nkz-text-primary">{action.label}</span>
            </div>
            <div className="flex items-center gap-2">
              {action.badge !== undefined && (
                <span className="bg-nkz-accent-soft text-nkz-accent-strong text-nkz-xs px-nkz-inline py-0.5 rounded-nkz-full font-medium">
                  {action.badge}
                </span>
              )}
              <ChevronRight size={16} className="text-nkz-text-muted" />
            </div>
          </div>
        ))}
      </Stack>

      {stats?.pendingSync && stats.pendingSync > 0 && (
        <div className="mt-2 p-nkz-inline bg-nkz-warning-soft rounded-nkz-md text-nkz-xs flex items-center gap-2 border border-nkz-warning">
          <RefreshCw size={14} className="text-nkz-warning" />
          <span className="text-nkz-warning-strong">{t('quickActions.pendingSync', { count: stats.pendingSync })}</span>
        </div>
      )}
    </SlotShellCompact>
  );
};

export default OdooQuickActions;

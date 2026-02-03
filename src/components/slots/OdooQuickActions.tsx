/**
 * Nekazari Odoo ERP Module - Quick Actions Slot Widget
 *
 * Provides quick access to common Odoo operations.
 * Displayed in the entity tree panel.
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

import React, { useState, useEffect } from 'react';
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

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  badge?: number;
}

const OdooQuickActions: React.FC<SlotWidgetProps> = () => {
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

  const quickActions: QuickAction[] = [
    {
      id: 'products',
      label: 'Products',
      icon: <Package size={18} />,
      path: '/web#action=product.product_template_action',
      badge: stats?.products
    },
    {
      id: 'invoices',
      label: 'Invoices',
      icon: <FileText size={18} />,
      path: '/web#action=account.action_move_out_invoice_type',
      badge: stats?.invoices
    },
    {
      id: 'assets',
      label: 'Assets',
      icon: <Building2 size={18} />,
      path: '/web#action=maintenance.hr_equipment_action',
      badge: stats?.assets
    },
    {
      id: 'energy',
      label: 'Energy Installations',
      icon: <Sun size={18} />,
      path: '/web#action=energy_community.action_energy_installation',
      badge: stats?.energyInstallations
    },
    {
      id: 'reports',
      label: 'Reports',
      icon: <TrendingUp size={18} />,
      path: '/web#action=account_reports.action_account_report_bs'
    }
  ];

  const handleActionClick = (action: QuickAction) => {
    if (odooBaseUrl) {
      window.open(`${odooBaseUrl}${action.path}`, '_blank');
    }
  };

  if (isLoading) {
    return (
      <div className="odoo-slot-widget">
        <div className="odoo-slot-header">
          <Building2 size={20} className="odoo-slot-icon" />
          <span>Odoo ERP</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem' }}>
          <RefreshCw size={16} className="animate-spin" />
          <span style={{ fontSize: '0.875rem' }}>Loading...</span>
        </div>
      </div>
    );
  }

  if (!odooBaseUrl) {
    return (
      <div className="odoo-slot-widget">
        <div className="odoo-slot-header">
          <Building2 size={20} className="odoo-slot-icon" />
          <span>Odoo ERP</span>
        </div>
        <div style={{ padding: '0.5rem', fontSize: '0.875rem', color: 'var(--odoo-text-muted)' }}>
          Odoo not configured for this tenant.
        </div>
      </div>
    );
  }

  return (
    <div className="odoo-slot-widget">
      <div className="odoo-slot-header">
        <Building2 size={20} className="odoo-slot-icon" />
        <span>Odoo ERP</span>
        <a
          href={odooBaseUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={{ marginLeft: 'auto' }}
          title="Open Odoo"
        >
          <ExternalLink size={16} style={{ color: 'var(--odoo-text-muted)' }} />
        </a>
      </div>

      <div className="odoo-link-list">
        {quickActions.map((action) => (
          <div
            key={action.id}
            className="odoo-link-item"
            onClick={() => handleActionClick(action)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ color: 'var(--odoo-primary)' }}>{action.icon}</span>
              <span>{action.label}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {action.badge !== undefined && (
                <span className="odoo-badge odoo-badge-info">{action.badge}</span>
              )}
              <ChevronRight size={16} style={{ color: 'var(--odoo-text-muted)' }} />
            </div>
          </div>
        ))}
      </div>

      {stats?.pendingSync && stats.pendingSync > 0 && (
        <div
          style={{
            marginTop: '0.5rem',
            padding: '0.5rem',
            background: 'var(--odoo-warning)',
            borderRadius: '0.25rem',
            fontSize: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <RefreshCw size={14} />
          <span>{stats.pendingSync} entities pending sync</span>
        </div>
      )}
    </div>
  );
};

export default OdooQuickActions;

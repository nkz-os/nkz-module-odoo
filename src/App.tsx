/**
 * Nekazari Odoo ERP Module - Main Application
 *
 * Native dashboard with SSO link to Odoo.
 * No iframe — Odoo runs on its own subdomain with Keycloak SSO.
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

import React, { useState } from 'react';
import { useTranslation } from '@nekazari/sdk';
import {
  Building2, Sun, Leaf, RefreshCw, ExternalLink,
  Settings, Package, FileText, Zap, AlertCircle,
  CheckCircle2, Clock
} from 'lucide-react';
import { OdooProvider, useOdoo } from './services/context';
import './index.css';

const StatCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: number | string;
}> = ({ icon, label, value }) => (
  <div className="odoo-stat-card">
    <div className="odoo-stat-icon">{icon}</div>
    <div className="odoo-stat-info">
      <span className="odoo-stat-value">{value}</span>
      <span className="odoo-stat-label">{label}</span>
    </div>
  </div>
);

const OdooContent: React.FC = () => {
  const { t } = useTranslation('odoo');
  const { tenantInfo, isLoading, error, refreshTenant, provisionOdoo, stats, syncStatus, triggerSync } = useOdoo();
  const [isProvisioning, setIsProvisioning] = useState(false);

  if (isLoading) {
    return (
      <div className="odoo-loading">
        <div className="odoo-spinner" />
        <p>{t('dashboard.loading')}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="odoo-error">
        <AlertCircle size={48} style={{ marginBottom: '1rem', opacity: 0.6 }} />
        <h2>{t('dashboard.errorTitle')}</h2>
        <p>{error}</p>
        <button className="odoo-btn odoo-btn-primary" onClick={refreshTenant}>
          {t('dashboard.retry')}
        </button>
      </div>
    );
  }

  if (!tenantInfo) {
    const handleProvision = async () => {
      setIsProvisioning(true);
      try {
        await provisionOdoo();
      } finally {
        setIsProvisioning(false);
      }
    };

    return (
      <div className="odoo-provision">
        <Building2 size={64} style={{ marginBottom: '1.5rem', opacity: 0.6 }} />
        <h2>{t('dashboard.notConfiguredTitle')}</h2>
        <p>{t('dashboard.notConfiguredLead')}</p>
        <p style={{ fontSize: '0.9rem', opacity: 0.8, marginBottom: '1.5rem' }}>
          {t('dashboard.notConfiguredHint')}
        </p>
        <button
          className="odoo-btn odoo-btn-primary"
          onClick={handleProvision}
          disabled={isProvisioning}
        >
          {isProvisioning ? (
            <>
              <RefreshCw size={16} className="animate-spin" style={{ marginRight: '0.5rem' }} />
              {t('dashboard.provisioningBtn')}
            </>
          ) : (
            <>
              <Settings size={16} style={{ marginRight: '0.5rem' }} />
              {t('dashboard.provisionCta')}
            </>
          )}
        </button>
      </div>
    );
  }

  if (tenantInfo.status === 'provisioning') {
    return (
      <div className="odoo-loading">
        <div className="odoo-spinner" />
        <p>{t('dashboard.provisioningTitle')}</p>
        <p>{t('dashboard.provisioningHint')}</p>
      </div>
    );
  }

  // Use SSO URL if available, fall back to regular Odoo URL
  const odooLink = tenantInfo.odooLoginUrl || tenantInfo.odooUrl;

  return (
    <div className="odoo-content">
      {/* Stats */}
      <div className="odoo-stats-grid">
        <StatCard
          icon={<Package size={20} />}
          label={t('dashboard.statProducts')}
          value={stats?.products ?? '—'}
        />
        <StatCard
          icon={<Building2 size={20} />}
          label={t('dashboard.statAssets')}
          value={stats?.assets ?? '—'}
        />
        <StatCard
          icon={<FileText size={20} />}
          label={t('dashboard.statInvoices')}
          value={stats?.invoices ?? '—'}
        />
        <StatCard
          icon={<Zap size={20} />}
          label={t('dashboard.statEnergy')}
          value={stats?.energyInstallations ?? '—'}
        />
      </div>

      {/* Sync Status */}
      <div className="odoo-sync-panel">
        <div className="odoo-sync-status">
          {syncStatus === 'synced' ? (
            <CheckCircle2 size={16} style={{ color: '#22c55e' }} />
          ) : syncStatus === 'syncing' ? (
            <RefreshCw size={16} className="animate-spin" style={{ color: '#3b82f6' }} />
          ) : (
            <Clock size={16} style={{ color: '#f59e0b' }} />
          )}
          <span>
            {syncStatus === 'synced'
              ? t('dashboard.syncSynced')
              : syncStatus === 'syncing'
                ? t('dashboard.syncSyncing')
                : t('dashboard.syncNeeded')}
          </span>
          {stats?.pendingSync ? (
            <span className="odoo-pending-badge">
              {t('dashboard.pending', { count: stats.pendingSync })}
            </span>
          ) : null}
        </div>
        <button
          className="odoo-btn odoo-btn-secondary"
          onClick={triggerSync}
          disabled={syncStatus === 'syncing'}
        >
          <RefreshCw size={14} />
          {t('dashboard.syncNow')}
        </button>
      </div>

      {/* Open Odoo */}
      <div className="odoo-actions">
        <a
          href={odooLink}
          target="_blank"
          rel="noopener noreferrer"
          className="odoo-btn odoo-btn-primary odoo-btn-large"
        >
          <ExternalLink size={18} style={{ marginRight: '0.5rem' }} />
          {t('dashboard.openOdoo')}
        </a>

        {/* Quick links to specific Odoo sections */}
        <div className="odoo-quick-links">
          <a
            href={`${tenantInfo.odooUrl}#menu_id=sale.sale_menu_root`}
            target="_blank"
            rel="noopener noreferrer"
            className="odoo-quick-link"
          >
            <Sun size={14} />
            {t('dashboard.linkSales')}
          </a>
          <a
            href={`${tenantInfo.odooUrl}#menu_id=stock.menu_stock_root`}
            target="_blank"
            rel="noopener noreferrer"
            className="odoo-quick-link"
          >
            <Leaf size={14} />
            {t('dashboard.linkInventory')}
          </a>
          <a
            href={`${tenantInfo.odooUrl}#menu_id=account.menu_finance`}
            target="_blank"
            rel="noopener noreferrer"
            className="odoo-quick-link"
          >
            <FileText size={14} />
            {t('dashboard.linkAccounting')}
          </a>
        </div>
      </div>

      {/* Module info */}
      {tenantInfo.energyModulesEnabled && (
        <div className="odoo-info-panel">
          <Zap size={14} style={{ color: '#f59e0b' }} />
          <span>{t('dashboard.energyModules')}</span>
        </div>
      )}
    </div>
  );
};

const OdooHeader: React.FC = () => {
  const { t } = useTranslation('odoo');
  const { tenantInfo } = useOdoo();

  return (
    <header className="odoo-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <Building2 size={28} />
        <div>
          <h1>{t('dashboard.headerTitle')}</h1>
          {tenantInfo && (
            <span style={{ fontSize: '0.875rem', opacity: 0.8 }}>
              {tenantInfo.name}
            </span>
          )}
        </div>
      </div>
    </header>
  );
};

const App: React.FC = () => {
  return (
    <OdooProvider>
      <div className="odoo-module">
        <OdooHeader />
        <OdooContent />
      </div>
    </OdooProvider>
  );
};

export default App;

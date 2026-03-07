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
  const { tenantInfo, isLoading, error, refreshTenant, provisionOdoo, stats, syncStatus, triggerSync } = useOdoo();
  const [isProvisioning, setIsProvisioning] = useState(false);

  if (isLoading) {
    return (
      <div className="odoo-loading">
        <div className="odoo-spinner" />
        <p>Connecting to your Odoo instance...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="odoo-error">
        <AlertCircle size={48} style={{ marginBottom: '1rem', opacity: 0.6 }} />
        <h2>Connection Error</h2>
        <p>{error}</p>
        <button className="odoo-btn odoo-btn-primary" onClick={refreshTenant}>
          Retry Connection
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
        <h2>Odoo ERP Not Configured</h2>
        <p>Your organization does not have an Odoo instance yet.</p>
        <p style={{ fontSize: '0.9rem', opacity: 0.8, marginBottom: '1.5rem' }}>
          Click below to provision your dedicated Odoo ERP with farm management,
          energy community modules, and NGSI-LD synchronization.
        </p>
        <button
          className="odoo-btn odoo-btn-primary"
          onClick={handleProvision}
          disabled={isProvisioning}
        >
          {isProvisioning ? (
            <>
              <RefreshCw size={16} className="animate-spin" style={{ marginRight: '0.5rem' }} />
              Provisioning...
            </>
          ) : (
            <>
              <Settings size={16} style={{ marginRight: '0.5rem' }} />
              Provision Odoo ERP
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
        <p>Your Odoo instance is being provisioned...</p>
        <p>This may take a few minutes.</p>
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
          label="Products"
          value={stats?.products ?? '—'}
        />
        <StatCard
          icon={<Building2 size={20} />}
          label="Assets"
          value={stats?.assets ?? '—'}
        />
        <StatCard
          icon={<FileText size={20} />}
          label="Invoices"
          value={stats?.invoices ?? '—'}
        />
        <StatCard
          icon={<Zap size={20} />}
          label="Energy Installations"
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
            {syncStatus === 'synced' ? 'Synced with Nekazari' :
             syncStatus === 'syncing' ? 'Syncing...' :
             'Sync needed'}
          </span>
          {stats?.pendingSync ? (
            <span className="odoo-pending-badge">{stats.pendingSync} pending</span>
          ) : null}
        </div>
        <button
          className="odoo-btn odoo-btn-secondary"
          onClick={triggerSync}
          disabled={syncStatus === 'syncing'}
        >
          <RefreshCw size={14} />
          Sync Now
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
          Open Odoo ERP
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
            Sales
          </a>
          <a
            href={`${tenantInfo.odooUrl}#menu_id=stock.menu_stock_root`}
            target="_blank"
            rel="noopener noreferrer"
            className="odoo-quick-link"
          >
            <Leaf size={14} />
            Inventory
          </a>
          <a
            href={`${tenantInfo.odooUrl}#menu_id=account.menu_finance`}
            target="_blank"
            rel="noopener noreferrer"
            className="odoo-quick-link"
          >
            <FileText size={14} />
            Accounting
          </a>
        </div>
      </div>

      {/* Module info */}
      {tenantInfo.energyModulesEnabled && (
        <div className="odoo-info-panel">
          <Zap size={14} style={{ color: '#f59e0b' }} />
          <span>Energy community modules enabled</span>
        </div>
      )}
    </div>
  );
};

const OdooHeader: React.FC = () => {
  const { tenantInfo } = useOdoo();

  return (
    <header className="odoo-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <Building2 size={28} />
        <div>
          <h1>Odoo ERP</h1>
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

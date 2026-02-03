/**
 * Nekazari Odoo ERP Module - Main Application
 *
 * This module provides multitenant Odoo ERP integration for Nekazari platform.
 * Each tenant gets their own isolated Odoo database (Multi-DB architecture).
 *
 * Features:
 * - Farm management (products, parcels, harvests)
 * - Energy community management (Som Comunitats modules)
 * - Solar installation tracking
 * - NGSI-LD entity synchronization
 * - N8N workflow integration
 * - Intelligence module predictions
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

import React, { useState, useCallback } from 'react';
import { Building2, Sun, Leaf, RefreshCw, ExternalLink, Settings } from 'lucide-react';
import { OdooProvider, useOdoo } from './services/context';
import './index.css';

type TabType = 'erp' | 'energy' | 'farm' | 'settings';

const OdooContent: React.FC = () => {
  const { tenantInfo, isLoading, error, refreshTenant, provisionOdoo } = useOdoo();
  const [isProvisioning, setIsProvisioning] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('erp');
  const [iframeLoaded, setIframeLoaded] = useState(false);

  const getOdooUrl = useCallback(() => {
    if (!tenantInfo?.odooUrl) return '';

    const paths: Record<TabType, string> = {
      erp: '/web',
      energy: '/web#menu_id=energy_community',
      farm: '/web#menu_id=stock',
      settings: '/web#menu_id=settings'
    };

    return `${tenantInfo.odooUrl}${paths[activeTab]}`;
  }, [tenantInfo, activeTab]);

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

  const openOdooTab = (path: string = '') => {
    if (tenantInfo?.odooUrl) {
      window.open(tenantInfo.odooUrl + path, '_blank');
    }
  };

  return (
    <div className="odoo-content">
      <div className="odoo-dashboard">
        <div className="odoo-info-card">
          <h3>Your Odoo Instance</h3>
          <div className="odoo-info-row">
            <span className="odoo-info-label">Database:</span>
            <span className="odoo-info-value">{tenantInfo.odooDatabase}</span>
          </div>
          <div className="odoo-info-row">
            <span className="odoo-info-label">Status:</span>
            <span className={`odoo-info-status ${tenantInfo.status}`}>{tenantInfo.status}</span>
          </div>
          <div className="odoo-info-row">
            <span className="odoo-info-label">Energy Modules:</span>
            <span className="odoo-info-value">{tenantInfo.energyModulesEnabled ? 'Enabled' : 'Disabled'}</span>
          </div>
        </div>

        <div className="odoo-quick-actions">
          <h3>Quick Access</h3>
          <div className="odoo-action-grid">
            <button className="odoo-action-btn" onClick={() => openOdooTab('')}>
              <Building2 size={24} />
              <span>ERP Dashboard</span>
            </button>
            <button className="odoo-action-btn" onClick={() => openOdooTab('#menu_id=sale.sale_menu_root')}>
              <Sun size={24} />
              <span>Sales</span>
            </button>
            <button className="odoo-action-btn" onClick={() => openOdooTab('#menu_id=stock.menu_stock_root')}>
              <Leaf size={24} />
              <span>Inventory</span>
            </button>
            <button className="odoo-action-btn" onClick={() => openOdooTab('#menu_id=account.menu_finance')}>
              <Settings size={24} />
              <span>Accounting</span>
            </button>
          </div>
        </div>

        <div className="odoo-modules-card">
          <h3>Installed Modules</h3>
          <div className="odoo-modules-list">
            {tenantInfo.installedModules.length > 0 ? (
              tenantInfo.installedModules.map((mod, i) => (
                <span key={i} className="odoo-module-tag">{mod}</span>
              ))
            ) : (
              <span className="odoo-info-muted">Base modules installed</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const OdooHeader: React.FC = () => {
  const { tenantInfo, syncStatus, triggerSync } = useOdoo();

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

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div className="odoo-status">
          <span
            className={`odoo-status-dot ${
              syncStatus === 'syncing' ? 'syncing' :
              syncStatus === 'synced' ? 'connected' : 'disconnected'
            }`}
          />
          <span style={{ fontSize: '0.875rem' }}>
            {syncStatus === 'syncing' ? 'Syncing...' :
             syncStatus === 'synced' ? 'Synced' : 'Sync needed'}
          </span>
        </div>

        <button
          className="odoo-nav-btn"
          onClick={triggerSync}
          disabled={syncStatus === 'syncing'}
          title="Sync with Nekazari"
        >
          <RefreshCw size={16} className={syncStatus === 'syncing' ? 'animate-spin' : ''} />
        </button>

        {tenantInfo?.odooUrl && (
          <a
            href={tenantInfo.odooUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="odoo-nav-btn"
            title="Open in new tab"
          >
            <ExternalLink size={16} />
          </a>
        )}
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

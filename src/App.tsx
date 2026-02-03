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
  const { tenantInfo, isLoading, error, refreshTenant } = useOdoo();
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
    return (
      <div className="odoo-error">
        <h2>Odoo Not Provisioned</h2>
        <p>Your tenant does not have an Odoo instance yet.</p>
        <p>Please contact your administrator to provision Odoo for your organization.</p>
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

  return (
    <div className="odoo-content">
      <nav className="odoo-nav">
        <button
          className={`odoo-nav-btn ${activeTab === 'erp' ? 'active' : ''}`}
          onClick={() => setActiveTab('erp')}
        >
          <Building2 size={16} style={{ marginRight: '0.5rem' }} />
          ERP Dashboard
        </button>
        <button
          className={`odoo-nav-btn ${activeTab === 'energy' ? 'active' : ''}`}
          onClick={() => setActiveTab('energy')}
        >
          <Sun size={16} style={{ marginRight: '0.5rem' }} />
          Energy
        </button>
        <button
          className={`odoo-nav-btn ${activeTab === 'farm' ? 'active' : ''}`}
          onClick={() => setActiveTab('farm')}
        >
          <Leaf size={16} style={{ marginRight: '0.5rem' }} />
          Farm
        </button>
        <button
          className={`odoo-nav-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          <Settings size={16} style={{ marginRight: '0.5rem' }} />
          Settings
        </button>
      </nav>

      <div className="odoo-iframe-container">
        {!iframeLoaded && (
          <div className="odoo-loading">
            <div className="odoo-spinner" />
            <p>Loading Odoo...</p>
          </div>
        )}
        <iframe
          className="odoo-iframe"
          src={getOdooUrl()}
          title="Odoo ERP"
          onLoad={() => setIframeLoaded(true)}
          style={{ display: iframeLoaded ? 'block' : 'none' }}
        />
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

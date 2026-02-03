/**
 * Nekazari Odoo ERP Module - React Context
 *
 * Provides global state management for Odoo integration.
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { odooApi, TenantOdooInfo, OdooStats } from './api';

type SyncStatus = 'idle' | 'syncing' | 'synced' | 'error';

interface OdooContextType {
  tenantInfo: TenantOdooInfo | null;
  isLoading: boolean;
  error: string | null;
  syncStatus: SyncStatus;
  stats: OdooStats | null;

  refreshTenant: () => Promise<void>;
  triggerSync: () => Promise<void>;
  provisionOdoo: () => Promise<void>;
}

const OdooContext = createContext<OdooContextType | null>(null);

interface OdooProviderProps {
  children: ReactNode;
}

export const OdooProvider: React.FC<OdooProviderProps> = ({ children }) => {
  const [tenantInfo, setTenantInfo] = useState<TenantOdooInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle');
  const [stats, setStats] = useState<OdooStats | null>(null);

  const refreshTenant = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const info = await odooApi.getTenantInfo();
      setTenantInfo(info);

      if (info.status === 'active') {
        const statsData = await odooApi.getStats();
        setStats(statsData);

        const syncStatusData = await odooApi.getSyncStatus();
        setSyncStatus(syncStatusData.lastSync ? 'synced' : 'idle');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect to Odoo';
      setError(message);
      setTenantInfo(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const triggerSync = useCallback(async () => {
    if (syncStatus === 'syncing') return;

    setSyncStatus('syncing');

    try {
      const result = await odooApi.triggerSync();

      if (result.success) {
        setSyncStatus('synced');
        // Refresh stats after sync
        const statsData = await odooApi.getStats();
        setStats(statsData);
      } else {
        setSyncStatus('error');
        console.error('Sync errors:', result.errors);
      }
    } catch (err) {
      setSyncStatus('error');
      console.error('Sync failed:', err);
    }
  }, [syncStatus]);

  const provisionOdoo = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const info = await odooApi.provisionTenant();
      setTenantInfo(info);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to provision Odoo';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    refreshTenant();
  }, [refreshTenant]);

  // Poll for provisioning status if needed
  useEffect(() => {
    if (tenantInfo?.status === 'provisioning') {
      const interval = setInterval(() => {
        refreshTenant();
      }, 10000); // Check every 10 seconds

      return () => clearInterval(interval);
    }
  }, [tenantInfo?.status, refreshTenant]);

  const value: OdooContextType = {
    tenantInfo,
    isLoading,
    error,
    syncStatus,
    stats,
    refreshTenant,
    triggerSync,
    provisionOdoo
  };

  return (
    <OdooContext.Provider value={value}>
      {children}
    </OdooContext.Provider>
  );
};

export const useOdoo = (): OdooContextType => {
  const context = useContext(OdooContext);

  if (!context) {
    throw new Error('useOdoo must be used within an OdooProvider');
  }

  return context;
};

export default OdooContext;

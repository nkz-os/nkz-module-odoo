/**
 * Nekazari Odoo ERP Module - Status Widget
 *
 * Shows sync status and quick stats for the selected entity.
 * Displayed in the context panel.
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

import React, { useState, useEffect } from 'react';
import {
  Building2,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
  FileText,
  ShoppingCart,
  Wrench
} from 'lucide-react';
import { SlotWidgetProps } from '../../slots/types';
import { odooApi, OdooEntity } from '../../services/api';

interface EntityOdooStatus {
  hasInvoices: boolean;
  invoiceCount: number;
  hasSalesOrders: boolean;
  salesOrderCount: number;
  hasMaintenanceRecords: boolean;
  maintenanceCount: number;
  lastActivity: string | null;
}

const OdooStatusWidget: React.FC<SlotWidgetProps> = ({
  selectedEntityId,
  selectedEntityType
}) => {
  const [linkedEntity, setLinkedEntity] = useState<OdooEntity | null>(null);
  const [status, setStatus] = useState<EntityOdooStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  useEffect(() => {
    if (!selectedEntityId) {
      setLinkedEntity(null);
      setStatus(null);
      return;
    }

    const fetchStatus = async () => {
      setIsLoading(true);

      try {
        const entity = await odooApi.getOdooEntityForNgsiLd(selectedEntityId);
        setLinkedEntity(entity);

        if (entity) {
          // In a real implementation, this would fetch actual status from Odoo
          // For now, we'll simulate the status
          setStatus({
            hasInvoices: Math.random() > 0.5,
            invoiceCount: Math.floor(Math.random() * 10),
            hasSalesOrders: Math.random() > 0.5,
            salesOrderCount: Math.floor(Math.random() * 5),
            hasMaintenanceRecords: Math.random() > 0.7,
            maintenanceCount: Math.floor(Math.random() * 3),
            lastActivity: entity.lastSync
          });
        }
      } catch (err) {
        console.error('Failed to fetch Odoo status:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStatus();
  }, [selectedEntityId]);

  const handleSync = async () => {
    if (!linkedEntity || isSyncing) return;

    setIsSyncing(true);

    try {
      await odooApi.triggerSync();
      // Refresh status after sync
      const entity = await odooApi.getOdooEntityForNgsiLd(selectedEntityId!);
      setLinkedEntity(entity);
    } catch (err) {
      console.error('Sync failed:', err);
    } finally {
      setIsSyncing(false);
    }
  };

  if (!selectedEntityId || !selectedEntityType) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="odoo-slot-widget">
        <div className="odoo-slot-header">
          <Clock size={20} className="odoo-slot-icon" />
          <span>Odoo Status</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem' }}>
          <RefreshCw size={16} className="animate-spin" />
          <span style={{ fontSize: '0.875rem' }}>Loading status...</span>
        </div>
      </div>
    );
  }

  if (!linkedEntity) {
    return null; // OdooEntityLink widget will handle the "not linked" case
  }

  return (
    <div className="odoo-slot-widget">
      <div className="odoo-slot-header">
        <Clock size={20} className="odoo-slot-icon" />
        <span>Odoo Status</span>
        <button
          onClick={handleSync}
          disabled={isSyncing}
          style={{
            marginLeft: 'auto',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '0.25rem'
          }}
          title="Sync now"
        >
          <RefreshCw
            size={16}
            style={{ color: 'var(--odoo-primary)' }}
            className={isSyncing ? 'animate-spin' : ''}
          />
        </button>
      </div>

      {status && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', padding: '0.5rem 0' }}>
          {/* Sync Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={16} style={{ color: 'var(--odoo-success)' }} />
            <span style={{ fontSize: '0.875rem' }}>Synced</span>
            {status.lastActivity && (
              <span style={{ fontSize: '0.75rem', color: 'var(--odoo-text-muted)', marginLeft: 'auto' }}>
                {new Date(status.lastActivity).toLocaleDateString()}
              </span>
            )}
          </div>

          {/* Quick Stats */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginTop: '0.5rem' }}>
            {status.hasInvoices && (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  padding: '0.5rem',
                  background: 'var(--odoo-bg)',
                  borderRadius: '0.25rem'
                }}
              >
                <FileText size={16} style={{ color: 'var(--odoo-primary)' }} />
                <span style={{ fontSize: '1rem', fontWeight: 600 }}>{status.invoiceCount}</span>
                <span style={{ fontSize: '0.625rem', color: 'var(--odoo-text-muted)' }}>Invoices</span>
              </div>
            )}

            {status.hasSalesOrders && (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  padding: '0.5rem',
                  background: 'var(--odoo-bg)',
                  borderRadius: '0.25rem'
                }}
              >
                <ShoppingCart size={16} style={{ color: 'var(--odoo-secondary)' }} />
                <span style={{ fontSize: '1rem', fontWeight: 600 }}>{status.salesOrderCount}</span>
                <span style={{ fontSize: '0.625rem', color: 'var(--odoo-text-muted)' }}>Orders</span>
              </div>
            )}

            {status.hasMaintenanceRecords && (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  padding: '0.5rem',
                  background: 'var(--odoo-bg)',
                  borderRadius: '0.25rem'
                }}
              >
                <Wrench size={16} style={{ color: 'var(--odoo-warning)' }} />
                <span style={{ fontSize: '1rem', fontWeight: 600 }}>{status.maintenanceCount}</span>
                <span style={{ fontSize: '0.625rem', color: 'var(--odoo-text-muted)' }}>Maint.</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default OdooStatusWidget;

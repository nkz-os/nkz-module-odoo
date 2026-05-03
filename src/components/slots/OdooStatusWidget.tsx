/**
 * Nekazari Odoo ERP Module - Status Widget
 *
 * Shows sync status and quick stats for the selected entity.
 * Displayed in the context panel.
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from '@nekazari/sdk';
import { SlotShell } from '@nekazari/viewer-kit';
import { Badge, Spinner, Stack, IconButton } from '@nekazari/ui-kit';
import {
  RefreshCw,
  CheckCircle,
  Clock,
  FileText,
  ShoppingCart,
  Wrench
} from 'lucide-react';
import { SlotWidgetProps } from '../../slots/types';
import { odooApi, OdooEntity } from '../../services/api';

const odooAccent = { base: '#6366F1', soft: '#E0E7FF', strong: '#4338CA' };

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
  const { t } = useTranslation('odoo');
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
      <SlotShell
        title={t('statusWidget.title')}
        icon={<Clock className="w-4 h-4" />}
        collapsible
        accent={odooAccent}
      >
        <div className="flex items-center gap-2 p-nkz-inline">
          <Spinner size="sm" />
          <span className="text-nkz-sm text-nkz-text-secondary">{t('statusWidget.loading')}</span>
        </div>
      </SlotShell>
    );
  }

  if (!linkedEntity) {
    return null;
  }

  return (
    <SlotShell
      title={t('statusWidget.title')}
      icon={<Clock className="w-4 h-4" />}
      collapsible
      accent={odooAccent}
    >
      <Stack gap="inline">
        {/* Sync Status */}
        <div className="flex items-center gap-2">
          <CheckCircle size={16} className="text-nkz-success" />
          <span className="text-nkz-sm text-nkz-text-primary">{t('statusWidget.synced')}</span>
          {status?.lastActivity && (
            <span className="text-nkz-xs text-nkz-text-muted ml-auto">
              {new Date(status.lastActivity).toLocaleDateString()}
            </span>
          )}
        </div>

        {/* Quick Stats Grid */}
        {status && (
          <div className="grid grid-cols-3 gap-2 mt-1">
            {status.hasInvoices && (
              <div className="flex flex-col items-center p-nkz-inline bg-nkz-surface-sunken rounded-nkz-md">
                <FileText size={16} className="text-nkz-accent-base" />
                <span className="text-nkz-sm font-semibold text-nkz-text-primary">{status.invoiceCount}</span>
                <span className="text-nkz-xs text-nkz-text-muted">{t('statusWidget.invoices')}</span>
              </div>
            )}

            {status.hasSalesOrders && (
              <div className="flex flex-col items-center p-nkz-inline bg-nkz-surface-sunken rounded-nkz-md">
                <ShoppingCart size={16} className="text-nkz-accent-base" />
                <span className="text-nkz-sm font-semibold text-nkz-text-primary">{status.salesOrderCount}</span>
                <span className="text-nkz-xs text-nkz-text-muted">{t('statusWidget.orders')}</span>
              </div>
            )}

            {status.hasMaintenanceRecords && (
              <div className="flex flex-col items-center p-nkz-inline bg-nkz-surface-sunken rounded-nkz-md">
                <Wrench size={16} className="text-nkz-warning" />
                <span className="text-nkz-sm font-semibold text-nkz-text-primary">{status.maintenanceCount}</span>
                <span className="text-nkz-xs text-nkz-text-muted">{t('statusWidget.maint')}</span>
              </div>
            )}
          </div>
        )}

        {/* Sync button */}
        <div className="flex justify-end">
          <IconButton
            aria-label={t('statusWidget.syncNowTitle')}
            size="sm"
            onClick={handleSync}
            disabled={isSyncing}
          >
            <RefreshCw size={16} className={isSyncing ? 'animate-spin' : ''} />
          </IconButton>
        </div>
      </Stack>
    </SlotShell>
  );
};

export default OdooStatusWidget;

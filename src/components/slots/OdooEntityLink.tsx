/**
 * Nekazari Odoo ERP Module - Entity Link Slot Widget
 *
 * Shows linked Odoo records for the selected NGSI-LD entity.
 * Displayed in the context panel when an entity is selected.
 */

import React, { useState, useEffect } from 'react';
import { Building2, ExternalLink, Plus, RefreshCw, Package, Zap, Tractor } from 'lucide-react';
import { useTranslation } from '@nekazari/sdk';
import { SlotShell } from '@nekazari/viewer-kit';
import { Button, Spinner, Badge, Stack } from '@nekazari/ui-kit';
import { SlotWidgetProps } from '../../slots/types';
import { odooApi, OdooEntity } from '../../services/api';

const odooAccent = { base: '#6366F1', soft: '#E0E7FF', strong: '#4338CA' };

const ENTITY_TYPE_ICONS: Record<string, React.ReactNode> = {
  AgriParcel: <Tractor size={16} />,
  Device: <Package size={16} />,
  EnergyMeter: <Zap size={16} />,
  SolarPanel: <Zap size={16} />,
  Building: <Building2 size={16} />
};

const ENTITY_TYPE_ODOO_MODEL: Record<string, string> = {
  AgriParcel: 'product.template',
  Device: 'maintenance.equipment',
  EnergyMeter: 'energy.meter',
  SolarPanel: 'energy.installation',
  Building: 'res.partner'
};

const OdooEntityLink: React.FC<SlotWidgetProps> = ({
  selectedEntityId,
  selectedEntityType
}) => {
  const { t } = useTranslation('odoo');
  const [linkedEntity, setLinkedEntity] = useState<OdooEntity | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedEntityId) {
      setLinkedEntity(null);
      return;
    }

    const fetchLinkedEntity = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const entity = await odooApi.getOdooEntityForNgsiLd(selectedEntityId);
        setLinkedEntity(entity);
      } catch (err) {
        setError(t('entityLink.errorFetch'));
        setLinkedEntity(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLinkedEntity();
  }, [selectedEntityId]);

  const handleCreateLink = async () => {
    if (!selectedEntityId || !selectedEntityType) return;

    setIsCreating(true);
    setError(null);

    try {
      const entity = await odooApi.createOdooEntityFromNgsiLd(
        selectedEntityId,
        selectedEntityType
      );
      setLinkedEntity(entity);
    } catch (err) {
      setError(t('entityLink.errorCreate'));
    } finally {
      setIsCreating(false);
    }
  };

  const handleOpenInOdoo = async () => {
    if (!linkedEntity) return;

    try {
      const { url } = await odooApi.openOdooEntity(
        linkedEntity.odooModel,
        linkedEntity.odooId
      );
      window.open(url, '_blank');
    } catch (err) {
      setError(t('entityLink.errorOpen'));
    }
  };

  if (!selectedEntityId || !selectedEntityType) {
    return null;
  }

  const icon = ENTITY_TYPE_ICONS[selectedEntityType] || <Package size={16} />;
  const expectedModel = ENTITY_TYPE_ODOO_MODEL[selectedEntityType] || 'product.template';

  return (
    <SlotShell
      moduleId="odoo-erp"
      title={t('entityLink.title')}
      icon={<Building2 className="w-4 h-4" />}
      collapsible
      accent={odooAccent}
    >
      {isLoading ? (
        <div className="flex items-center gap-2 p-nkz-inline">
          <Spinner size="sm" />
          <span className="text-nkz-sm text-nkz-text-secondary">{t('entityLink.loading')}</span>
        </div>
      ) : error ? (
        <Badge intent="negative" className="p-nkz-inline">
          {error}
        </Badge>
      ) : linkedEntity ? (
        <Stack gap="tight">
          <div
            className="flex items-center justify-between p-nkz-inline bg-nkz-surface-sunken rounded-nkz-md hover:bg-nkz-surface transition-colors cursor-pointer"
            onClick={handleOpenInOdoo}
          >
            <div className="flex items-center gap-2">
              <span className="text-nkz-accent-base">{icon}</span>
              <div>
                <div className="text-nkz-sm font-medium text-nkz-text-primary">{linkedEntity.odooName}</div>
                <div className="text-nkz-xs text-nkz-text-muted">
                  {linkedEntity.odooModel} #{linkedEntity.odooId}
                </div>
              </div>
            </div>
            <ExternalLink size={16} className="text-nkz-text-muted" />
          </div>

          <div className="text-nkz-xs text-nkz-text-muted px-nkz-inline">
            {t('entityLink.lastSynced', {
              date: linkedEntity.lastSync
                ? new Date(linkedEntity.lastSync).toLocaleString()
                : t('entityLink.never'),
            })}
          </div>
        </Stack>
      ) : (
        <Stack gap="inline">
          <p className="text-nkz-sm text-nkz-text-muted">
            {t('entityLink.noRecord')}
          </p>
          <Button
            variant="primary"
            size="sm"
            onClick={handleCreateLink}
            disabled={isCreating}
            leadingIcon={isCreating ? <RefreshCw size={16} className="animate-spin" /> : <Plus size={16} />}
          >
            {isCreating ? t('entityLink.creating') : t('entityLink.createInOdoo', { model: expectedModel })}
          </Button>
        </Stack>
      )}
    </SlotShell>
  );
};

export default OdooEntityLink;

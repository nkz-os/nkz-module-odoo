/**
 * Nekazari Odoo ERP Module - Entity Link Slot Widget
 *
 * Shows linked Odoo records for the selected NGSI-LD entity.
 * Displayed in the context panel when an entity is selected.
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

import React, { useState, useEffect } from 'react';
import { Building2, ExternalLink, Plus, RefreshCw, Package, Zap, Tractor } from 'lucide-react';
import { SlotWidgetProps } from '../../slots/types';
import { odooApi, OdooEntity } from '../../services/api';

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
        setError('Failed to fetch Odoo link');
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
      setError('Failed to create Odoo record');
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
      setError('Failed to open in Odoo');
    }
  };

  if (!selectedEntityId || !selectedEntityType) {
    return null;
  }

  const icon = ENTITY_TYPE_ICONS[selectedEntityType] || <Package size={16} />;
  const expectedModel = ENTITY_TYPE_ODOO_MODEL[selectedEntityType] || 'product.template';

  return (
    <div className="odoo-slot-widget">
      <div className="odoo-slot-header">
        <Building2 size={20} className="odoo-slot-icon" />
        <span>Odoo ERP</span>
      </div>

      {isLoading ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem' }}>
          <RefreshCw size={16} className="animate-spin" />
          <span>Loading...</span>
        </div>
      ) : error ? (
        <div style={{ color: 'var(--odoo-danger)', padding: '0.5rem', fontSize: '0.875rem' }}>
          {error}
        </div>
      ) : linkedEntity ? (
        <div className="odoo-link-list">
          <div className="odoo-link-item" onClick={handleOpenInOdoo}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {icon}
              <div>
                <div style={{ fontWeight: 500 }}>{linkedEntity.odooName}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--odoo-text-muted)' }}>
                  {linkedEntity.odooModel} #{linkedEntity.odooId}
                </div>
              </div>
            </div>
            <ExternalLink size={16} style={{ color: 'var(--odoo-text-muted)' }} />
          </div>

          <div style={{ fontSize: '0.75rem', color: 'var(--odoo-text-muted)', padding: '0.25rem 0.5rem' }}>
            Last synced: {linkedEntity.lastSync ? new Date(linkedEntity.lastSync).toLocaleString() : 'Never'}
          </div>
        </div>
      ) : (
        <div style={{ padding: '0.5rem' }}>
          <p style={{ fontSize: '0.875rem', marginBottom: '0.5rem', color: 'var(--odoo-text-muted)' }}>
            No Odoo record linked to this entity.
          </p>
          <button
            className="odoo-btn odoo-btn-primary"
            onClick={handleCreateLink}
            disabled={isCreating}
            style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
          >
            {isCreating ? (
              <>
                <RefreshCw size={16} className="animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Plus size={16} />
                Create in Odoo ({expectedModel})
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default OdooEntityLink;

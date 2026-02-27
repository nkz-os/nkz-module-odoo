/**
 * Odoo ERP Module - Main page for the /odoo route (host).
 * Shows a short description and a link to open Odoo in a new tab.
 * No iframe embed — Odoo runs on its own subdomain (URL from backend or host __ENV__).
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

import React, { useState } from 'react';
import { Building2, ExternalLink, Settings, RefreshCw } from 'lucide-react';
import { OdooProvider, useOdoo } from './services/context';
import './index.css';

const MODULE_DESCRIPTION =
  'Integración multitenant de Odoo ERP con Nekazari: gestión de explotación, ' +
  'comunidades energéticas (Som Comunitats), inventario, ventas y contabilidad. ' +
  'Cada organización dispone de su propia base de datos Odoo aislada.';

function OdooModulePageContent() {
  const { tenantInfo, isLoading, error, refreshTenant, provisionOdoo } = useOdoo();
  const [isProvisioning, setIsProvisioning] = useState(false);

  if (isLoading) {
    return (
      <div className="odoo-loading" style={{ minHeight: '280px' }}>
        <div className="odoo-spinner" />
        <p>Comprobando configuración de Odoo...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="odoo-error">
        <h2>Error de conexión</h2>
        <p>{error}</p>
        <button className="odoo-btn odoo-btn-primary" onClick={refreshTenant}>
          Reintentar
        </button>
      </div>
    );
  }

  const handleProvision = async () => {
    setIsProvisioning(true);
    try {
      await provisionOdoo();
    } finally {
      setIsProvisioning(false);
    }
  };

  const odooUrl =
    tenantInfo?.odooUrl ||
    (typeof window !== 'undefined' && (window as any).__ENV__?.ODOO_PUBLIC_URL) ||
    '';

  return (
    <div
      style={{
        maxWidth: 560,
        margin: '2rem auto',
        padding: '2rem',
        background: 'var(--odoo-card-bg)',
        borderRadius: 12,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
        border: '1px solid var(--odoo-border)',
      }}
    >
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <Building2 size={48} style={{ color: 'var(--odoo-primary)', marginBottom: '0.75rem' }} />
        <h1 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--odoo-text)', marginBottom: '0.5rem' }}>
          Odoo ERP
        </h1>
        <p style={{ fontSize: '0.9375rem', color: 'var(--odoo-text-muted)', lineHeight: 1.5 }}>
          {MODULE_DESCRIPTION}
        </p>
      </div>

      {!tenantInfo ? (
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--odoo-text-muted)', marginBottom: '1rem' }}>
            Su organización aún no tiene una instancia de Odoo. Provisiónela para acceder al ERP.
          </p>
          <button
            className="odoo-btn odoo-btn-primary"
            onClick={handleProvision}
            disabled={isProvisioning}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
          >
            {isProvisioning ? (
              <>
                <RefreshCw size={18} className="animate-spin" />
                Provisionando...
              </>
            ) : (
              <>
                <Settings size={18} />
                Configurar Odoo ERP
              </>
            )}
          </button>
        </div>
      ) : tenantInfo.status === 'provisioning' ? (
        <div className="odoo-loading" style={{ minHeight: '120px' }}>
          <div className="odoo-spinner" />
          <p>Su instancia de Odoo se está creando...</p>
          <p style={{ fontSize: '0.875rem', opacity: 0.8 }}>Puede tardar unos minutos.</p>
        </div>
      ) : odooUrl ? (
        <div style={{ textAlign: 'center' }}>
          <a
            href={odooUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="odoo-btn odoo-btn-primary"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              textDecoration: 'none',
            }}
          >
            <ExternalLink size={18} />
            Abrir Odoo ERP
          </a>
          <p style={{ fontSize: '0.8125rem', color: 'var(--odoo-text-muted)', marginTop: '1rem' }}>
            Se abrirá Odoo en una nueva pestaña ({tenantInfo.odooDatabase || 'su base de datos'}).
          </p>
        </div>
      ) : (
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--odoo-text-muted)' }}>
            URL de Odoo no configurada. Configure ODOO_URL en el backend o ODOO_PUBLIC_URL en el host.
          </p>
        </div>
      )}
    </div>
  );
}

/** Main component for the host route /odoo — description + link to Odoo (no embed). */
export default function OdooModulePage() {
  return (
    <OdooProvider>
      <div className="odoo-module" style={{ minHeight: '100%' }}>
        <OdooModulePageContent />
      </div>
    </OdooProvider>
  );
}

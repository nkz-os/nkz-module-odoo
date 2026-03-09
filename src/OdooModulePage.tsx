/**
 * Odoo ERP Module - Main page for the /odoo route (host).
 * Shows description, features, and a link to open Odoo in a new tab.
 * No iframe embed — Odoo runs on its own subdomain (URL from backend or host __ENV__).
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

import React, { useState } from 'react';
import {
  Building2,
  ExternalLink,
  Settings,
  RefreshCw,
  Package,
  BarChart3,
  Zap,
  FileText,
  Database,
  Shield,
} from 'lucide-react';
import { OdooProvider, useOdoo } from './services/context';
import './index.css';

const MODULE_DESCRIPTION =
  'Integración multitenant de Odoo ERP con Nekazari: gestión de explotación, ' +
  'comunidades energéticas (Som Comunitats), inventario, ventas y contabilidad. ' +
  'Cada organización dispone de su propia base de datos Odoo aislada.';

const FEATURES = [
  { icon: Database, label: 'Una base de datos por organización (multi-tenant)' },
  { icon: Package, label: 'Inventario, ventas y contabilidad' },
  { icon: Zap, label: 'Comunidades energéticas y autoconsumo (Som Comunitats)' },
  { icon: BarChart3, label: 'Sincronización con NGSI-LD y datos de la plataforma' },
  { icon: FileText, label: 'Facturación e informes integrados' },
  { icon: Shield, label: 'Acceso seguro con Keycloak (SSO)' },
];

function OdooModulePageContent() {
  const { tenantInfo, isLoading, error, refreshTenant, provisionOdoo } = useOdoo();
  const [isProvisioning, setIsProvisioning] = useState(false);

  if (isLoading) {
    return (
      <div className="odoo-module-page">
        <div className="odoo-module-page__loading">
          <div className="odoo-spinner" />
          <p>Comprobando configuración de Odoo...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="odoo-module-page">
        <div className="odoo-module-page__card odoo-module-page__card--error">
          <h2>Error de conexión</h2>
          <p>{error}</p>
          <button className="odoo-btn odoo-btn-primary" onClick={refreshTenant}>
            Reintentar
          </button>
        </div>
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

  // Prefer SSO login URL (auto-login via Keycloak) over plain Odoo URL
  const odooUrl =
    tenantInfo?.odooUrl ||
    (typeof window !== 'undefined' && (window as any).__ENV__?.ODOO_PUBLIC_URL) ||
    '';

  const loginUrl = tenantInfo?.odooLoginUrl || odooUrl;
  const hasSso = Boolean(tenantInfo?.odooLoginUrl);

  return (
    <div className="odoo-module-page">
      <div className="odoo-module-page__hero">
        <div className="odoo-module-page__hero-icon">
          <Building2 size={56} />
        </div>
        <h1 className="odoo-module-page__title">Odoo ERP</h1>
        <p className="odoo-module-page__lead">{MODULE_DESCRIPTION}</p>
      </div>

      <div className="odoo-module-page__features">
        <h2 className="odoo-module-page__features-title">Qué incluye</h2>
        <ul className="odoo-module-page__features-list">
          {FEATURES.map(({ icon: Icon, label }) => (
            <li key={label} className="odoo-module-page__feature">
              <Icon size={20} className="odoo-module-page__feature-icon" />
              <span>{label}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="odoo-module-page__card odoo-module-page__card--cta">
        {!tenantInfo ? (
          <>
            <p className="odoo-module-page__card-text">
              Su organización aún no tiene una instancia de Odoo. Provisiónela para acceder al ERP
              con su propia base de datos aislada.
            </p>
            <button
              className="odoo-btn odoo-btn-primary odoo-module-page__btn"
              onClick={handleProvision}
              disabled={isProvisioning}
            >
              {isProvisioning ? (
                <>
                  <RefreshCw size={20} className="animate-spin" />
                  Provisionando...
                </>
              ) : (
                <>
                  <Settings size={20} />
                  Configurar Odoo ERP
                </>
              )}
            </button>
          </>
        ) : tenantInfo.status === 'provisioning' ? (
          <div className="odoo-module-page__loading">
            <div className="odoo-spinner" />
            <p>Su instancia de Odoo se está creando...</p>
            <p className="odoo-module-page__hint">Puede tardar unos minutos.</p>
          </div>
        ) : loginUrl ? (
          <>
            <p className="odoo-module-page__card-text">
              Su instancia está lista.{' '}
              {hasSso
                ? 'Acceda directamente con su cuenta de la plataforma.'
                : 'Ábrala en una nueva pestaña para trabajar con el ERP.'}
            </p>
            <a
              href={loginUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="odoo-btn odoo-btn-primary odoo-module-page__btn"
            >
              <ExternalLink size={20} />
              {hasSso ? 'Entrar en Odoo ERP' : 'Abrir Odoo ERP'}
            </a>
            <p className="odoo-module-page__hint">
              Base de datos: {tenantInfo.odooDatabase || 'su base de datos'}
              {hasSso && <span className="odoo-module-page__sso-badge"> · SSO activo</span>}
            </p>
          </>
        ) : (
          <p className="odoo-module-page__card-text">
            URL de Odoo no configurada. Configure ODOO_URL en el backend o ODOO_PUBLIC_URL en el
            host.
          </p>
        )}
      </div>
    </div>
  );
}

/** Main component for the host route /odoo — description + features + link to Odoo (no embed). */
export default function OdooModulePage() {
  return (
    <OdooProvider>
      <div className="odoo-module odoo-module-page__wrap">
        <OdooModulePageContent />
      </div>
    </OdooProvider>
  );
}

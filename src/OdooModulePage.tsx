/**
 * Odoo ERP Module - Main page for the /odoo route (host).
 * Shows description, features, and a link to open Odoo in a new tab.
 * No iframe embed — Odoo runs on its own subdomain (URL from backend or host __ENV__).
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

import { useMemo, useState } from 'react';
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
import { useTranslation } from '@nekazari/sdk';
import { OdooProvider, useOdoo } from './services/context';

function OdooModulePageContent() {
  const { t } = useTranslation('odoo');
  const { tenantInfo, isLoading, error, refreshTenant, provisionOdoo } = useOdoo();
  const [isProvisioning, setIsProvisioning] = useState(false);

  const features = useMemo(
    () => [
      { icon: Database, label: t('main.featureDb') },
      { icon: Package, label: t('main.featureInvoicing') },
      { icon: Zap, label: t('main.featureEnergy') },
      { icon: BarChart3, label: t('main.featureNgsi') },
      { icon: FileText, label: t('main.featureReports') },
      { icon: Shield, label: t('main.featureSso') },
    ],
    [t]
  );

  if (isLoading) {
    return (
      <div className="odoo-module-page">
        <div className="odoo-module-page__loading">
          <div className="odoo-spinner" />
          <p>{t('main.loading')}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="odoo-module-page">
        <div className="odoo-module-page__card odoo-module-page__card--error">
          <h2>{t('main.errorTitle')}</h2>
          <p>{error}</p>
          <button className="odoo-btn odoo-btn-primary" onClick={refreshTenant}>
            {t('main.retry')}
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
        <h1 className="odoo-module-page__title">{t('main.heroTitle')}</h1>
        <p className="odoo-module-page__lead">{t('main.lead')}</p>
      </div>

      <div className="odoo-module-page__features">
        <h2 className="odoo-module-page__features-title">{t('main.featuresTitle')}</h2>
        <ul className="odoo-module-page__features-list">
          {features.map(({ icon: Icon, label }) => (
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
            <p className="odoo-module-page__card-text">{t('main.notProvisioned')}</p>
            <button
              className="odoo-btn odoo-btn-primary odoo-module-page__btn"
              onClick={handleProvision}
              disabled={isProvisioning}
            >
              {isProvisioning ? (
                <>
                  <RefreshCw size={20} className="animate-spin" />
                  {t('main.provisioningBtn')}
                </>
              ) : (
                <>
                  <Settings size={20} />
                  {t('main.provisionCta')}
                </>
              )}
            </button>
          </>
        ) : tenantInfo.status === 'provisioning' ? (
          <div className="odoo-module-page__loading">
            <div className="odoo-spinner" />
            <p>{t('main.provisioningTitle')}</p>
            <p className="odoo-module-page__hint">{t('main.provisioningHint')}</p>
          </div>
        ) : loginUrl ? (
          <>
            <p className="odoo-module-page__card-text">
              {hasSso ? t('main.readySso') : t('main.readyPlain')}
            </p>
            <a
              href={loginUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="odoo-btn odoo-btn-primary odoo-module-page__btn"
            >
              <ExternalLink size={20} />
              {hasSso ? t('main.enterOdoo') : t('main.openOdoo')}
            </a>
            <p className="odoo-module-page__hint">
              {t('main.database', {
                name: tenantInfo.odooDatabase || t('main.defaultDatabaseName'),
              })}
              {hasSso && <span className="odoo-module-page__sso-badge">{t('main.ssoBadge')}</span>}
            </p>
          </>
        ) : (
          <p className="odoo-module-page__card-text">{t('main.urlMissing')}</p>
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

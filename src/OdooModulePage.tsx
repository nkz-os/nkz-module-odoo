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
import { Button, Card, Spinner, Badge, EmptyState, Surface, Stack, Inline } from '@nekazari/ui-kit';
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
      <div className="p-nkz-section flex flex-col items-center gap-nkz-stack">
        <Spinner size="lg" />
        <p className="text-nkz-sm text-nkz-text-secondary">{t('main.loading')}</p>
      </div>
    );
  }

  if (error) {
    return (
      <Card padding="lg">
        <Stack gap="stack" align="center">
          <h2 className="text-nkz-lg font-semibold text-nkz-text-primary">{t('main.errorTitle')}</h2>
          <p className="text-nkz-sm text-nkz-text-secondary">{error}</p>
          <Button variant="primary" onClick={refreshTenant}>
            {t('main.retry')}
          </Button>
        </Stack>
      </Card>
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

  const loginUrl = tenantInfo?.odooLoginUrl || odooUrl;
  const hasSso = Boolean(tenantInfo?.odooLoginUrl);

  return (
    <Stack gap="section">
      {/* Hero */}
      <Surface variant="default" padding="section" radius="lg">
        <Stack gap="stack" align="center">
          <div className="text-nkz-accent-base">
            <Building2 size={56} />
          </div>
          <h1 className="text-nkz-2xl font-bold text-nkz-text-primary text-center">
            {t('main.heroTitle')}
          </h1>
          <p className="text-nkz-base text-nkz-text-secondary text-center max-w-2xl">
            {t('main.lead')}
          </p>
        </Stack>
      </Surface>

      {/* Features */}
      <Card padding="lg">
        <Stack gap="stack">
          <h2 className="text-nkz-lg font-semibold text-nkz-text-primary">
            {t('main.featuresTitle')}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-nkz-inline">
            {features.map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-nkz-inline p-nkz-inline bg-nkz-surface-sunken rounded-nkz-md"
              >
                <span className="text-nkz-accent-base">
                  <Icon size={20} />
                </span>
                <span className="text-nkz-sm text-nkz-text-primary">{label}</span>
              </div>
            ))}
          </div>
        </Stack>
      </Card>

      {/* CTA / Status Card */}
      <Card padding="lg">
        <Stack gap="stack" align="center">
          {!tenantInfo ? (
            <>
              <p className="text-nkz-sm text-nkz-text-secondary text-center">
                {t('main.notProvisioned')}
              </p>
              <Button
                variant="primary"
                size="lg"
                onClick={handleProvision}
                disabled={isProvisioning}
                leadingIcon={
                  isProvisioning ? (
                    <RefreshCw size={20} className="animate-spin" />
                  ) : (
                    <Settings size={20} />
                  )
                }
              >
                {isProvisioning ? t('main.provisioningBtn') : t('main.provisionCta')}
              </Button>
            </>
          ) : tenantInfo.status === 'provisioning' ? (
            <Stack gap="stack" align="center">
              <Spinner size="md" />
              <p className="text-nkz-base font-medium text-nkz-text-primary">
                {t('main.provisioningTitle')}
              </p>
              <p className="text-nkz-sm text-nkz-text-muted">
                {t('main.provisioningHint')}
              </p>
            </Stack>
          ) : loginUrl ? (
            <>
              <p className="text-nkz-sm text-nkz-text-secondary text-center">
                {hasSso ? t('main.readySso') : t('main.readyPlain')}
              </p>
              <Button
                variant="primary"
                size="lg"
                href={loginUrl}
                leadingIcon={<ExternalLink size={20} />}
              >
                {hasSso ? t('main.enterOdoo') : t('main.openOdoo')}
              </Button>
              <Inline gap="tight" align="center">
                <span className="text-nkz-xs text-nkz-text-muted">
                  {t('main.database', {
                    name: tenantInfo.odooDatabase || t('main.defaultDatabaseName'),
                  })}
                </span>
                {hasSso && (
                  <Badge intent="positive">{t('main.ssoBadge')}</Badge>
                )}
              </Inline>
            </>
          ) : (
            <p className="text-nkz-sm text-nkz-text-secondary text-center">
              {t('main.urlMissing')}
            </p>
          )}
        </Stack>
      </Card>
    </Stack>
  );
}

/** Main component for the host route /odoo — description + features + link to Odoo (no embed). */
export default function OdooModulePage() {
  return (
    <OdooProvider>
      <div className="p-nkz-section">
        <OdooModulePageContent />
      </div>
    </OdooProvider>
  );
}

/**
 * Nekazari Odoo ERP Module - API Client
 *
 * Handles communication with the Odoo orchestration backend.
 *
 * @author Kate Benetis <kate@robotika.cloud>
 * @company Robotika
 * @license AGPL-3.0
 */

export interface TenantOdooInfo {
  id: string;
  name: string;
  odooDatabase: string;
  odooUrl: string;
  status: 'active' | 'provisioning' | 'error';
  lastSync: string | null;
  energyModulesEnabled: boolean;
  installedModules: string[];
}

export interface OdooEntity {
  odooId: number;
  odooModel: string;
  odooName: string;
  ngsiLdId: string;
  ngsiLdType: string;
  lastSync: string;
}

export interface SyncResult {
  success: boolean;
  entitiesSynced: number;
  errors: string[];
  timestamp: string;
}

export interface OdooStats {
  products: number;
  assets: number;
  invoices: number;
  energyInstallations: number;
  pendingSync: number;
}

class OdooApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = this.resolveApiUrl();
  }

  /**
   * Resolve the API base URL. Prefer relative path so no domain is hardcoded.
   * Priority: host-injected config → VITE_API_URL → relative /api/odoo.
   */
  private resolveApiUrl(): string {
    if (typeof window === 'undefined') {
      return '/api/odoo';
    }

    const config = (window as any).__nekazariConfig;
    if (config?.apiUrl) {
      const base = String(config.apiUrl).replace(/\/+$/, '');
      return base ? `${base}/api/odoo` : '/api/odoo';
    }

    const envApiUrl = (import.meta as any).env?.VITE_API_URL;
    if (envApiUrl) {
      const base = String(envApiUrl).replace(/\/+$/, '');
      return base ? `${base}/api/odoo` : '/api/odoo';
    }

    return '/api/odoo';
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null;

    // 1. Try Keycloak instance (same as working vegetation-health module)
    const keycloakInstance = (window as any).keycloak;
    if (keycloakInstance?.token) {
      return keycloakInstance.token;
    }

    // 2. Try __nekazariAuthContext
    const authContext = (window as any).__nekazariAuthContext;
    if (authContext) {
      const token = typeof authContext.getToken === 'function' 
        ? authContext.getToken() 
        : authContext.token;
      if (token) return token;
    }

    // 3. Fallback to localStorage
    return localStorage.getItem('nkz_token') || localStorage.getItem('auth_token');
  }

  private getTenantId(): string | null {
    if (typeof window === 'undefined') return null;

    // 1. Try __nekazariAuthContext
    const authContext = (window as any).__nekazariAuthContext;
    if (authContext?.tenantId) {
      return authContext.tenantId;
    }

    // 2. Try to extract from token
    const token = this.getToken();
    if (token) {
      try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
          window.atob(base64)
            .split('')
            .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        );
        const decoded = JSON.parse(jsonPayload);
        const tenantId = decoded['tenant-id'] || decoded.tenant_id || decoded.tenantId || decoded.tenant;
        if (tenantId) return tenantId;
      } catch (e) {
        console.warn('[OdooApi] Failed to decode token for tenant', e);
      }
    }

    // 3. Fallback to localStorage
    return localStorage.getItem('nkz_tenant_id');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const tenantId = this.getTenantId();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...(tenantId && { 'X-Tenant-ID': tenantId })
    };

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        ...headers,
        ...(options.headers || {})
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.status}`);
    }

    return response.json();
  }

  // Tenant Management
  async getTenantInfo(): Promise<TenantOdooInfo> {
    return this.request('/tenant/info');
  }

  async provisionTenant(): Promise<TenantOdooInfo> {
    return this.request('/tenant/provision', { method: 'POST' });
  }

  async deleteTenantOdoo(): Promise<void> {
    return this.request('/tenant/delete', { method: 'DELETE' });
  }

  // Synchronization
  async triggerSync(): Promise<SyncResult> {
    return this.request('/sync/trigger', { method: 'POST' });
  }

  async getSyncStatus(): Promise<{ status: string; lastSync: string | null }> {
    return this.request('/sync/status');
  }

  async getEntityMappings(ngsiLdType?: string): Promise<OdooEntity[]> {
    const params = ngsiLdType ? `?type=${ngsiLdType}` : '';
    return this.request(`/sync/mappings${params}`);
  }

  // Entity Operations
  async getOdooEntityForNgsiLd(ngsiLdId: string): Promise<OdooEntity | null> {
    try {
      return await this.request(`/entity/by-ngsi/${encodeURIComponent(ngsiLdId)}`);
    } catch {
      return null;
    }
  }

  async createOdooEntityFromNgsiLd(ngsiLdId: string, ngsiLdType: string): Promise<OdooEntity> {
    return this.request('/entity/create-from-ngsi', {
      method: 'POST',
      body: JSON.stringify({ ngsiLdId, ngsiLdType })
    });
  }

  async openOdooEntity(odooModel: string, odooId: number): Promise<{ url: string }> {
    return this.request(`/entity/open/${odooModel}/${odooId}`);
  }

  // Statistics
  async getStats(): Promise<OdooStats> {
    return this.request('/stats');
  }

  // Energy Community specific
  async getEnergyInstallations(): Promise<any[]> {
    return this.request('/energy/installations');
  }

  async getEnergyProduction(installationId: number, dateFrom: string, dateTo: string): Promise<any> {
    return this.request(`/energy/production/${installationId}?from=${dateFrom}&to=${dateTo}`);
  }

  async getSelfConsumptionProjects(): Promise<any[]> {
    return this.request('/energy/selfconsumption');
  }

  // Health check
  async healthCheck(): Promise<{ status: string; odoo: string; database: string }> {
    return this.request('/health');
  }
}

export const odooApi = new OdooApiClient();

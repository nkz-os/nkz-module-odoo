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
    // In production, use the absolute API URL
    // In development, use proxy
    if (typeof window !== 'undefined' && window.location.hostname === 'nekazari.artotxiki.com') {
      this.baseUrl = 'https://nkz.artotxiki.com/api/odoo';
    } else {
      this.baseUrl = '/api/odoo';
    }
  }

  private getToken(): string | null {
    // Get token from global context injected by Nekazari host
    const auth = (window as any).__nekazariAuth;
    return auth?.token || localStorage.getItem('nkz_token');
  }

  private getTenantId(): string | null {
    const tenant = (window as any).__nekazariTenant;
    return tenant?.id || localStorage.getItem('nkz_tenant_id');
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

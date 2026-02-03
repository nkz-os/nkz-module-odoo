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
   * Resolve the API URL in a portable way.
   * Priority:
   * 1. Host-injected config (window.__nekazariConfig.apiUrl)
   * 2. Environment variable (import.meta.env.VITE_API_URL)
   * 3. Dynamic detection based on current domain
   * 4. Fallback to relative path (for local development with proxy)
   */
  private resolveApiUrl(): string {
    if (typeof window === 'undefined') {
      return '/api/odoo';
    }

    // 1. Check host-injected config
    const config = (window as any).__nekazariConfig;
    if (config?.apiUrl) {
      return `${config.apiUrl}/api/odoo`;
    }

    // 2. Check environment variable
    const envApiUrl = (import.meta as any).env?.VITE_API_URL;
    if (envApiUrl) {
      return `${envApiUrl}/api/odoo`;
    }

    // 3. Dynamic detection: if on a "frontend" domain, derive API domain
    const hostname = window.location.hostname;
    
    // Pattern: frontend at "app.domain.com" or "nekazari.domain.com" → API at "api.domain.com" or "nkz.domain.com"
    // This handles common patterns without hardcoding specific domains
    if (hostname !== 'localhost' && !hostname.startsWith('127.') && !hostname.startsWith('192.168.')) {
      // Extract the base domain (e.g., "artotxiki.com" from "nekazari.artotxiki.com")
      const parts = hostname.split('.');
      if (parts.length >= 2) {
        const baseDomain = parts.slice(-2).join('.');
        const subdomain = parts.slice(0, -2).join('.');
        
        // Common frontend → API subdomain mappings
        const apiSubdomainMap: Record<string, string> = {
          'nekazari': 'nkz',
          'app': 'api',
          'www': 'api',
          'frontend': 'api'
        };
        
        const apiSubdomain = apiSubdomainMap[subdomain] || 'api';
        return `https://${apiSubdomain}.${baseDomain}/api/odoo`;
      }
    }

    // 4. Fallback: relative path (works with dev proxy)
    return '/api/odoo';
  }

  private getToken(): string | null {
    // Get token from Nekazari host auth context
    // The host exposes authentication via window.__nekazariAuthContext
    const authContext = (window as any).__nekazariAuthContext;
    
    if (authContext) {
      // Try getToken() method first, then direct token property
      const token = typeof authContext.getToken === 'function' 
        ? authContext.getToken() 
        : authContext.token;
      if (token) return token;
    }
    
    // Fallback to localStorage for standalone testing
    return localStorage.getItem('nkz_token');
  }

  private getTenantId(): string | null {
    // Get tenant ID from Nekazari host auth context
    const authContext = (window as any).__nekazariAuthContext;
    
    if (authContext) {
      // Try getTenantId() method first, then direct tenantId property
      const tenantId = typeof authContext.getTenantId === 'function'
        ? authContext.getTenantId()
        : authContext.tenantId;
      if (tenantId) return tenantId;
    }
    
    // Fallback to localStorage for standalone testing
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

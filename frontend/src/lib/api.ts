const DJANGO_API = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') localStorage.setItem('auth_token', token);
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') return localStorage.getItem('auth_token');
    return null;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const token = this.getToken();
    const headers: HeadersInit = { 'Content-Type': 'application/json', ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const url = `${DJANGO_API}${endpoint}`;
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) { localStorage.removeItem('auth_token'); this.token = null; window.location.href = '/login'; }
    if (response.status === 204) return { success: true };
    return response.json();
  }

  async createSale(data: any) {
  return this.request('/sales/sales/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  }


  async login(username: string, password: string) {
    const data = await this.request('/auth/token/', { method: 'POST', body: JSON.stringify({ username, password }) });
    if (data.access) this.setToken(data.access);
    return data;
  }

  async getDashboardKPIs() { return this.request('/analytics/dashboard/'); }

  async getMedicines(params?: Record<string, string>) {
    let url = '/medicines/';
    if (params) url += '?' + new URLSearchParams(params).toString();
    return this.request(url);
  }

  async createMedicine(data: any) { return this.request('/medicines/', { method: 'POST', body: JSON.stringify(data) }); }
  async updateMedicine(id: string, data: any) { return this.request(`/medicines/${id}/`, { method: 'PUT', body: JSON.stringify(data) }); }
  async deleteMedicine(id: string) { return this.request(`/medicines/${id}/`, { method: 'DELETE' }); }
  async getSales() { return this.request('/sales/sales/'); }
  async predictSales(medicineId: string, daysAhead: number = 7) { return this.request('/ai/predict/', { method: 'POST', body: JSON.stringify({ medicine_id: medicineId, days_ahead: daysAhead }) }); }
  async getSeasonalAnalysis() { return this.request('/ai/seasonal/'); }
  async chatWithAI(message: string) { return this.request('/ai/chat/', { method: 'POST', body: JSON.stringify({ message }) }); }
}

export const api = new ApiClient();

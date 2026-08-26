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
    if (response.status === 401) {
      localStorage.removeItem('auth_token');
      this.token = null;
      window.location.href = '/login';
      throw new Error('Non authentifié');
    }
    if (response.status === 204) return { success: true };
    return response.json();
  }

  // ========== Authentification ==========
  async login(username: string, password: string) {
    const data = await this.request('/auth/token/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    if (data.access) this.setToken(data.access);
    return data;
  }

  async getMe() {
    return this.request('/auth/me/');
  }

  // ========== Onboarding ==========
  async completeOnboarding() {
    return this.request('/auth/onboarding/complete/', { method: 'POST' });
  }

  // ========== Utilisateurs ==========
  async getUsers() {
    return this.request('/auth/users/');
  }

  async createUser(data: any) {
    return this.request('/auth/users/', { method: 'POST', body: JSON.stringify(data) });
  }

  async updateUser(id: number, data: any) {
    return this.request(`/auth/users/${id}/`, { method: 'PATCH', body: JSON.stringify(data) });
  }

  async deleteUser(id: number) {
    return this.request(`/auth/users/${id}/`, { method: 'DELETE' });
  }

  async activateUser(id: number) {
    return this.request(`/auth/users/${id}/activate/`, { method: 'POST' });
  }

  // ========== Profil utilisateur ==========
  async updateMe(data: any) {
    return this.request('/auth/me/', { method: 'PUT', body: JSON.stringify(data) });
  }

  async changePassword(data: any) {
    return this.request('/auth/change-password/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }



  async getInventorySummary() {
    return this.request('/inventory/summary/');
  }


  async uploadPhoto(formData: FormData) {
    const token = this.getToken();
    if (!token) throw new Error('Non authentifié');
    const url = `${DJANGO_API}/auth/upload-photo/`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    if (!response.ok) {
      throw new Error('Erreur lors de l\'upload');
    }
    return response.json();
  }

  // ========== Médicaments ==========
  async getMedicines(params?: Record<string, string>) {
    let url = '/medicines/';
    if (params) url += '?' + new URLSearchParams(params).toString();
    return this.request(url);
  }

  async createMedicine(data: any) {
    return this.request('/medicines/', { method: 'POST', body: JSON.stringify(data) });
  }

  async updateMedicine(id: string, data: any) {
    return this.request(`/medicines/${id}/`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteMedicine(id: string) {
    return this.request(`/medicines/${id}/`, { method: 'DELETE' });
  }

  // ========== Catégories ==========
  async getCategories() {
    return this.request('/categories/');
  }

  // ========== Ventes ==========
  async getSales() {
    return this.request('/sales/sales/');
  }

  async createSale(data: any) {
    return this.request('/sales/sales/', { method: 'POST', body: JSON.stringify(data) });
  }

  // ========== Analytics / Dashboard ==========
  async getDashboardKPIs() {
    return this.request('/analytics/dashboard/');
  }

  async getSalesCharts() {
    return this.request('/analytics/charts/');
  }

  async getTodaySales() {
    return this.request('/analytics/today-sales/');
  }

  async getOutOfStock() {
    return this.request('/analytics/out-of-stock/');
  }

  async getLowStock() {
    return this.request('/analytics/low-stock/');
  }

  async getExpiringSoon() {
    return this.request('/analytics/expiring-soon/');
  }

  // ========== Notifications ==========
  async getNotifications() {
    return this.request('/notifications/notifications/');
  }

  async markAllNotificationsRead() {
    return this.request('/notifications/notifications/mark_all_read/', { method: 'POST' });
  }

  // ========== IA / Entraînement ==========
  async trainModel() {
    return this.request('/analytics/ia/train/', { method: 'POST' });
  }

  // ========== IA (anciens endpoints) ==========
  async predictSalesByName(medicineId: string, medicineName: string, daysAhead: number = 7) {
    return this.request('/ai/predict/', {
      method: 'POST',
      body: JSON.stringify({ medicine_id: medicineId, medicine_name: medicineName, days_ahead: daysAhead }),
    });
  }

  async predictSales(medicineId: string, daysAhead: number = 7) {
    return this.request('/ai/predict/', {
      method: 'POST',
      body: JSON.stringify({ medicine_id: medicineId, days_ahead: daysAhead }),
    });
  }

  async getSeasonalAnalysis() {
    return this.request('/ai/seasonal/');
  }

  async chatWithAI(message: string) {
    return this.request('/ai/chat/', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }

  async recommendStock(medicineId: string) {
    return this.request('/ai/recommend-stock/', {
      method: 'POST',
      body: JSON.stringify({ medicine_id: medicineId }),
    });
  }

  // ========== IA – nouveaux endpoints proxy /analytics/ia ==========
  async getIAPredict(medicineId: string, daysAhead: number = 7) {
    return this.request(`/analytics/ia/predict/?medicine_id=${medicineId}&days=${daysAhead}`);
  }

  async getIAStockAnalysis(medicineId: string, currentStock: number) {
    return this.request(`/analytics/ia/stock-analysis/?medicine_id=${medicineId}&current_stock=${currentStock}`);
  }

  async getIAOrderRecommendation(medicineId: string, currentStock: number) {
    return this.request(`/analytics/ia/order-recommendation/?medicine_id=${medicineId}&current_stock=${currentStock}`);
  }

  async getIACriticality(medicineId: string) {
    return this.request(`/analytics/ia/criticality/?medicine_id=${medicineId}`);
  }

  async getIASeasonalAnalysis() {
    return this.request('/analytics/ia/seasonal/');
  }

  async getIAModelPerformance() {
    return this.request('/analytics/ia/model-performance/');
  }

  async getIAShap(medicineId: string) {
    return this.request(`/analytics/ia/shap/?medicine_id=${medicineId}`);
  }

  // ========== Stocks & Lots ==========
  async getAllStockLots() {
    return this.request('/inventory/lots/');
  }

  async getStockLots(medicineId: string) {
    return this.request(`/inventory/lots/?medicine=${medicineId}`);
  }

  // ========== Rapports ==========
 
  async downloadReport(kind: string, format: 'pdf' | 'excel', params?: Record<string, string>) {
  const token = this.getToken();
  if (!token) throw new Error('Non authentifié');

  const query = new URLSearchParams({ format, ...params }).toString();
  const url = `${DJANGO_API}/reports/${kind}/?${query}`;

  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    let detail = `Erreur ${response.status}`;
    try {
      const errorBody = await response.json();
      detail = errorBody.detail || errorBody.error || JSON.stringify(errorBody);
    } catch {
      const text = await response.text();
      detail = text.slice(0, 200);
    }
    console.error(`Erreur ${response.status} pour ${kind}:`, detail);
    throw new Error(`Erreur ${response.status}: ${detail}`);
  }

  return response.blob();
  }


  // ========== Recherche globale ==========
  async globalSearch(query: string) {
    return this.request(`/analytics/search/?q=${encodeURIComponent(query)}`);
  }

  // ========== Commandes (Orders) ==========
  async createOrder(medicineId: string, quantity: number, supplierId: string | null = null) {
    return this.request('/orders/orders/', {
      method: 'POST',
      body: JSON.stringify({
        medicine: medicineId,
        quantity_ordered: quantity,
        supplier: supplierId,
      }),
    });
  }


  async requestPasswordReset(email: string) {
  return this.request('/auth/password-reset/', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
  }


  async confirmPasswordReset(uid: string, token: string, newPassword: string) {
  return this.request('/auth/password-reset/confirm/', {
    method: 'POST',
    body: JSON.stringify({ uid, token, new_password: newPassword }),
  });
  }

  async getOrders() {
    return this.request('/orders/orders/');
  }

  async receiveOrder(orderId: number | string, data: any) {
    return this.request(`/orders/orders/${orderId}/receive/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async downloadOrderPdf(orderId: number | string): Promise<Blob> {
    const token = this.getToken();
    if (!token) {
      window.location.href = "/login";
      throw new Error("Non authentifié");
    }

    const url = `${DJANGO_API}/orders/orders/${orderId}/download-pdf/`;

    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.status === 401) {
      window.location.href = "/login";
      throw new Error("Session expirée");
    }

    if (!response.ok) {
      throw new Error("Erreur lors du téléchargement");
    }

    return response.blob();
  }
}

export const api = new ApiClient();
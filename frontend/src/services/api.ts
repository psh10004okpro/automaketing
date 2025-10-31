import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retrying, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await api.post('/api/auth/refresh', {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: newRefreshToken } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data: { email: string; password: string; name?: string; company_name?: string }) =>
    api.post('/api/auth/register', data),

  login: (email: string, password: string) =>
    api.post('/api/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),

  getCurrentUser: () => api.get('/api/auth/me'),
};

// Campaigns API
export const campaignsAPI = {
  list: () => api.get('/api/campaigns/'),

  get: (id: string) => api.get(`/api/campaigns/${id}`),

  create: (data: any) => api.post('/api/campaigns/', data),

  update: (id: string, data: any) => api.put(`/api/campaigns/${id}`, data),

  delete: (id: string) => api.delete(`/api/campaigns/${id}`),

  send: (id: string, recipientIds?: string[]) =>
    api.post(`/api/campaigns/${id}/send`, { recipient_ids: recipientIds }),
};

// AI Content API
export const aiAPI = {
  generateContent: (data: {
    content_type: string;
    target_audience: string;
    main_message: string;
    tone: string;
    platform?: string;
  }) => api.post('/api/ai/generate', data),

  optimizeSubject: (subjectLine: string) =>
    api.post('/api/ai/optimize-subject', { subject_line: subjectLine }),

  generateSocialCaptions: (topic: string, platform: string, count: number = 3) =>
    api.post('/api/ai/social-captions', null, {
      params: { topic, platform, count },
    }),
};

// Leads API
export const leadsAPI = {
  list: (params?: { search?: string; tag?: string; min_score?: number; skip?: number; limit?: number }) =>
    api.get('/api/leads/', { params }),

  get: (id: string) => api.get(`/api/leads/${id}`),

  create: (data: any) => api.post('/api/leads/', data),

  update: (id: string, data: any) => api.put(`/api/leads/${id}`, data),

  delete: (id: string) => api.delete(`/api/leads/${id}`),

  getActivities: (id: string, limit?: number) =>
    api.get(`/api/leads/${id}/activities`, { params: { limit } }),

  addActivity: (id: string, activityType: string, metadata?: any) =>
    api.post(`/api/leads/${id}/activities`, null, {
      params: { activity_type: activityType, metadata },
    }),

  getSummary: () => api.get('/api/leads/stats/summary'),

  import: (leads: any[]) => api.post('/api/leads/import', leads),
};

// Analytics API
export const analyticsAPI = {
  getOverview: (days: number = 30) =>
    api.get('/api/analytics/overview', { params: { days } }),

  getCampaignPerformance: (days: number = 30) =>
    api.get('/api/analytics/campaigns/performance', { params: { days } }),

  getCampaignTimeline: (days: number = 30) =>
    api.get('/api/analytics/campaigns/timeline', { params: { days } }),

  getLeadsGrowth: (days: number = 30) =>
    api.get('/api/analytics/leads/growth', { params: { days } }),

  getRecentActivities: (limit: number = 50) =>
    api.get('/api/analytics/activities/recent', { params: { limit } }),

  getEngagementHeatmap: () => api.get('/api/analytics/engagement/heatmap'),

  getInsights: () => api.get('/api/analytics/insights'),
};

// Workflows API
export const workflowsAPI = {
  list: (activeOnly?: boolean) =>
    api.get('/api/workflows/', { params: { active_only: activeOnly } }),

  get: (id: string) => api.get(`/api/workflows/${id}`),

  create: (data: any) => api.post('/api/workflows/', data),

  update: (id: string, data: any) => api.put(`/api/workflows/${id}`, data),

  delete: (id: string) => api.delete(`/api/workflows/${id}`),

  activate: (id: string) => api.post(`/api/workflows/${id}/activate`),

  deactivate: (id: string) => api.post(`/api/workflows/${id}/deactivate`),

  trigger: (id: string, triggerData: any) =>
    api.post(`/api/workflows/${id}/trigger`, triggerData),

  getTemplates: () => api.get('/api/workflows/templates/list'),
};

export default api;

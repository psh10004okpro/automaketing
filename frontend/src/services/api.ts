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

// SMS Campaigns API
export const smsAPI = {
  list: () => api.get('/api/sms/'),

  get: (id: string) => api.get(`/api/sms/${id}`),

  create: (data: any) => api.post('/api/sms/', data),

  update: (id: string, data: any) => api.put(`/api/sms/${id}`, data),

  delete: (id: string) => api.delete(`/api/sms/${id}`),

  send: (id: string, recipientIds?: string[]) =>
    api.post(`/api/sms/${id}/send`, { recipient_ids: recipientIds }),

  getStatus: (id: string) => api.get(`/api/sms/${id}/status`),

  validatePhone: (phone: string) =>
    api.post('/api/sms/validate-phone', null, { params: { phone } }),
};

// Social Media API
export const socialAPI = {
  createPost: (data: {
    platforms: string[];
    content: string;
    image_url?: string;
    scheduled_time?: string;
  }) => api.post('/api/social/posts', data),

  listPosts: (statusFilter?: string) =>
    api.get('/api/social/posts', { params: { status_filter: statusFilter } }),

  getPost: (id: string) => api.get(`/api/social/posts/${id}`),

  deletePost: (id: string) => api.delete(`/api/social/posts/${id}`),

  publishNow: (id: string) => api.post(`/api/social/posts/${id}/publish`),

  connectAccount: (data: {
    platform: string;
    account_id: string;
    account_name: string;
    access_token: string;
    refresh_token?: string;
  }) => api.post('/api/social/accounts/connect', data),

  listAccounts: () => api.get('/api/social/accounts'),

  disconnectAccount: (id: string) => api.delete(`/api/social/accounts/${id}`),

  getFacebookAuthUrl: (redirectUri: string) =>
    api.get('/api/social/auth/facebook/url', { params: { redirect_uri: redirectUri } }),

  facebookCallback: (code: string, redirectUri: string) =>
    api.post('/api/social/auth/facebook/callback', null, {
      params: { code, redirect_uri: redirectUri },
    }),

  testPost: (platforms: string[], content: string) =>
    api.post('/api/social/test-post', null, { params: { platforms, content } }),
};

// A/B Testing API
export const abTestAPI = {
  create: (data: any) => api.post('/api/ab-tests/', data),

  list: (statusFilter?: string, typeFilter?: string) =>
    api.get('/api/ab-tests/', {
      params: { status_filter: statusFilter, type_filter: typeFilter },
    }),

  get: (id: string) => api.get(`/api/ab-tests/${id}`),

  start: (id: string, recipientIds: string[]) =>
    api.post(`/api/ab-tests/${id}/start`, { recipient_ids: recipientIds }),

  updateMetrics: (id: string, variant: string, metric: string, increment: number = 1) =>
    api.post(`/api/ab-tests/${id}/metrics`, { variant, metric, increment }),

  getStats: (id: string) => api.get(`/api/ab-tests/${id}/stats`),

  checkWinner: (id: string) => api.post(`/api/ab-tests/${id}/check-winner`),

  declareWinner: (id: string, winnerVariant: string) =>
    api.post(`/api/ab-tests/${id}/declare-winner`, { winner_variant: winnerVariant }),

  cancel: (id: string) => api.post(`/api/ab-tests/${id}/cancel`),

  delete: (id: string) => api.delete(`/api/ab-tests/${id}`),
};

// Drip Campaign API
export const dripCampaignAPI = {
  create: (data: any) => api.post('/api/drip-campaigns/', data),

  list: (statusFilter?: string) =>
    api.get('/api/drip-campaigns/', { params: { status_filter: statusFilter } }),

  get: (id: string) => api.get(`/api/drip-campaigns/${id}`),

  update: (id: string, data: any) => api.put(`/api/drip-campaigns/${id}`, data),

  delete: (id: string) => api.delete(`/api/drip-campaigns/${id}`),

  addStep: (campaignId: string, data: any) =>
    api.post(`/api/drip-campaigns/${campaignId}/steps`, data),

  updateStep: (stepId: string, data: any) =>
    api.put(`/api/drip-campaigns/steps/${stepId}`, data),

  deleteStep: (stepId: string) => api.delete(`/api/drip-campaigns/steps/${stepId}`),

  activate: (id: string) => api.post(`/api/drip-campaigns/${id}/activate`),

  pause: (id: string) => api.post(`/api/drip-campaigns/${id}/pause`),

  enroll: (campaignId: string, data: any) =>
    api.post(`/api/drip-campaigns/${campaignId}/enroll`, data),

  unsubscribe: (campaignId: string, subscriberId: string) =>
    api.post(`/api/drip-campaigns/${campaignId}/subscribers/${subscriberId}/unsubscribe`),

  getStats: (id: string) => api.get(`/api/drip-campaigns/${id}/stats`),

  listSubscribers: (campaignId: string) =>
    api.get(`/api/drip-campaigns/${campaignId}/subscribers`),
};

// Segment API
export const segmentAPI = {
  create: (data: any) => api.post('/api/segments/', data),

  list: (typeFilter?: string) =>
    api.get('/api/segments/', { params: { type_filter: typeFilter } }),

  get: (id: string) => api.get(`/api/segments/${id}`),

  update: (id: string, data: any) => api.put(`/api/segments/${id}`, data),

  delete: (id: string) => api.delete(`/api/segments/${id}`),

  calculate: (id: string) => api.post(`/api/segments/${id}/calculate`),

  duplicate: (id: string, newName?: string) =>
    api.post(`/api/segments/${id}/duplicate`, null, { params: { new_name: newName } }),

  preview: (data: any) => api.post('/api/segments/preview', data),

  getLeads: (id: string, limit: number = 100, offset: number = 0) =>
    api.get(`/api/segments/${id}/leads`, { params: { limit, offset } }),

  addLeads: (id: string, leadIds: string[]) =>
    api.post(`/api/segments/${id}/leads`, { lead_ids: leadIds }),

  removeLeads: (id: string, leadIds: string[]) =>
    api.delete(`/api/segments/${id}/leads`, { data: { lead_ids: leadIds } }),
};

export default api;

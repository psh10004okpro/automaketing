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

export default api;

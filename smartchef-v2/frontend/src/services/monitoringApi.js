import api from './api';

export const monitoringApi = {
  getDashboard: (params = {}) =>
    api.get('/monitoring/dashboard', { params }),

  getTrend: (params = {}) =>
    api.get('/monitoring/dashboard/trend', { params }),

  queryLogs: (params) => api.get('/monitoring/logs', { params }),

  getSessionTrace: (sessionId) =>
    api.get(`/monitoring/sessions/${sessionId}/traces`),

  getDeviceSessions: (deviceId, params) =>
    api.get(`/monitoring/devices/${deviceId}/sessions`, { params }),
};

export const alertApi = {
  listRules: (params) => api.get('/alert-rules', { params }),
  createRule: (data) => api.post('/alert-rules', data),
  getRule: (id) => api.get(`/alert-rules/${id}`),
  updateRule: (id, data) => api.put(`/alert-rules/${id}`, data),
  deleteRule: (id) => api.delete(`/alert-rules/${id}`),
  toggleRule: (id, isEnabled) =>
    api.put(`/alert-rules/${id}/toggle`, { is_enabled: isEnabled }),

  listEvents: (params) => api.get('/alert-events', { params }),
};

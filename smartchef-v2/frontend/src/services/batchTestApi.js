import api from './api';

export const batchTestApi = {
  list: (params) => api.get('/batch-tests', { params }),
  getStats: () => api.get('/batch-tests/stats'),
  create: (data) => api.post('/batch-tests', data),
  get: (id) => api.get(`/batch-tests/${id}`),
  delete: (id) => api.delete(`/batch-tests/${id}`),

  listCases: (id, params) => api.get(`/batch-tests/${id}/cases`, { params }),
  addCase: (id, data) => api.post(`/batch-tests/${id}/cases`, data),
  updateCase: (id, caseId, data) => api.put(`/batch-tests/${id}/cases/${caseId}`, data),
  deleteCase: (id, caseId) => api.delete(`/batch-tests/${id}/cases/${caseId}`),
  importCases: (id, cases) => api.post(`/batch-tests/${id}/import-cases`, { cases }),
  exportCases: (id) => api.get(`/batch-tests/${id}/export-cases`),

  execute: (id) => api.post(`/batch-tests/${id}/execute`),
  listRuns: (id, params) => api.get(`/batch-tests/${id}/runs`, { params }),
  getAnalysis: (id) => api.get(`/batch-tests/${id}/analysis`),
  triggerAnalysis: (id) => api.post(`/batch-tests/${id}/analyze`),
  generateCases: (id, data = {}) => api.post(`/batch-tests/${id}/generate-cases`, data),
};

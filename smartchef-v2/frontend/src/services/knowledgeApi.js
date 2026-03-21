import api from './api';

export const knowledgeApi = {
  listCategories: () => api.get('/knowledge/categories'),
  createCategory: (data) => api.post('/knowledge/categories', data),
  updateCategory: (id, data) => api.put(`/knowledge/categories/${id}`, data),
  deleteCategory: (id) => api.delete(`/knowledge/categories/${id}`),

  listDocuments: (params) => api.get('/knowledge/documents', { params }),
  uploadDocument: (formData) =>
    api.post('/knowledge/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    }),
  getDocument: (id) => api.get(`/knowledge/documents/${id}`),
  updateDocument: (id, data) => api.put(`/knowledge/documents/${id}`, data),
  deleteDocument: (id) => api.delete(`/knowledge/documents/${id}`),
  reindexDocument: (id) => api.post(`/knowledge/documents/${id}/reindex`),

  search: (data) => api.post('/knowledge/search', data),
};

import api from './api';

/** 提交训练/评估任务接口应快速返回；保留适度超时以防代理/慢网 */
const LONG_RUNNING_MS = 60000;

export const intentLibraryApi = {
  listLibraries: (params, opts = {}) =>
    api.get('/intent-libraries', { params, ...opts }),
  createLibrary: (data) => api.post('/intent-libraries', data),
  getLibrary: (id) => api.get(`/intent-libraries/${id}`),
  updateLibrary: (id, data) => api.put(`/intent-libraries/${id}`, data),
  deleteLibrary: (id) => api.delete(`/intent-libraries/${id}`),
  importLibraries: (formData) =>
    api.post('/intent-libraries/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  listModels: (libId) => api.get(`/intent-libraries/${libId}/models`),
  /** 单模型轮询（含 progress），避免列表接口与 id 匹配问题 */
  getModel: (modelId) => api.get(`/models/${modelId}`),
  createModel: (libId, data) => api.post(`/intent-libraries/${libId}/models`, data),
  trainModel: (modelId, data) =>
    api.post(`/models/${modelId}/train`, data ?? {}, { timeout: LONG_RUNNING_MS }),
  evaluateModel: (modelId, data) =>
    api.post(`/models/${modelId}/evaluate`, data, { timeout: LONG_RUNNING_MS }),
  setTestable: (modelId) => api.post(`/models/${modelId}/set-testable`),
  publishModel: (modelId) => api.post(`/models/${modelId}/publish`),
  archiveModel: (modelId) => api.post(`/models/${modelId}/archive`),
  restoreModel: (modelId) => api.post(`/models/${modelId}/restore`),
  downloadModel: (modelId) => api.get(`/models/${modelId}/download`, { responseType: 'blob' }),

  listDatasets: (libId, params) => api.get(`/intent-libraries/${libId}/datasets`, { params }),
  createDataset: (libId, data) => api.post(`/intent-libraries/${libId}/datasets`, data),
  getDataset: (id) => api.get(`/datasets/${id}`),
  updateDataset: (id, data) => api.put(`/datasets/${id}`, data),
  deleteDataset: (id) => api.delete(`/datasets/${id}`),

  listIntents: (datasetId, params) => api.get(`/datasets/${datasetId}/intents`, { params }),
  createIntent: (datasetId, data) => api.post(`/datasets/${datasetId}/intents`, data),
  updateIntent: (intentId, data) => api.put(`/intents/${intentId}`, data),
  deleteIntent: (intentId) => api.delete(`/intents/${intentId}`),

  listSlots: (datasetId) => api.get(`/datasets/${datasetId}/slots`),
  createSlot: (datasetId, data) => api.post(`/datasets/${datasetId}/slots`, data),
  updateSlot: (slotId, data) => api.put(`/slots/${slotId}`, data),
  deleteSlot: (slotId) => api.delete(`/slots/${slotId}`),
  listSlotEntities: (slotId) => api.get(`/slots/${slotId}/entities`),
  createSlotEntity: (slotId, data) => api.post(`/slots/${slotId}/entities`, data),
  updateSlotEntity: (entityId, data) => api.put(`/entities/${entityId}`, data),
  deleteSlotEntity: (entityId) => api.delete(`/entities/${entityId}`),

  listSimilarQuestions: (intentId) => api.get(`/intents/${intentId}/similar-questions`),
  createSimilarQuestion: (intentId, data) =>
    api.post(`/intents/${intentId}/similar-questions`, data),
  updateSimilarQuestion: (sqId, data) => api.put(`/similar-questions/${sqId}`, data),
  deleteSimilarQuestion: (sqId) => api.delete(`/similar-questions/${sqId}`),

  generateTrainingData: (datasetId, data) =>
    api.post(`/datasets/${datasetId}/generate-training`, data),
  generateEvaluationData: (libraryId, datasetId, data) =>
    api.post(`/intent-libraries/${libraryId}/eval-datasets/${datasetId}/generate`, data),

  listEvalDatasets: (libId, params) =>
    api.get(`/intent-libraries/${libId}/eval-datasets`, { params }),
  createEvalDataset: (libId, data) =>
    api.post(`/intent-libraries/${libId}/eval-datasets`, data),

  listNegativeExamples: (intentId) => api.get(`/intents/${intentId}/negative-examples`),
  createNegativeExample: (intentId, data) =>
    api.post(`/intents/${intentId}/negative-examples`, data),
  deleteNegativeExample: (neId) => api.delete(`/negative-examples/${neId}`),

  createTestSession: (modelId, data) => api.post(`/models/${modelId}/test-sessions`, data),
  listTestSessions: (modelId) => api.get(`/models/${modelId}/test-sessions`),
  /** @param data {{ content: string }} 与后端 SendMessageRequest 一致 */
  sendTestMessage: (sessionId, data) =>
    api.post(`/test-sessions/${sessionId}/messages`, data),
  getTestMessages: (sessionId, params) =>
    api.get(`/test-sessions/${sessionId}/messages`, { params }),
};

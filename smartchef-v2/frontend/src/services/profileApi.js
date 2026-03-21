import api from './api';

export const profileApi = {
  // Profile CRUD
  listProfiles: (params) => api.get('/profiles', { params }),
  getStats: () => api.get('/profiles/stats'),
  createProfile: (data) => api.post('/profiles', data),
  getProfile: (id) => api.get(`/profiles/${id}`),
  updateProfile: (id, data) => api.put(`/profiles/${id}`, data),
  deleteProfile: (id) => api.delete(`/profiles/${id}`),

  // Persona
  listPersonas: (profileId) => api.get(`/profiles/${profileId}/personas`),
  createPersona: (profileId, data) => api.post(`/profiles/${profileId}/personas`, data),
  updatePersona: (profileId, personaId, data) =>
    api.put(`/profiles/${profileId}/personas/${personaId}`, data),
  deletePersona: (profileId, personaId) =>
    api.delete(`/profiles/${profileId}/personas/${personaId}`),
  activatePersona: (profileId, personaId) =>
    api.post(`/profiles/${profileId}/personas/${personaId}/activate`),

  // Library bindings
  listBindings: (profileId) => api.get(`/profiles/${profileId}/intent-libraries`),
  syncBindings: (profileId, bindings) =>
    api.put(`/profiles/${profileId}/intent-libraries`, { bindings }),

  // Publishing
  publish: (profileId) => api.post(`/profiles/${profileId}/publish`),
  listVersions: (profileId) => api.get(`/profiles/${profileId}/versions`),
  getVersion: (versionId) => api.get(`/versions/${versionId}`),
  archiveVersion: (versionId) => api.post(`/versions/${versionId}/archive`),

  // Test sessions
  createTestSession: (profileId, data) =>
    api.post(`/profiles/${profileId}/test-sessions`, data),
  listTestSessions: (profileId) => api.get(`/profiles/${profileId}/test-sessions`),
  updateTestSession: (sessionId, data) => api.put(`/test-sessions/${sessionId}`, data),
  deleteTestSession: (sessionId) => api.delete(`/test-sessions/${sessionId}`),
  sendMessage: (sessionId, data) => api.post(`/test-sessions/${sessionId}/messages`, data),
  getMessages: (sessionId) => api.get(`/test-sessions/${sessionId}/messages`),
};

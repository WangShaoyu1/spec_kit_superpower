/**
 * 开发（vite dev）：默认 ''，请求同源 /api/...，由 Vite 转发到后端，避免 CORS。
 * 测试（vitest MODE=test）：回退到完整 URL，便于断言与 Node 环境一致。
 * 生产构建：默认 http://127.0.0.1:8005；部署时请设置 VITE_API_BASE 为真实 API 根地址。
 */
function resolveApiBase() {
  const raw = import.meta.env.VITE_API_BASE
  if (raw != null && String(raw).trim() !== '') {
    return String(raw).replace(/\/$/, '')
  }
  if (import.meta.env.DEV && import.meta.env.MODE !== 'test') {
    return ''
  }
  return 'http://127.0.0.1:8005'
}

const API_BASE = resolveApiBase()


async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  const payload = await response.json()

  if (!response.ok || payload.code !== '000000') {
    const error = new Error(payload.message || '请求失败')
    error.payload = payload
    throw error
  }

  return payload.data
}


function authHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}


function withQuery(path, params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, value)
    }
  })
  const query = search.toString()
  return query ? `${path}?${query}` : path
}


export function login(username, password) {
  return request('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
}


export function fetchUsers(token) {
  return request('/api/v1/admin/users', {
    headers: authHeaders(token),
  })
}


export function fetchPermissionMatrix(token) {
  return request('/api/v1/admin/permission-matrix', {
    headers: authHeaders(token),
  })
}


export function createUser(token, payload) {
  return request('/api/v1/admin/users', {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function updateUserRole(token, userId, role) {
  return request(`/api/v1/admin/users/${userId}/role`, {
    method: 'PATCH',
    headers: authHeaders(token),
    body: JSON.stringify({ role }),
  })
}


export function changeUserStatus(token, userId, status) {
  return request(`/api/v1/admin/users/${userId}/status`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ status }),
  })
}


export function resetUserPassword(token, userId) {
  return request(`/api/v1/admin/users/${userId}/reset-password`, {
    method: 'POST',
    headers: authHeaders(token),
  })
}


export function fetchIntentLibraries(token) {
  return request('/api/v1/intent-libraries', {
    headers: authHeaders(token),
  })
}


export function createIntentLibrary(token, payload) {
  return request('/api/v1/intent-libraries', {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function fetchIntentLibraryDetail(token, libraryId) {
  return request(`/api/v1/intent-libraries/${libraryId}`, {
    headers: authHeaders(token),
  })
}


export function trainIntentLibraryModel(token, libraryId, payload) {
  return request(`/api/v1/intent-libraries/${libraryId}/models/train`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function evaluateIntentModel(token, modelId, payload) {
  return request(`/api/v1/models/${modelId}/evaluate`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function publishIntentModel(token, modelId, payload) {
  return request(`/api/v1/models/${modelId}/publish`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function downloadIntentModel(token, modelId) {
  return request(`/api/v1/models/${modelId}/download`, {
    headers: authHeaders(token),
  })
}


export function runIntentModelSingleTest(token, modelId, payload) {
  return request(`/api/v1/models/${modelId}/single-test`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function fetchKnowledgeBases(token, params = {}) {
  return request(withQuery('/api/v1/knowledge-bases', params), {
    headers: authHeaders(token),
  })
}


export function createKnowledgeCategory(token, payload) {
  return request('/api/v1/knowledge-bases/categories', {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function updateKnowledgeCategory(token, categoryId, payload) {
  return request(`/api/v1/knowledge-bases/categories/${categoryId}`, {
    method: 'PATCH',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function uploadKnowledgeDocument(token, categoryId, payload) {
  return request(`/api/v1/knowledge-bases/${categoryId}/documents/upload`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function fetchKnowledgeDocumentDetail(token, documentId) {
  return request(`/api/v1/knowledge-documents/${documentId}`, {
    headers: authHeaders(token),
  })
}


export function reindexKnowledgeDocument(token, documentId, payload = {}) {
  return request(`/api/v1/knowledge-documents/${documentId}/reindex`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function runKnowledgeRetrieveTest(token, documentId, payload) {
  return request(`/api/v1/knowledge-documents/${documentId}/retrieve-test`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function deleteKnowledgeDocument(token, documentId) {
  return request(`/api/v1/knowledge-documents/${documentId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })
}


export function fetchDialogProfiles(token, params = {}) {
  return request(withQuery('/api/v1/dialog-profiles', params), {
    headers: authHeaders(token),
  })
}


export function createDialogProfile(token, payload) {
  return request('/api/v1/dialog-profiles', {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function fetchDialogProfileDetail(token, profileId) {
  return request(`/api/v1/dialog-profiles/${profileId}`, {
    headers: authHeaders(token),
  })
}


export function updateDialogProfile(token, profileId, payload) {
  return request(`/api/v1/dialog-profiles/${profileId}`, {
    method: 'PATCH',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function publishDialogProfile(token, profileId, payload = {}) {
  return request(`/api/v1/dialog-profiles/${profileId}/publish`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function createDialogProfileSession(token, profileId, payload) {
  return request(`/api/v1/dialog-profiles/${profileId}/test-sessions`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function fetchDialogProfileSession(token, sessionId) {
  return request(`/api/v1/test-sessions/${sessionId}`, {
    headers: authHeaders(token),
  })
}


export function sendDialogProfileMessage(token, sessionId, payload) {
  return request(`/api/v1/test-sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function fetchBatchTests(token, params = {}) {
  return request(withQuery('/api/v1/batch-tests', params), {
    headers: authHeaders(token),
  })
}


export function createBatchTest(token, payload) {
  return request('/api/v1/batch-tests', {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function fetchBatchTestDetail(token, batchId) {
  return request(`/api/v1/batch-tests/${batchId}`, {
    headers: authHeaders(token),
  })
}


export function generateBatchTestCases(token, batchId, payload) {
  return request(`/api/v1/batch-tests/${batchId}/generate-cases`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function executeBatchTest(token, batchId, payload = {}) {
  return request(`/api/v1/batch-tests/${batchId}/execute`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function fetchMonitoringOverview(token, params = {}) {
  return request(withQuery('/api/v1/monitoring/overview', params), {
    headers: authHeaders(token),
  })
}


export function fetchMonitoringRequestLogs(token, params = {}) {
  return request(withQuery('/api/v1/monitoring/request-logs', params), {
    headers: authHeaders(token),
  })
}


export function fetchMonitoringDeviceSessions(token, params = {}) {
  return request(withQuery('/api/v1/monitoring/device-sessions', params), {
    headers: authHeaders(token),
  })
}


export function fetchMonitoringSessionDetail(token, sessionId) {
  return request(`/api/v1/monitoring/sessions/${sessionId}`, {
    headers: authHeaders(token),
  })
}


export function fetchMonitoringAlertRules(token) {
  return request('/api/v1/monitoring/alert-rules', {
    headers: authHeaders(token),
  })
}


export function createMonitoringAlertRule(token, payload) {
  return request('/api/v1/monitoring/alert-rules', {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}


export function updateMonitoringAlertRule(token, ruleId, payload) {
  return request(`/api/v1/monitoring/alert-rules/${ruleId}`, {
    method: 'PATCH',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
}

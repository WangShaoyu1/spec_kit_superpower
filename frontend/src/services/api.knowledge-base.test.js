import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  createKnowledgeCategory,
  deleteKnowledgeDocument,
  fetchKnowledgeBases,
  fetchKnowledgeDocumentDetail,
  reindexKnowledgeDocument,
  runKnowledgeRetrieveTest,
  updateKnowledgeCategory,
  uploadKnowledgeDocument,
} from './api'


function success(data = {}) {
  return Promise.resolve({
    ok: true,
    json: async () => ({ code: '000000', message: 'success', data }),
  })
}


describe('knowledge-base api', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('requests knowledge directory and detail with auth headers', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(() => success({ categories: [], documents: [] }))

    await fetchKnowledgeBases('token-admin', { category_id: 'kb_001' })
    await fetchKnowledgeDocumentDetail('token-admin', 'doc_001')

    expect(fetchSpy).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining('/api/v1/knowledge-bases?category_id=kb_001'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
    expect(fetchSpy).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('/api/v1/knowledge-documents/doc_001'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
  })

  it('sends category, upload, reindex, retrieve and delete requests', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(() => success({}))

    await createKnowledgeCategory('token-admin', { name: '菜谱知识', icon: '🍳', description: 'desc' })
    await updateKnowledgeCategory('token-admin', 'kb_001', { name: '菜谱知识库', icon: '📚', description: 'updated' })
    await uploadKnowledgeDocument('token-admin', 'kb_001', {
      name: '银耳汤.json',
      format: 'json',
      content: '{"recipe_name":"银耳汤"}',
    })
    await reindexKnowledgeDocument('token-admin', 'doc_001', { reason: 'refresh' })
    await runKnowledgeRetrieveTest('token-admin', 'doc_001', { query: '银耳汤' })
    await deleteKnowledgeDocument('token-admin', 'doc_001')

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/knowledge-bases/categories'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/knowledge-bases/categories/kb_001'),
      expect.objectContaining({ method: 'PATCH' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/knowledge-bases/kb_001/documents/upload'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/knowledge-documents/doc_001/reindex'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/knowledge-documents/doc_001/retrieve-test'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/knowledge-documents/doc_001'),
      expect.objectContaining({ method: 'DELETE' }),
    )
  })
})

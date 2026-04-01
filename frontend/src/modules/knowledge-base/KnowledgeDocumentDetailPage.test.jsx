import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { KnowledgeDocumentDetailPage } from './KnowledgeDocumentDetailPage'


const apiMocks = vi.hoisted(() => ({
  fetchKnowledgeDocumentDetail: vi.fn(),
  reindexKnowledgeDocument: vi.fn(),
  runKnowledgeRetrieveTest: vi.fn(),
  deleteKnowledgeDocument: vi.fn(),
}))


vi.mock('../../services/api', () => apiMocks)


const detailPayload = {
  document: {
    id: 'doc_001',
    name: '银耳汤.json',
    format: 'json',
    status: 'ready',
    index_version: 1,
  },
  valid_content: [
    { field: 'recipe_name', value: '银耳汤' },
  ],
  filtered_fields: [
    { field: 'image_url', reason: 'filtered' },
  ],
  probes: [],
}


describe('KnowledgeDocumentDetailPage', () => {
  beforeEach(() => {
    apiMocks.fetchKnowledgeDocumentDetail.mockResolvedValue(detailPayload)
    apiMocks.reindexKnowledgeDocument.mockResolvedValue({ document: { id: 'doc_001', status: 'indexing' } })
    apiMocks.runKnowledgeRetrieveTest.mockResolvedValue({
      hit: true,
      score: 0.96,
      snippet: '银耳汤需要银耳和雪梨',
      response_preview: '命中文档片段：银耳汤需要银耳和雪梨',
    })
    apiMocks.deleteKnowledgeDocument.mockResolvedValue({ deleted: true })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('renders field sections and supports retrieve + reindex actions', async () => {
    render(
      <MemoryRouter initialEntries={['/knowledge-base/doc_001']}>
        <Routes>
          <Route path="/knowledge-base/:documentId" element={<KnowledgeDocumentDetailPage token="token-admin" />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '银耳汤.json' })).toBeInTheDocument()
      expect(screen.getByText('recipe_name')).toBeInTheDocument()
      expect(screen.getByText('image_url')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '重新索引' }))

    await waitFor(() => {
      expect(apiMocks.reindexKnowledgeDocument).toHaveBeenCalledWith('token-admin', 'doc_001', { reason: 'manual_refresh' })
    })

    fireEvent.change(screen.getByLabelText('检索语句'), { target: { value: '银耳汤' } })
    fireEvent.click(screen.getByRole('button', { name: '执行检索验证' }))

    await waitFor(() => {
      expect(apiMocks.runKnowledgeRetrieveTest).toHaveBeenCalledWith('token-admin', 'doc_001', { query: '银耳汤' })
    })

    expect(await screen.findByText(/命中，得分/)).toBeInTheDocument()
  })
})

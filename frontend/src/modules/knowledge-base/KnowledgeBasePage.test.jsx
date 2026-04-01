import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { KnowledgeBasePage } from './KnowledgeBasePage'


const apiMocks = vi.hoisted(() => ({
  fetchKnowledgeBases: vi.fn(),
  createKnowledgeCategory: vi.fn(),
  uploadKnowledgeDocument: vi.fn(),
}))


vi.mock('../../services/api', () => apiMocks)


const directoryPayload = {
  categories: [
    {
      id: 'kb_001',
      name: '菜谱知识',
      icon: '🍳',
      description: '菜谱知识库',
      document_count: 1,
      ready_document_count: 1,
      status: 'ready',
    },
  ],
  documents: [
    {
      id: 'doc_001',
      name: '银耳汤.json',
      format: 'json',
      status: 'ready',
      index_version: 1,
    },
  ],
}


describe('KnowledgeBasePage', () => {
  beforeEach(() => {
    apiMocks.fetchKnowledgeBases.mockImplementation((_token, params) => {
      if (params?.category_id) {
        return Promise.resolve(directoryPayload)
      }
      return Promise.resolve({ categories: directoryPayload.categories, documents: [] })
    })
    apiMocks.createKnowledgeCategory.mockResolvedValue({ category: directoryPayload.categories[0] })
    apiMocks.uploadKnowledgeDocument.mockResolvedValue({ document: directoryPayload.documents[0] })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('loads categories and documents for the selected category', async () => {
    render(
      <MemoryRouter>
        <KnowledgeBasePage token="token-admin" />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '知识库管理' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /菜谱知识/ })).toBeInTheDocument()
      expect(screen.getByText('银耳汤.json')).toBeInTheDocument()
    })
  })

  it('creates category and uploads document', async () => {
    render(
      <MemoryRouter>
        <KnowledgeBasePage token="token-admin" />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /菜谱知识/ })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '新建分类' }))
    fireEvent.change(screen.getByLabelText('分类名称'), { target: { value: '公司信息' } })
    fireEvent.click(screen.getByRole('button', { name: /创建分类/ }))

    await waitFor(() => {
      expect(apiMocks.createKnowledgeCategory).toHaveBeenCalled()
    })

    fireEvent.click(screen.getByRole('button', { name: '上传文档' }))
    fireEvent.change(screen.getByLabelText('文档名称'), { target: { value: '公司简介.md' } })
    fireEvent.change(screen.getByLabelText('文档内容'), { target: { value: '# 公司简介\nSmartChef' } })
    fireEvent.click(screen.getByRole('button', { name: /提交文档/ }))

    await waitFor(() => {
      expect(apiMocks.uploadKnowledgeDocument).toHaveBeenCalledWith('token-admin', 'kb_001', expect.any(Object))
    })
  })
})

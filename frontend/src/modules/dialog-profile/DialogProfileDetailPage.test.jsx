import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { DialogProfileDetailPage } from './DialogProfileDetailPage'


const apiMocks = vi.hoisted(() => ({
  fetchDialogProfileDetail: vi.fn(),
  fetchIntentLibraries: vi.fn(),
  fetchKnowledgeBases: vi.fn(),
  updateDialogProfile: vi.fn(),
  publishDialogProfile: vi.fn(),
}))


vi.mock('../../services/api', () => apiMocks)


const detailPayload = {
  profile: {
    id: 'profile_001',
    name: '方案A',
    status: 'draft',
    llm_model: 'gpt-4o-mini',
    routing_strategy: 'intent_first',
    persona_name: '厨房助手',
    persona_prompt: '活泼友好的厨房助手',
    intent_threshold: 0.66,
    session_timeout_minutes: 15,
    knowledge_base_id: 'kb_001',
    publish_version: 0,
  },
  bindings: [
    {
      id: 'binding_001',
      library_id: 'lib_001',
      library_name: '中文指令库',
      published_model_name: null,
    },
  ],
  published_versions: [],
}


describe('DialogProfileDetailPage', () => {
  beforeEach(() => {
    apiMocks.fetchDialogProfileDetail.mockResolvedValue(detailPayload)
    apiMocks.fetchIntentLibraries.mockResolvedValue({
      items: [{ id: 'lib_001', name: '中文指令库' }],
    })
    apiMocks.fetchKnowledgeBases.mockResolvedValue({
      categories: [{ id: 'kb_001', name: '菜谱知识库' }],
      documents: [],
    })
    apiMocks.updateDialogProfile.mockResolvedValue({ profile: detailPayload.profile })
    apiMocks.publishDialogProfile.mockRejectedValue({
      payload: {
        data: {
          guard_items: ['指令库 中文指令库 缺少已发布模型'],
        },
      },
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('preserves selected knowledge base when saving and shows publish blockers', async () => {
    render(
      <MemoryRouter initialEntries={['/dialog-profiles/profile_001']}>
        <Routes>
          <Route path="/dialog-profiles/:profileId" element={<DialogProfileDetailPage token="token-admin" />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '方案A' })).toBeInTheDocument()
      expect(screen.getAllByText(/中文指令库/).length).toBeGreaterThan(0)
    })

    fireEvent.change(screen.getByLabelText('人设名称'), { target: { value: '专业顾问' } })
    fireEvent.click(screen.getByRole('button', { name: '保存配置' }))

    await waitFor(() => {
      expect(apiMocks.updateDialogProfile).toHaveBeenCalledWith(
        'token-admin',
        'profile_001',
        expect.objectContaining({ knowledge_base_id: 'kb_001' }),
      )
    })

    fireEvent.click(screen.getByRole('button', { name: '发布方案' }))

    await waitFor(() => {
      expect(screen.getByText(/发布门禁未通过/)).toBeInTheDocument()
      expect(screen.getByText(/缺少已发布模型/)).toBeInTheDocument()
    })
  })
})

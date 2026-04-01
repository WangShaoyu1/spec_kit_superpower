import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { DialogProfilePage } from './DialogProfilePage'


const apiMocks = vi.hoisted(() => ({
  fetchKnowledgeBases: vi.fn(),
  fetchDialogProfiles: vi.fn(),
  createDialogProfile: vi.fn(),
}))


vi.mock('../../services/api', () => apiMocks)


const directoryPayload = {
  items: [
    {
      id: 'profile_001',
      name: '方案A',
      status: 'draft',
      llm_model: 'gpt-4o-mini',
      routing_strategy: 'intent_first',
      persona_name: '厨房助手',
      intent_threshold: 0.66,
      session_timeout_minutes: 15,
    },
  ],
  summary: {
    total: 1,
    draft_count: 1,
    published_count: 0,
  },
  current_published_profile: null,
}


describe('DialogProfilePage', () => {
  beforeEach(() => {
    apiMocks.fetchDialogProfiles.mockResolvedValue(directoryPayload)
    apiMocks.fetchKnowledgeBases.mockResolvedValue({
      categories: [{ id: 'kb_001', name: '菜谱知识库' }],
      documents: [],
    })
    apiMocks.createDialogProfile.mockResolvedValue({ profile: directoryPayload.items[0] })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('loads dialog profile directory', async () => {
    render(
      <MemoryRouter>
        <DialogProfilePage token="token-admin" />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '对话方案' })).toBeInTheDocument()
      expect(screen.getByText('方案A')).toBeInTheDocument()
      expect(screen.getByText('草稿方案')).toBeInTheDocument()
    })
  })

  it('creates a dialog profile with selected knowledge base', async () => {
    render(
      <MemoryRouter>
        <DialogProfilePage token="token-admin" />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('方案A')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '新建方案' }))
    fireEvent.change(screen.getByLabelText('方案名称'), { target: { value: '方案B' } })
    fireEvent.change(screen.getByLabelText('人设名称'), { target: { value: '专业顾问' } })
    fireEvent.change(screen.getByLabelText('人设描述'), { target: { value: '专业冷静的厨电顾问' } })
    fireEvent.change(screen.getByLabelText('指令阈值'), { target: { value: '0.7' } })
    fireEvent.change(screen.getByLabelText('会话超时'), { target: { value: '20' } })
    fireEvent.mouseDown(screen.getAllByLabelText('知识库')[0])
    fireEvent.click(screen.getByText('菜谱知识库'))
    fireEvent.click(screen.getByRole('button', { name: /创建方案/ }))

    await waitFor(() => {
      expect(apiMocks.createDialogProfile).toHaveBeenCalledWith(
        'token-admin',
        expect.objectContaining({ knowledge_base_id: 'kb_001' }),
      )
    })
  })
})

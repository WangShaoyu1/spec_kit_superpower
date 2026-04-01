import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { BatchTestPage } from './BatchTestPage'


const apiMocks = vi.hoisted(() => ({
  createBatchTest: vi.fn(),
  fetchBatchTests: vi.fn(),
  fetchDialogProfiles: vi.fn(),
}))


vi.mock('../../services/api', () => apiMocks)


const directoryPayload = {
  items: [
    {
      id: 'batch_001',
      name: '回归批次A',
      profile_name: '方案A',
      status: 'completed',
      case_count: 4,
      pass_count: 3,
      accuracy: 0.75,
      response_p95_ms: 2430,
    },
  ],
  summary: {
    total: 1,
    draft_count: 0,
    ready_count: 0,
    running_count: 0,
    completed_count: 1,
  },
}


describe('BatchTestPage', () => {
  beforeEach(() => {
    apiMocks.fetchBatchTests.mockResolvedValue(directoryPayload)
    apiMocks.fetchDialogProfiles.mockResolvedValue({
      items: [{ id: 'profile_001', name: '方案A', status: 'published' }],
    })
    apiMocks.createBatchTest.mockResolvedValue({
      batch: { id: 'batch_002', name: '回归批次B' },
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('loads batch directory', async () => {
    render(
      <MemoryRouter>
        <BatchTestPage token="token-admin" />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '批量测试' })).toBeInTheDocument()
      expect(screen.getByText('回归批次A')).toBeInTheDocument()
      expect(screen.getByText('已完成批次')).toBeInTheDocument()
    })
  })

  it('creates a batch test run', async () => {
    render(
      <MemoryRouter>
        <BatchTestPage token="token-admin" />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('回归批次A')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '新建批次' }))
    fireEvent.change(screen.getByLabelText('批次名称'), { target: { value: '回归批次B' } })
    fireEvent.mouseDown(screen.getByLabelText('被测方案'))
    fireEvent.click(screen.getByText('方案A'))
    fireEvent.change(screen.getByLabelText('准确率阈值'), { target: { value: '0.9' } })
    fireEvent.change(screen.getByLabelText('指令 P95 阈值'), { target: { value: '200' } })
    fireEvent.change(screen.getByLabelText('知识/闲聊 P95 阈值'), { target: { value: '1800' } })
    fireEvent.click(screen.getByRole('button', { name: /创建批次/ }))

    await waitFor(() => {
      expect(apiMocks.createBatchTest).toHaveBeenCalledWith(
        'token-admin',
        expect.objectContaining({
          name: '回归批次B',
          profile_id: 'profile_001',
          baseline_thresholds: {
            accuracy_min: 0.9,
            command_response_p95_ms: 200,
            knowledge_response_p95_ms: 1800,
          },
        }),
      )
    })
  })
})

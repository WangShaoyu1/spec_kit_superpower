import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

const messageMocks = vi.hoisted(() => ({
  success: vi.fn(),
  error: vi.fn(),
}))

import { BatchTestDetailPage } from './BatchTestDetailPage'


const apiMocks = vi.hoisted(() => ({
  executeBatchTest: vi.fn(),
  fetchBatchTestDetail: vi.fn(),
  generateBatchTestCases: vi.fn(),
}))


vi.mock('antd', async () => {
  const actual = await vi.importActual('antd')
  return {
    ...actual,
    message: messageMocks,
  }
})

vi.mock('../../services/api', () => apiMocks)


const readyPayload = {
  batch: {
    id: 'batch_001',
    name: '回归批次A',
    profile_name: '方案A',
    status: 'ready',
    case_count: 4,
    executed_count: 0,
    pass_count: 0,
    accuracy: 0,
    response_p95_ms: 0,
    threshold_snapshot: {
      accuracy_min: 0.95,
      command_response_p95_ms: 200,
      knowledge_response_p95_ms: 2000,
    },
  },
  cases: [
    {
      id: 'case_001',
      case_no: 'CASE-001',
      utterance: '请帮我设置温度180度',
      expected_route: 'intent',
      expected_intent: 'device.control',
      expected_slots: { temperature: 180 },
    },
  ],
  results: [],
  metrics: { accuracy: 0, response_p95_ms: 0 },
  analysis: { summary: { total_cases: 1 }, root_causes: [], recommendations: [], confusion_matrix: [] },
}

const completedPayload = {
  ...readyPayload,
  batch: {
    ...readyPayload.batch,
    status: 'completed',
    executed_count: 1,
    pass_count: 0,
    accuracy: 0,
    response_p95_ms: 2430,
  },
  results: [
    {
      id: 'result_001',
      case_id: 'case_001',
      actual_route: 'knowledge',
      actual_intent: 'knowledge.query',
      actual_slots: { temperature: 180 },
      score: 0.58,
      latency_ms: 2430,
      passed: false,
      failure_reason: 'intent_mismatch',
    },
  ],
  metrics: { accuracy: 0, response_p95_ms: 2430 },
  analysis: {
    summary: { total_cases: 1, pass_count: 0, failed_count: 1 },
    root_causes: [{ reason: 'intent_mismatch', count: 1 }],
    recommendations: ['补充 remaining-time 场景样本并校准知识/指令边界。'],
    confusion_matrix: [{ expected_intent: 'device.control', actual_intent: 'knowledge.query', count: 1 }],
  },
}

const runningPayload = {
  ...readyPayload,
  batch: {
    ...readyPayload.batch,
    status: 'running',
    analysis_status: 'pending',
  },
}


describe('BatchTestDetailPage', () => {
  beforeEach(() => {
    apiMocks.fetchBatchTestDetail
      .mockResolvedValueOnce(readyPayload)
      .mockResolvedValueOnce(readyPayload)
      .mockResolvedValueOnce(runningPayload)
      .mockResolvedValueOnce(completedPayload)
    apiMocks.generateBatchTestCases.mockResolvedValue({ batch: { ...readyPayload.batch, status: 'ready' } })
    apiMocks.executeBatchTest.mockResolvedValue({ batch: { ...readyPayload.batch, status: 'running' } })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('generates cases and shows execution analysis', async () => {
    render(
      <MemoryRouter initialEntries={['/batch-tests/batch_001']}>
        <Routes>
          <Route path="/batch-tests/:batchId" element={<BatchTestDetailPage token="token-admin" />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '回归批次A' })).toBeInTheDocument()
      expect(screen.getByText('CASE-001')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '自动生成用例' }))

    await waitFor(() => {
      expect(apiMocks.generateBatchTestCases).toHaveBeenCalledWith('token-admin', 'batch_001', { mode: 'auto' })
    })
    messageMocks.success.mockClear()

    fireEvent.click(screen.getByRole('button', { name: '执行批次' }))
    expect(apiMocks.executeBatchTest).toHaveBeenCalledWith('token-admin', 'batch_001', {})

    expect(messageMocks.success).not.toHaveBeenCalledWith('批次执行完成，结果已刷新')

    await waitFor(() => {
      fireEvent.click(screen.getByRole('tab', { name: '执行结果' }))
      expect(screen.getByText(/intent_mismatch/)).toBeInTheDocument()
      expect(messageMocks.success).toHaveBeenCalledWith('批次执行完成，结果已刷新')
    }, { timeout: 2500 })

    expect(screen.getByText(/command_response_p95_ms/)).toBeInTheDocument()
    expect(screen.getAllByText(/\{"temperature":180\}/)).toHaveLength(2)

    fireEvent.click(screen.getByRole('tab', { name: '智能分析' }))

    await waitFor(() => {
      expect(screen.getByText(/remaining-time/)).toBeInTheDocument()
      expect(screen.getAllByText(/knowledge\.query/).length).toBeGreaterThan(0)
    })
  })
})

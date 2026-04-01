import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { IntentLibraryPage } from './IntentLibraryPage'


const apiMocks = vi.hoisted(() => ({
  fetchIntentLibraries: vi.fn(),
  fetchIntentLibraryDetail: vi.fn(),
  createIntentLibrary: vi.fn(),
  trainIntentLibraryModel: vi.fn(),
  evaluateIntentModel: vi.fn(),
  publishIntentModel: vi.fn(),
  downloadIntentModel: vi.fn(),
  runIntentModelSingleTest: vi.fn(),
}))


vi.mock('../../services/api', () => apiMocks)


const listPayload = {
  items: [
    {
      id: 'lib_001',
      library_key: 'zh_core_v1',
      name: '中文指令库',
      language: 'zh',
      model_count: 1,
      default_thresholds: { command_intent_accuracy_min: 0.95 },
    },
  ],
}

const detailPayload = {
  library: listPayload.items[0],
  datasets: [
    { id: 'ds_train', dataset_type: 'training', name: '训练集A', sample_count: 39 },
    { id: 'ds_eval', dataset_type: 'evaluation', name: '评估集', sample_count: 39 },
  ],
  models: [
    { id: 'model_001', version_name: 'v1.0.0', status: 'trained', is_testable: false, is_published: false },
  ],
  evaluation_runs: [],
  partial_requirements: ['FR-050 Partial'],
}


describe('IntentLibraryPage', () => {
  beforeEach(() => {
    apiMocks.fetchIntentLibraries.mockResolvedValue(listPayload)
    apiMocks.fetchIntentLibraryDetail.mockResolvedValue(detailPayload)
    apiMocks.createIntentLibrary.mockResolvedValue({ library: listPayload.items[0] })
    apiMocks.trainIntentLibraryModel.mockResolvedValue({ model: { id: 'model_001', status: 'training' } })
    apiMocks.evaluateIntentModel.mockResolvedValue({ evaluation_run: { id: 'run_001', status: 'running' } })
    apiMocks.publishIntentModel.mockResolvedValue({ model: { id: 'model_001', is_published: true } })
    apiMocks.downloadIntentModel.mockResolvedValue({ artifact_format: 'zip', artifact_uri: '/artifacts/model_001.zip' })
    apiMocks.runIntentModelSingleTest.mockResolvedValue({
      intent: 'device.on',
      confidence: 0.96,
      slots: { device: '烤箱' },
      latency_ms: 42,
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('loads the library directory and detail view', async () => {
    render(<IntentLibraryPage token="token-admin" />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '指令库管理' })).toBeInTheDocument()
      expect(screen.getAllByText('中文指令库').length).toBeGreaterThan(0)
      expect(screen.getByText('FR-050 Partial')).toBeInTheDocument()
    })

    expect(apiMocks.fetchIntentLibraries).toHaveBeenCalledWith('token-admin')
    expect(apiMocks.fetchIntentLibraryDetail).toHaveBeenCalledWith('token-admin', 'lib_001')
  })

  it('creates a library and triggers train, evaluate, publish and single test flows', async () => {
    render(<IntentLibraryPage token="token-admin" />)

    await waitFor(() => {
      expect(screen.getAllByText('中文指令库').length).toBeGreaterThan(0)
    })

    fireEvent.click(screen.getByRole('button', { name: '新建指令库' }))
    fireEvent.change(screen.getByLabelText('唯一 Key'), { target: { value: 'zh_core_v2' } })
    fireEvent.change(screen.getByLabelText('名称'), { target: { value: '中文指令库 2' } })
    fireEvent.click(screen.getByRole('button', { name: /创\s*建/ }))

    await waitFor(() => {
      expect(apiMocks.createIntentLibrary).toHaveBeenCalled()
    })

    fireEvent.click(screen.getByRole('button', { name: '发起训练' }))
    fireEvent.click(screen.getByRole('button', { name: '发起评估' }))
    fireEvent.click(screen.getByRole('button', { name: '发布模型' }))
    fireEvent.click(screen.getByRole('button', { name: '下载元数据' }))
    fireEvent.change(screen.getByLabelText('单条测试'), { target: { value: '帮我打开烤箱，预热200度' } })
    fireEvent.click(screen.getByRole('button', { name: '执行测试' }))

    await waitFor(() => {
      expect(apiMocks.trainIntentLibraryModel).toHaveBeenCalledWith('token-admin', 'lib_001', expect.any(Object))
      expect(apiMocks.evaluateIntentModel).toHaveBeenCalledWith('token-admin', 'model_001', expect.any(Object))
      expect(apiMocks.publishIntentModel).toHaveBeenCalledWith('token-admin', 'model_001', expect.any(Object))
      expect(apiMocks.downloadIntentModel).toHaveBeenCalledWith('token-admin', 'model_001')
      expect(apiMocks.runIntentModelSingleTest).toHaveBeenCalledWith('token-admin', 'model_001', {
        utterance: '帮我打开烤箱，预热200度',
      })
    })

    expect(await screen.findByText('device.on')).toBeInTheDocument()
  })
})

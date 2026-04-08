import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { IntentLibraryDetailPage } from './IntentLibraryDetailPage'

const apiMocks = vi.hoisted(() => ({
  fetchIntentLibraryDetail: vi.fn(),
  trainIntentLibraryModel: vi.fn(),
  publishIntentModel: vi.fn(),
  downloadIntentModel: vi.fn(),
}))

vi.mock('../../services/api', () => apiMocks)

const detailPayload = {
  library: {
    id: 'lib_001',
    library_key: 'zh_core_v1',
    name: '中文指令库',
    language: 'zh',
  },
  datasets: [
    { id: 'ds_train', dataset_type: 'training', name: '训练集A', sample_count: 39 },
    { id: 'ds_eval', dataset_type: 'evaluation', name: '评估集', sample_count: 39 },
  ],
  models: [
    { id: 'model_001', version_name: 'v1.0.0', status: 'trained', is_testable: false, is_published: false },
    { id: 'model_002', version_name: 'v1.0.1', status: 'testable', is_testable: true, is_published: false },
  ],
  evaluation_runs: [],
  partial_requirements: ['FR-050 Partial'],
}

const trainedOnlyPayload = {
  ...detailPayload,
  models: [
    { id: 'model_010', version_name: 'v1.0.0', status: 'trained', is_testable: false, is_published: false },
  ],
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/intent-library/lib_001']}>
      <Routes>
        <Route path="/intent-library/:libraryId" element={<IntentLibraryDetailPage token="token-admin" />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('IntentLibraryDetailPage', () => {
  beforeEach(() => {
    apiMocks.fetchIntentLibraryDetail.mockResolvedValue(detailPayload)
    apiMocks.trainIntentLibraryModel.mockResolvedValue({ model: { id: 'model_003' } })
    apiMocks.publishIntentModel.mockResolvedValue({ model: { id: 'model_002', is_published: true } })
    apiMocks.downloadIntentModel.mockResolvedValue({ artifact_format: 'zip', artifact_uri: '/artifacts/model_002.zip' })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('renders a dedicated detail page with navigation actions', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '中文指令库' })).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: '返回指令库列表' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '数据集管理' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '模型测试' })).toBeInTheDocument()
    expect(screen.getByText('FR-050 Partial')).toBeInTheDocument()
  })

  it('triggers train, publish and download actions from the detail page', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '发起训练' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '发起训练' }))
    await waitFor(() => {
      expect(apiMocks.trainIntentLibraryModel).toHaveBeenCalledWith(
        'token-admin',
        'lib_001',
        expect.objectContaining({ training_dataset_id: 'ds_train' }),
      )
    })

    fireEvent.click(screen.getByRole('button', { name: '发布模型' }))
    await waitFor(() => {
      expect(apiMocks.publishIntentModel).toHaveBeenCalledWith('token-admin', 'model_002', { note: 'ready' })
    })

    fireEvent.click(screen.getByRole('button', { name: '下载元数据' }))
    await waitFor(() => {
      expect(apiMocks.downloadIntentModel).toHaveBeenCalledWith('token-admin', 'model_002')
      expect(screen.getByText('/artifacts/model_002.zip')).toBeInTheDocument()
    })
  })

  it('shows publish guidance when no model is ready for publish', async () => {
    apiMocks.fetchIntentLibraryDetail.mockResolvedValueOnce(trainedOnlyPayload)
    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '发布模型' })).toBeDisabled()
    })

    expect(screen.getByText('当前没有可直接发布的模型，请先完成评估并进入 testable 状态。')).toBeInTheDocument()
  })
})

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { IntentLibraryDatasetsPage } from './IntentLibraryDatasetsPage'

const apiMocks = vi.hoisted(() => ({
  fetchIntentLibraryDetail: vi.fn(),
  createIntentDataset: vi.fn(),
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
    { id: 'ds_train', dataset_type: 'training', name: '训练集A', sample_count: 39, bound_model_id: null },
    { id: 'ds_eval', dataset_type: 'evaluation', name: '评估集A', sample_count: 39, bound_model_id: 'model_001' },
  ],
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/intent-library/lib_001/datasets']}>
      <Routes>
        <Route path="/intent-library/:libraryId/datasets" element={<IntentLibraryDatasetsPage token="token-admin" />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('IntentLibraryDatasetsPage', () => {
  beforeEach(() => {
    apiMocks.fetchIntentLibraryDetail.mockResolvedValue(detailPayload)
    apiMocks.createIntentDataset.mockResolvedValue({ dataset: { id: 'ds_llm', name: 'LLM扩充集' } })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('renders the datasets page with create and llm generation actions', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '数据集管理' })).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: '新建数据集' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'LLM 合成' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '导入数据集' })).toBeInTheDocument()
    expect(screen.getByText('训练集A')).toBeInTheDocument()
  })

  it('creates a dataset and refreshes the catalog', async () => {
    apiMocks.fetchIntentLibraryDetail
      .mockResolvedValueOnce(detailPayload)
      .mockResolvedValueOnce({
        ...detailPayload,
        datasets: [...detailPayload.datasets, { id: 'ds_llm', dataset_type: 'training', name: 'LLM扩充集', sample_count: 12 }],
      })

    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '新建数据集' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '新建数据集' }))
    fireEvent.change(screen.getByLabelText('数据集名称'), { target: { value: 'LLM扩充集' } })
    fireEvent.click(screen.getByRole('button', { name: '保存数据集' }))

    await waitFor(() => {
      expect(apiMocks.createIntentDataset).toHaveBeenCalledWith(
        'token-admin',
        'lib_001',
        expect.objectContaining({ name: 'LLM扩充集', dataset_type: 'training' }),
      )
      expect(screen.getByText('LLM扩充集')).toBeInTheDocument()
    })
  })

  it('creates an imported dataset through the import entry', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '导入数据集' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '导入数据集' }))
    fireEvent.change(screen.getByLabelText('数据集名称'), { target: { value: '导入训练集' } })
    fireEvent.change(screen.getByLabelText('导入样本'), { target: { value: '打开烤箱\n关闭烤箱' } })
    fireEvent.click(screen.getByRole('button', { name: '保存数据集' }))

    await waitFor(() => {
      expect(apiMocks.createIntentDataset).toHaveBeenCalledWith(
        'token-admin',
        'lib_001',
        expect.objectContaining({ name: '导入训练集', source: 'import', entries: ['打开烤箱', '关闭烤箱'] }),
      )
    })
  })
})

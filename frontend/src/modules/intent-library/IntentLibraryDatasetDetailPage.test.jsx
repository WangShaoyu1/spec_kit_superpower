import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { IntentLibraryDatasetDetailPage } from './IntentLibraryDatasetDetailPage'

const apiMocks = vi.hoisted(() => ({
  fetchIntentDatasetDetail: vi.fn(),
  saveIntentDatasetDetail: vi.fn(),
}))

vi.mock('../../services/api', () => apiMocks)

const detailPayload = {
  library: { id: 'lib_001', name: '中文指令库' },
  dataset: {
    id: 'ds_train',
    name: '训练集A',
    dataset_type: 'training',
    source: 'import',
    sample_count: 1,
    schema_version: '1.0',
  },
  samples: [
    {
      intent_key: 'device.on',
      display_name: '打开设备',
      required_slots: [{ name: 'device' }],
      prompt_samples: ['打开烤箱'],
      negative_samples: [],
      entities: [{ entity_name: 'device', values: ['烤箱'] }],
    },
  ],
}

const multiSampleDetailPayload = {
  ...detailPayload,
  dataset: {
    ...detailPayload.dataset,
    sample_count: 2,
  },
  samples: [
    detailPayload.samples[0],
    {
      intent_key: 'device.off',
      display_name: '关闭设备',
      required_slots: [{ name: 'device' }],
      prompt_samples: ['关闭烤箱'],
      negative_samples: [],
      entities: [{ entity_name: 'device', values: ['烤箱'] }],
    },
  ],
}

const emptyDetailPayload = {
  ...detailPayload,
  dataset: {
    ...detailPayload.dataset,
    sample_count: 0,
  },
  samples: [],
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/intent-library/lib_001/datasets/ds_train']}>
      <Routes>
        <Route
          path="/intent-library/:libraryId/datasets/:datasetId"
          element={<IntentLibraryDatasetDetailPage token="token-admin" />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('IntentLibraryDatasetDetailPage', () => {
  beforeEach(() => {
    apiMocks.fetchIntentDatasetDetail.mockResolvedValue(detailPayload)
    apiMocks.saveIntentDatasetDetail.mockResolvedValue({ dataset: detailPayload.dataset, samples: detailPayload.samples })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('renders deep-ui actions for dataset detail management', async () => {
    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '训练集A' })).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: '意图配置' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '新增问法' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '批量导入实体' })).toBeInTheDocument()
  })

  it('saves intent updates through the dataset detail API and reloads the latest snapshot', async () => {
    apiMocks.fetchIntentDatasetDetail
      .mockResolvedValueOnce(detailPayload)
      .mockResolvedValueOnce({
        ...detailPayload,
        samples: [
          {
            ...detailPayload.samples[0],
            display_name: '打开烤箱设备',
          },
        ],
      })

    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '意图配置' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '意图配置' }))
    fireEvent.change(screen.getByLabelText('显示名称'), { target: { value: '打开烤箱设备' } })
    fireEvent.click(screen.getByRole('button', { name: '保存意图配置' }))

    await waitFor(() => {
      expect(apiMocks.saveIntentDatasetDetail).toHaveBeenCalledWith(
        'token-admin',
        'lib_001',
        'ds_train',
        expect.objectContaining({
          samples: [expect.objectContaining({ display_name: '打开烤箱设备' })],
        }),
      )
      expect(screen.getByText('打开烤箱设备')).toBeInTheDocument()
    })
  })

  it('updates the selected sample instead of always mutating the first one', async () => {
    apiMocks.fetchIntentDatasetDetail
      .mockResolvedValueOnce(multiSampleDetailPayload)
      .mockResolvedValueOnce({
        ...multiSampleDetailPayload,
        samples: [
          multiSampleDetailPayload.samples[0],
          {
            ...multiSampleDetailPayload.samples[1],
            intent_key: 'device.off.oven',
            display_name: '关闭烤箱设备',
          },
        ],
      })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('关闭设备')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('关闭设备'))
    fireEvent.click(screen.getByRole('button', { name: '意图配置' }))
    fireEvent.change(screen.getByLabelText('Intent Key'), { target: { value: 'device.off.oven' } })
    fireEvent.change(screen.getByLabelText('显示名称'), { target: { value: '关闭烤箱设备' } })
    fireEvent.click(screen.getByRole('button', { name: '保存意图配置' }))

    await waitFor(() => {
      expect(apiMocks.saveIntentDatasetDetail).toHaveBeenCalledWith(
        'token-admin',
        'lib_001',
        'ds_train',
        expect.objectContaining({
          samples: [
            expect.objectContaining({ display_name: '打开设备' }),
            expect.objectContaining({ intent_key: 'device.off.oven', display_name: '关闭烤箱设备' }),
          ],
        }),
      )
      expect(screen.getByText('关闭烤箱设备')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '意图配置' }))

    await waitFor(() => {
      expect(screen.getByDisplayValue('device.off.oven')).toBeInTheDocument()
      expect(screen.getByDisplayValue('关闭烤箱设备')).toBeInTheDocument()
    })
  })

  it('shows negative-sample readback after saving exclusion samples', async () => {
    apiMocks.fetchIntentDatasetDetail
      .mockResolvedValueOnce(detailPayload)
      .mockResolvedValueOnce({
        ...detailPayload,
        samples: [
          {
            ...detailPayload.samples[0],
            negative_samples: ['不要打开烤箱'],
          },
        ],
      })

    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '相似问/排除问' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '相似问/排除问' }))
    fireEvent.change(screen.getByLabelText('排除问'), { target: { value: '不要打开烤箱' } })
    fireEvent.click(screen.getByRole('button', { name: '保存排除问' }))

    await waitFor(() => {
      expect(screen.getByText('不要打开烤箱')).toBeInTheDocument()
    })
  })

  it('bootstraps the first sample for a manual empty dataset', async () => {
    apiMocks.fetchIntentDatasetDetail
      .mockResolvedValueOnce(emptyDetailPayload)
      .mockResolvedValueOnce({
        ...detailPayload,
        samples: [
          {
            intent_key: 'device.bootstrap',
            display_name: '初始化样本',
            required_slots: [],
            prompt_samples: [],
            negative_samples: [],
            entities: [],
          },
        ],
      })

    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '意图配置' })).toBeInTheDocument()
    })

    expect(screen.getByText('当前数据集暂无样本')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '意图配置' }))
    fireEvent.change(screen.getByLabelText('Intent Key'), { target: { value: 'device.bootstrap' } })
    fireEvent.change(screen.getByLabelText('显示名称'), { target: { value: '初始化样本' } })
    fireEvent.click(screen.getByRole('button', { name: '保存意图配置' }))

    await waitFor(() => {
      expect(apiMocks.saveIntentDatasetDetail).toHaveBeenCalledWith(
        'token-admin',
        'lib_001',
        'ds_train',
        expect.objectContaining({
          samples: [expect.objectContaining({ intent_key: 'device.bootstrap', display_name: '初始化样本' })],
        }),
      )
      expect(screen.getByText('初始化样本')).toBeInTheDocument()
    })
  })

  it('keeps the intent dialog open when saving fails', async () => {
    apiMocks.saveIntentDatasetDetail.mockRejectedValueOnce(new Error('保存失败'))

    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '意图配置' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '意图配置' }))
    fireEvent.change(screen.getByLabelText('显示名称'), { target: { value: '保存失败后的名称' } })
    fireEvent.click(screen.getByRole('button', { name: '保存意图配置' }))

    await waitFor(() => {
      expect(apiMocks.saveIntentDatasetDetail).toHaveBeenCalled()
    })

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByDisplayValue('保存失败后的名称')).toBeInTheDocument()
    expect(screen.queryByText('保存失败后的名称')).not.toBeInTheDocument()
  })
})

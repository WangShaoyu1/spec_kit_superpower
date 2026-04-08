import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from '../../App'

function jsonResponse(payload) {
  return Promise.resolve({
    ok: true,
    json: async () => payload,
  })
}

const session = {
  access_token: 'token-admin',
  capabilities: ['intent_library_read', 'intent_library_write', 'test_execute'],
}

const listPayload = {
  code: '000000',
  message: 'success',
  data: {
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
  },
}

const detailPayload = {
  code: '000000',
  message: 'success',
  data: {
    library: listPayload.data.items[0],
    datasets: [
      { id: 'ds_train', dataset_type: 'training', name: '训练集A', sample_count: 39 },
      { id: 'ds_eval', dataset_type: 'evaluation', name: '评估集', sample_count: 39 },
    ],
    models: [
      { id: 'model_001', version_name: 'v1.0.0', status: 'trained', is_testable: false, is_published: false },
      { id: 'model_002', version_name: 'v1.0.1', status: 'testable', is_testable: true, is_published: false },
    ],
    evaluation_runs: [
      {
        id: 'run_001',
        status: 'succeeded',
        metrics: {
          command_intent_accuracy: 0.96,
          slot_f1: 0.92,
          response_p95_ms: 1800,
        },
        analysis: {
          summary: '批量评估完成，指标达到冻结门槛。',
          recommendations: ['FR-050 当前仍仅支持库默认值与任务快照覆盖。'],
        },
      },
    ],
    partial_requirements: ['FR-050 Partial'],
  },
}

function mockIntentLibraryFetches() {
  return vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
    const target = String(url)

    if (target.includes('/api/v1/intent-libraries/lib_001/datasets/ds_train')) {
      return jsonResponse({
        code: '000000',
        message: 'success',
        data: {
          library: listPayload.data.items[0],
          dataset: {
            id: 'ds_train',
            name: '训练集A',
            dataset_type: 'training',
            source: 'import',
            bound_model_id: 'model_002',
            sample_count: 39,
            schema_version: '1.0',
          },
          samples: [
            {
              intent_key: 'AI_cooking_page_open',
              display_name: '选择智能烹饪模式',
              required_slots: [],
              optional_slots: [],
              prompt_samples: [],
            },
          ],
        },
      })
    }

    if (target.includes('/api/v1/intent-libraries/lib_001')) {
      return jsonResponse(detailPayload)
    }

    if (target.includes('/api/v1/intent-libraries')) {
      return jsonResponse(listPayload)
    }

    if (target.includes('/api/v1/models/model_002/single-test')) {
      return jsonResponse({
        code: '000000',
        message: 'success',
        data: {
          intent: 'device.on',
          confidence: 0.96,
          slots: { device: '烤箱' },
          latency_ms: 42,
          model_version: 'v1.0.1',
          model_status: 'testable',
        },
      })
    }

    throw new Error(`Unhandled fetch in intent route test: ${target}`)
  })
}

describe('Intent library routes', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('smartchef-session', JSON.stringify(session))
    vi.restoreAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    cleanup()
  })

  it('renders the detail route as a dedicated page with return and child navigation actions', async () => {
    window.history.pushState({}, '', '/intent-library/lib_001')
    mockIntentLibraryFetches()

    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '中文指令库' })).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: '返回指令库列表' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '数据集管理' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '模型测试' })).toBeInTheDocument()
  })

  it('navigates from detail to datasets and back to the library detail page', async () => {
    window.history.pushState({}, '', '/intent-library/lib_001')
    mockIntentLibraryFetches()

    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '数据集管理' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '数据集管理' }))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '数据集管理' })).toBeInTheDocument()
      expect(window.location.pathname).toBe('/intent-library/lib_001/datasets')
    })

    fireEvent.click(screen.getByRole('button', { name: '返回指令库详情' }))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '中文指令库' })).toBeInTheDocument()
      expect(window.location.pathname).toBe('/intent-library/lib_001')
    })
  })

  it('renders the model test route with single and batch testing tabs', async () => {
    window.history.pushState({}, '', '/intent-library/lib_001/test')
    mockIntentLibraryFetches()

    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '模型测试' })).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: '返回指令库详情' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '单条测试' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '批量测试' })).toBeInTheDocument()
  })

  it('uses the current testable model for single test requests', async () => {
    window.history.pushState({}, '', '/intent-library/lib_001/test')
    const fetchSpy = mockIntentLibraryFetches()

    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '模型测试' })).toBeInTheDocument()
    })

    fireEvent.change(screen.getByRole('textbox', { name: '单条测试' }), { target: { value: '帮我打开烤箱，预热200度' } })
    fireEvent.click(screen.getByRole('button', { name: '执行测试' }))

    await waitFor(() => {
      expect(screen.getByText('device.on')).toBeInTheDocument()
      expect(screen.getByText('模型版本 v1.0.1')).toBeInTheDocument()
      expect(screen.getByText('当前状态 testable')).toBeInTheDocument()
    })

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/models/model_002/single-test'),
      expect.any(Object),
    )
  })

  it('shows batch evaluation analysis on the test page', async () => {
    window.history.pushState({}, '', '/intent-library/lib_001/test')
    mockIntentLibraryFetches()

    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '模型测试' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('tab', { name: '批量测试' }))

    await waitFor(() => {
      expect(screen.getByText('批量评估完成，指标达到冻结门槛。')).toBeInTheDocument()
      expect(screen.getByText('FR-050 当前仍仅支持库默认值与任务快照覆盖。')).toBeInTheDocument()
    })
  })

  it('renders the dataset detail route and supports returning to the datasets page', async () => {
    window.history.pushState({}, '', '/intent-library/lib_001/datasets/ds_train')
    mockIntentLibraryFetches()

    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '训练集A' })).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: '返回数据集列表' })).toBeInTheDocument()
    expect(screen.getByText('AI_cooking_page_open')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '返回数据集列表' }))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '数据集管理' })).toBeInTheDocument()
      expect(window.location.pathname).toBe('/intent-library/lib_001/datasets')
      expect(screen.getByRole('table')).toBeInTheDocument()
    })
  })
})

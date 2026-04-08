import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  createIntentLibrary,
  createIntentDataset,
  deleteIntentLibrary,
  downloadIntentModel,
  evaluateIntentModel,
  fetchIntentDatasetDetail,
  fetchIntentLibraries,
  fetchIntentLibraryDetail,
  publishIntentModel,
  runIntentModelSingleTest,
  saveIntentDatasetDetail,
  trainIntentLibraryModel,
} from './api'


function success(data = {}) {
  return Promise.resolve({
    ok: true,
    json: async () => ({ code: '000000', message: 'success', data }),
  })
}


describe('intent-library api', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('requests the intent-library directory, detail and dataset detail with auth headers', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(() => success({ items: [] }))

    await fetchIntentLibraries('token-admin')
    await fetchIntentLibraryDetail('token-admin', 'lib_001')
    await fetchIntentDatasetDetail('token-admin', 'lib_001', 'ds_train')

    expect(fetchSpy).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining('/api/v1/intent-libraries'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
    expect(fetchSpy).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('/api/v1/intent-libraries/lib_001'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
    expect(fetchSpy).toHaveBeenNthCalledWith(
      3,
      expect.stringContaining('/api/v1/intent-libraries/lib_001/datasets/ds_train'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
  })

  it('sends create, delete, dataset and model requests', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(() => success({}))

    await createIntentLibrary('token-admin', {
      library_key: 'zh_core_v1',
      name: '中文指令库',
      language: 'zh',
      description: '正式指令库',
      default_thresholds: { command_intent_accuracy_min: 0.95 },
    })
    await deleteIntentLibrary('token-admin', 'lib_001')
    await createIntentDataset('token-admin', 'lib_001', {
      name: '训练集C',
      dataset_type: 'training',
      source: 'llm',
      sample_count: 12,
    })
    await saveIntentDatasetDetail('token-admin', 'lib_001', 'ds_train', {
      samples: [{ intent_key: 'device.on', display_name: '打开设备' }],
    })
    await trainIntentLibraryModel('token-admin', 'lib_001', { training_dataset_id: 'ds_train', version_name: 'v1.0.0' })
    await evaluateIntentModel('token-admin', 'model_001', {
      evaluation_dataset_id: 'ds_eval',
      threshold_override: { slot_f1_min: 0.91 },
    })
    await publishIntentModel('token-admin', 'model_001', { note: 'ready' })
    await downloadIntentModel('token-admin', 'model_001')
    await runIntentModelSingleTest('token-admin', 'model_001', { utterance: '帮我打开烤箱，预热200度' })

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/intent-libraries'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/intent-libraries/lib_001'),
      expect.objectContaining({ method: 'DELETE' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/intent-libraries/lib_001/datasets'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/intent-libraries/lib_001/datasets/ds_train'),
      expect.objectContaining({ method: 'PUT' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/intent-libraries/lib_001/models/train'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/models/model_001/evaluate'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/models/model_001/publish'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/models/model_001/download'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/models/model_001/single-test'),
      expect.objectContaining({ method: 'POST' }),
    )
  })
})

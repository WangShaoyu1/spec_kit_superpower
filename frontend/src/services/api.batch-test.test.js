import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  createBatchTest,
  executeBatchTest,
  fetchBatchTestDetail,
  fetchBatchTests,
  generateBatchTestCases,
} from './api'


function success(data = {}) {
  return Promise.resolve({
    ok: true,
    json: async () => ({ code: '000000', message: 'success', data }),
  })
}


describe('batch-test api', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('requests batch directory and detail with auth headers', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(() => success({ items: [] }))

    await fetchBatchTests('token-admin', { status: 'completed' })
    await fetchBatchTestDetail('token-admin', 'batch_001')

    expect(fetchSpy).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining('/api/v1/batch-tests?status=completed'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
    expect(fetchSpy).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('/api/v1/batch-tests/batch_001'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
  })

  it('sends create, generate and execute requests', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(() => success({}))

    await createBatchTest('token-admin', { name: '方案回归批次' })
    await generateBatchTestCases('token-admin', 'batch_001', { mode: 'auto' })
    await executeBatchTest('token-admin', 'batch_001', {})

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/batch-tests'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/batch-tests/batch_001/generate-cases'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/batch-tests/batch_001/execute'),
      expect.objectContaining({ method: 'POST' }),
    )
  })
})

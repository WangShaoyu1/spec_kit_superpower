import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  createMonitoringAlertRule,
  fetchMonitoringAlertRules,
  fetchMonitoringDeviceSessions,
  fetchMonitoringOverview,
  fetchMonitoringRequestLogs,
  fetchMonitoringSessionDetail,
  updateMonitoringAlertRule,
} from './api'


function success(data = {}) {
  return Promise.resolve({
    ok: true,
    json: async () => ({ code: '000000', message: 'success', data }),
  })
}


describe('monitoring api', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('requests overview, logs, device sessions and session detail with auth headers', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(() => success({ items: [] }))

    await fetchMonitoringOverview('token-admin', { window: '15m' })
    await fetchMonitoringRequestLogs('token-admin', { device_id: 'device_a', route: 'intent' })
    await fetchMonitoringDeviceSessions('token-admin', { device_id: 'device_a' })
    await fetchMonitoringSessionDetail('token-admin', 'session_a')

    expect(fetchSpy).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining('/api/v1/monitoring/overview?window=15m'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
    expect(fetchSpy).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('/api/v1/monitoring/request-logs?device_id=device_a&route=intent'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
    expect(fetchSpy).toHaveBeenNthCalledWith(
      3,
      expect.stringContaining('/api/v1/monitoring/device-sessions?device_id=device_a'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
    expect(fetchSpy).toHaveBeenNthCalledWith(
      4,
      expect.stringContaining('/api/v1/monitoring/sessions/session_a'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
  })

  it('sends alert rule create and update requests', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(() => success({}))

    await fetchMonitoringAlertRules('token-admin')
    await createMonitoringAlertRule('token-admin', { name: '错误率突增' })
    await updateMonitoringAlertRule('token-admin', 'rule_001', { enabled: false })

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/monitoring/alert-rules'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/monitoring/alert-rules'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/monitoring/alert-rules/rule_001'),
      expect.objectContaining({ method: 'PATCH' }),
    )
  })
})

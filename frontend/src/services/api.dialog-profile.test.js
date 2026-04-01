import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  createDialogProfile,
  createDialogProfileSession,
  fetchDialogProfileDetail,
  fetchDialogProfiles,
  fetchDialogProfileSession,
  publishDialogProfile,
  sendDialogProfileMessage,
  updateDialogProfile,
} from './api'


function success(data = {}) {
  return Promise.resolve({
    ok: true,
    json: async () => ({ code: '000000', message: 'success', data }),
  })
}


describe('dialog-profile api', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('requests directory, detail and session with auth headers', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(() => success({ items: [] }))

    await fetchDialogProfiles('token-admin', { status: 'draft' })
    await fetchDialogProfileDetail('token-admin', 'profile_001')
    await fetchDialogProfileSession('token-admin', 'session_001')

    expect(fetchSpy).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining('/api/v1/dialog-profiles?status=draft'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
    expect(fetchSpy).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('/api/v1/dialog-profiles/profile_001'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
    expect(fetchSpy).toHaveBeenNthCalledWith(
      3,
      expect.stringContaining('/api/v1/test-sessions/session_001'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
  })

  it('sends create, update, publish and message requests', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(() => success({}))

    await createDialogProfile('token-admin', { name: '方案A' })
    await updateDialogProfile('token-admin', 'profile_001', { name: '方案A-正式' })
    await publishDialogProfile('token-admin', 'profile_001', { note: 'ready' })
    await createDialogProfileSession('token-admin', 'profile_001', {
      name: '会话A',
      device_context: { device_id: 'device_a' },
    })
    await sendDialogProfileMessage('token-admin', 'session_001', {
      text: '开始烹饪',
      device_context: { device_id: 'device_a' },
    })

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/dialog-profiles'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/dialog-profiles/profile_001'),
      expect.objectContaining({ method: 'PATCH' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/dialog-profiles/profile_001/publish'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/dialog-profiles/profile_001/test-sessions'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/test-sessions/session_001/messages'),
      expect.objectContaining({ method: 'POST' }),
    )
  })
})

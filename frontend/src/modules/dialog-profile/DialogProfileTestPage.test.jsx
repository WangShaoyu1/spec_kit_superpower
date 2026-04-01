import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { DialogProfileTestPage } from './DialogProfileTestPage'


const apiMocks = vi.hoisted(() => ({
  fetchDialogProfileDetail: vi.fn(),
  createDialogProfileSession: vi.fn(),
  fetchDialogProfileSession: vi.fn(),
  sendDialogProfileMessage: vi.fn(),
}))


vi.mock('../../services/api', () => apiMocks)


describe('DialogProfileTestPage', () => {
  beforeEach(() => {
    apiMocks.fetchDialogProfileDetail.mockResolvedValue({
      profile: { id: 'profile_001', name: '方案A' },
    })
    apiMocks.createDialogProfileSession
      .mockResolvedValueOnce({
        session: { id: 'session_001', name: '默认会话', message_count: 0 },
      })
      .mockResolvedValueOnce({
        session: { id: 'session_002', name: '会话 2', message_count: 0 },
      })
    apiMocks.fetchDialogProfileSession.mockImplementation((_token, sessionId) => {
      if (sessionId === 'session_002') {
        return Promise.resolve({
          session: { id: 'session_002', name: '会话 2', message_count: 0 },
          messages: [],
        })
      }
      return Promise.resolve({
        session: { id: 'session_001', name: '默认会话', message_count: 2 },
        messages: [
          { id: 'm1', role: 'user', text: '开始烹饪' },
          { id: 'm2', role: 'assistant', text: '厨房助手：指令已记录，正在按 device.control 执行。', response_time_ms: 12 },
        ],
      })
    })
    apiMocks.sendDialogProfileMessage.mockResolvedValue({
      assistant_message: { id: 'm2', text: '厨房助手：指令已记录，正在按 device.control 执行。', response_time_ms: 12 },
      debug_trace: {
        route: { type: 'intent', confidence: 0.96 },
        intent: { name: 'device.control', confidence: 0.94 },
        model: 'gpt-4o-mini',
        slots: { device_id: 'device_a' },
        response_text: '厨房助手：指令已记录，正在按 device.control 执行。',
        device_context_snapshot: { device_id: 'device_a', page: 'recipe', cooking: true },
      },
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('creates sessions, sends messages and renders trace', async () => {
    render(
      <MemoryRouter initialEntries={['/dialog-profiles/profile_001/test']}>
        <Routes>
          <Route path="/dialog-profiles/:profileId/test" element={<DialogProfileTestPage token="token-admin" />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '方案A' })).toBeInTheDocument()
      expect(screen.getByText('默认会话')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '新建会话' }))
    await waitFor(() => {
      expect(screen.getByText('会话 2')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('测试消息'), { target: { value: '开始烹饪' } })
    fireEvent.click(screen.getByRole('button', { name: '发送消息' }))

    await waitFor(() => {
      expect(apiMocks.sendDialogProfileMessage).toHaveBeenCalled()
      expect(screen.getByText(/route: intent \(0.96\)/)).toBeInTheDocument()
      expect(screen.getByText(/intent: device.control \(0.94\)/)).toBeInTheDocument()
      expect(screen.getByText(/response: 厨房助手/)).toBeInTheDocument()
    })
  })
})

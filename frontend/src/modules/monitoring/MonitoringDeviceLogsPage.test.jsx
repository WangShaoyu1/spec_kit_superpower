import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { MonitoringDeviceLogsPage } from './MonitoringDeviceLogsPage'


const apiMocks = vi.hoisted(() => ({
  fetchMonitoringDeviceSessions: vi.fn(),
  fetchMonitoringSessionDetail: vi.fn(),
}))


vi.mock('../../services/api', () => apiMocks)


describe('MonitoringDeviceLogsPage', () => {
  beforeEach(() => {
    apiMocks.fetchMonitoringDeviceSessions.mockResolvedValue({
      items: [
        {
          session_id: 'session_a',
          device_id: 'device_a',
          turn_count: 2,
          version: 'v1.0.3',
          started_at: '2026-03-31T12:00:00Z',
          ended_at: '2026-03-31T12:03:00Z',
        },
      ],
    })
    apiMocks.fetchMonitoringSessionDetail.mockResolvedValue({
      session: { session_id: 'session_a', device_id: 'device_a', turn_count: 2 },
      rounds: [
        {
          request_id: 'req_001',
          round_no: 1,
          input_text: '设置180度',
          latency_ms: 320,
          is_error: false,
          trace: {
            route: { type: 'intent', confidence: 0.96 },
            intent: { name: 'device.control', confidence: 0.94 },
            slots: { temperature: 180, device_id: 'device_a' },
            reply_text: '已设置到180度',
            device_context_snapshot: { page: 'cook', mode: 'manual' },
          },
        },
      ],
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('searches device sessions and loads trace detail', async () => {
    render(
      <MemoryRouter>
        <MonitoringDeviceLogsPage token="token-admin" />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('设备 ID'), { target: { value: 'device_a' } })
    fireEvent.click(screen.getByRole('button', { name: '查询会话' }))

    await waitFor(() => {
      expect(apiMocks.fetchMonitoringDeviceSessions).toHaveBeenCalledWith('token-admin', { device_id: 'device_a' })
      expect(screen.getByText('session_a')).toBeInTheDocument()
      expect(screen.getByText('v1.0.3')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '查看链路' }))

    await waitFor(() => {
      expect(apiMocks.fetchMonitoringSessionDetail).toHaveBeenCalledWith('token-admin', 'session_a')
      expect(screen.getByText('设置180度')).toBeInTheDocument()
      expect(screen.getByText(/device\.control/)).toBeInTheDocument()
      expect(screen.getByText(/0.96/)).toBeInTheDocument()
      expect(screen.getByText(/已设置到180度/)).toBeInTheDocument()
      expect(screen.getByText(/"page":"cook"/)).toBeInTheDocument()
    })
  })
})

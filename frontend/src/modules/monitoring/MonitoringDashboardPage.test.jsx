import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { MonitoringDashboardPage } from './MonitoringDashboardPage'


const apiMocks = vi.hoisted(() => ({
  fetchMonitoringOverview: vi.fn(),
  fetchMonitoringRequestLogs: vi.fn(),
}))


vi.mock('../../services/api', () => apiMocks)


describe('MonitoringDashboardPage', () => {
  beforeEach(() => {
    apiMocks.fetchMonitoringOverview.mockResolvedValue({
      metrics: {
        request_count: 32,
        qps: 0.0356,
        avg_latency_ms: 420,
        p95_latency_ms: 980,
        accuracy_rate: 0.9375,
        error_rate: 0.0312,
        average_turns: 2.4,
      },
      route_distribution: [{ route_type: 'intent', count: 20, ratio: 0.625 }],
      latest_alerts: [{ id: 'event_001', rule_name: '准确率下降', metric_value: 0.82, status: 'open' }],
    })
    apiMocks.fetchMonitoringRequestLogs.mockResolvedValue({
      items: [
        {
          id: 'log_001',
          request_id: 'req_001',
          device_id: 'device_a',
          session_id: 'session_a',
          route_type: 'intent',
          intent_name: 'device.control',
          latency_ms: 320,
          is_error: false,
        },
      ],
      pagination: { page: 1, page_size: 20, total: 1 },
    })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
    cleanup()
  })

  it('loads overview metrics and logs', async () => {
    render(
      <MemoryRouter>
        <MonitoringDashboardPage token="token-admin" />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '监控仪表盘' })).toBeInTheDocument()
      expect(screen.getByText('总请求量')).toBeInTheDocument()
      expect(screen.getByText('准确率下降')).toBeInTheDocument()
      expect(screen.getByText('req_001')).toBeInTheDocument()
    })
  })

  it('refreshes with current filters', async () => {
    render(
      <MemoryRouter>
        <MonitoringDashboardPage token="token-admin" />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('req_001')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('设备 ID'), { target: { value: 'device_a' } })
    fireEvent.change(screen.getByLabelText('意图'), { target: { value: 'device.control' } })
    fireEvent.change(screen.getByLabelText('最小耗时 (ms)'), { target: { value: '300' } })
    fireEvent.change(screen.getByLabelText('最大耗时 (ms)'), { target: { value: '400' } })
    fireEvent.mouseDown(screen.getAllByLabelText('异常状态')[0])
    fireEvent.click(screen.getAllByText('正常').at(-1))
    fireEvent.click(screen.getByRole('button', { name: '筛选日志' }))

    await waitFor(() => {
      expect(apiMocks.fetchMonitoringRequestLogs).toHaveBeenLastCalledWith('token-admin', {
        device_id: 'device_a',
        window: '15m',
        route: '',
        intent: 'device.control',
        latency_min_ms: 300,
        latency_max_ms: 400,
        is_error: false,
      })
    })

    fireEvent.click(screen.getByRole('button', { name: '手动刷新' }))

    await waitFor(() => {
      expect(apiMocks.fetchMonitoringOverview).toHaveBeenCalledTimes(3)
      expect(apiMocks.fetchMonitoringRequestLogs).toHaveBeenLastCalledWith('token-admin', {
        device_id: 'device_a',
        window: '15m',
        route: '',
        intent: 'device.control',
        latency_min_ms: 300,
        latency_max_ms: 400,
        is_error: false,
      })
    })
  })

  it('polls overview and logs every 30 seconds', async () => {
    vi.useFakeTimers()

    render(
      <MemoryRouter>
        <MonitoringDashboardPage token="token-admin" />
      </MemoryRouter>,
    )

    await Promise.resolve()
    expect(apiMocks.fetchMonitoringOverview).toHaveBeenCalledTimes(1)
    expect(apiMocks.fetchMonitoringRequestLogs).toHaveBeenCalledTimes(1)

    await vi.advanceTimersByTimeAsync(30000)
    await Promise.resolve()
    expect(apiMocks.fetchMonitoringOverview).toHaveBeenCalledTimes(2)
    expect(apiMocks.fetchMonitoringRequestLogs).toHaveBeenCalledTimes(2)
  })
})

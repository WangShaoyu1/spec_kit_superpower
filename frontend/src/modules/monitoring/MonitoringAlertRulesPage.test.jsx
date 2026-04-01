import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { MonitoringAlertRulesPage } from './MonitoringAlertRulesPage'


const apiMocks = vi.hoisted(() => ({
  createMonitoringAlertRule: vi.fn(),
  fetchMonitoringAlertRules: vi.fn(),
  updateMonitoringAlertRule: vi.fn(),
}))


vi.mock('../../services/api', () => apiMocks)


describe('MonitoringAlertRulesPage', () => {
  beforeEach(() => {
    apiMocks.fetchMonitoringAlertRules.mockResolvedValue({
      rules: [
        {
          id: 'rule_001',
          name: '准确率下降',
          metric_key: 'accuracy_drop',
          comparator: 'lt',
          threshold: 0.9,
          window_minutes: 5,
          severity: 'warn',
          enabled: true,
        },
      ],
      latest_events: [
        { id: 'event_001', rule_name: '准确率下降', metric_value: 0.82, status: 'open' },
      ],
    })
    apiMocks.createMonitoringAlertRule.mockResolvedValue({
      rule: { id: 'rule_002', name: '错误率突增' },
    })
    apiMocks.updateMonitoringAlertRule.mockResolvedValue({
      rule: { id: 'rule_001', enabled: false },
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('loads alert rules and recent events', async () => {
    render(
      <MemoryRouter>
        <MonitoringAlertRulesPage token="token-admin" />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '告警规则' })).toBeInTheDocument()
      expect(screen.getAllByText('准确率下降').length).toBeGreaterThan(0)
      expect(screen.getByText(/metric=0.82/)).toBeInTheDocument()
    })
  })

  it('creates and toggles alert rules with real reload', async () => {
    render(
      <MemoryRouter>
        <MonitoringAlertRulesPage token="token-admin" />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getAllByText('准确率下降').length).toBeGreaterThan(0)
    })

    fireEvent.click(screen.getByRole('button', { name: '新建规则' }))
    fireEvent.change(screen.getByLabelText('规则名称'), { target: { value: '错误率突增' } })
    fireEvent.mouseDown(screen.getAllByLabelText('指标')[0])
    fireEvent.click(screen.getByText('错误率突增'))
    fireEvent.change(screen.getByLabelText('阈值'), { target: { value: '0.2' } })
    fireEvent.change(screen.getByLabelText('持续窗口'), { target: { value: '10' } })
    fireEvent.click(screen.getByRole('button', { name: /创建规则/ }))

    await waitFor(() => {
      expect(apiMocks.createMonitoringAlertRule).toHaveBeenCalledWith(
        'token-admin',
        expect.objectContaining({
          name: '错误率突增',
          metric_key: 'error_rate_spike',
          threshold: 0.2,
          window_minutes: 10,
        }),
      )
      expect(apiMocks.fetchMonitoringAlertRules).toHaveBeenCalledTimes(2)
    })

    fireEvent.click(screen.getByRole('switch'))

    await waitFor(() => {
      expect(apiMocks.updateMonitoringAlertRule).toHaveBeenCalledWith(
        'token-admin',
        'rule_001',
        expect.objectContaining({ enabled: false }),
      )
      expect(apiMocks.fetchMonitoringAlertRules).toHaveBeenCalledTimes(3)
    })
  })
})

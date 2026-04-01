import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AppShell } from './AppShell'
import { UserMgmtPage } from '../modules/user-mgmt/UserMgmtPage'

const apiMocks = vi.hoisted(() => ({
  changeUserStatus: vi.fn(),
  createUser: vi.fn(),
  fetchPermissionMatrix: vi.fn(),
  fetchUsers: vi.fn(),
  resetUserPassword: vi.fn(),
  updateUserRole: vi.fn(),
}))

vi.mock('../services/api', () => apiMocks)

function renderShell(initialPath) {
  return render(
    <ConfigProvider locale={zhCN}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route path="user-mgmt" element={<UserMgmtPage token="token-admin" />} />
            <Route path="intent-library/*" element={<div>指令库占位页</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </ConfigProvider>,
  )
}

describe('AppShell', () => {
  beforeEach(() => {
    apiMocks.fetchUsers.mockResolvedValue({
      items: [
        {
          id: 'user_001',
          username: 'admin',
          name: '管理员',
          role: 'admin',
          status: 'active',
          created_at: '2026-03-31',
          last_login_at: null,
        },
      ],
      summary: { total: 1, admin_count: 1, pm_count: 0, tester_count: 0 },
    })
    apiMocks.fetchPermissionMatrix.mockResolvedValue({
      items: [{ capability_key: 'user_manage', description: '用户管理', admin: true, pm: true, tester: false }],
    })
    apiMocks.changeUserStatus.mockResolvedValue({})
    apiMocks.createUser.mockResolvedValue({})
    apiMocks.resetUserPassword.mockResolvedValue({})
    apiMocks.updateUserRole.mockResolvedValue({})
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders the business shell without rollout copy in the main menu', () => {
    renderShell('/user-mgmt')

    expect(screen.getByText('SmartChef')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '用户管理' })).toBeInTheDocument()
    expect(screen.getAllByText('指令库管理').length).toBeGreaterThan(0)
    expect(screen.queryByRole('link', { name: '总览驾驶舱' })).not.toBeInTheDocument()
    expect(screen.queryByText('Spec Harness Console')).not.toBeInTheDocument()
    expect(screen.queryByText(/正式前端壳|harness 顺序/i)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '平台概览' })).toBeInTheDocument()
  })

  it('renders the user management entry route', () => {
    renderShell('/user-mgmt')

    expect(screen.getAllByRole('heading', { name: '账号管理' }).length).toBeGreaterThan(0)
    expect(screen.getAllByText('新建账号').length).toBeGreaterThan(0)
  })

  it('opens the overview drawer from the top action area', () => {
    renderShell('/user-mgmt')

    fireEvent.click(screen.getAllByRole('button', { name: '平台概览' })[0])

    expect(screen.getAllByText('平台概览').length).toBeGreaterThan(1)
    expect(screen.getByText('已接入模块')).toBeInTheDocument()
  })

  it('keeps the intent library menu selected on nested routes', () => {
    const { container } = renderShell('/intent-library/lib_001/test')

    const selectedIntentEntry = container.querySelector('.ant-menu-item-selected a[href="/intent-library"]')

    expect(selectedIntentEntry).not.toBeNull()
    expect(screen.getByText('指令库占位页')).toBeInTheDocument()
  })
})

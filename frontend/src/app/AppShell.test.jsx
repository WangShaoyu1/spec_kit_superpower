import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { render, screen } from '@testing-library/react'
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

  it('renders the formal console menu', () => {
    renderShell('/')

    expect(screen.getByText('SmartChef')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '用户管理' })).toBeInTheDocument()
    expect(screen.getAllByText('指令库管理').length).toBeGreaterThan(0)
    expect(screen.getByText('Spec Harness Console')).toBeInTheDocument()
  })

  it('renders the user management entry route', () => {
    renderShell('/user-mgmt')

    expect(screen.getByRole('heading', { name: '账号管理' })).toBeInTheDocument()
    expect(screen.getByText('新建账号')).toBeInTheDocument()
  })
})

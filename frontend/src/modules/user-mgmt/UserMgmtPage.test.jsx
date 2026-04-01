import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { UserMgmtPage } from './UserMgmtPage'


const apiMocks = vi.hoisted(() => ({
  changeUserStatus: vi.fn(),
  createUser: vi.fn(),
  fetchPermissionMatrix: vi.fn(),
  fetchUsers: vi.fn(),
  resetUserPassword: vi.fn(),
  updateUserRole: vi.fn(),
}))


vi.mock('../../services/api', () => apiMocks)


describe('UserMgmtPage', () => {
  let usersState
  let matrixState

  beforeEach(() => {
    usersState = [
      {
        id: 'user_001',
        username: 'admin',
        name: '管理员',
        role: 'admin',
        status: 'active',
        created_at: '2026-03-31',
        last_login_at: null,
      },
      {
        id: 'user_002',
        username: 'wang_pm',
        name: '小王',
        role: 'pm',
        status: 'active',
        created_at: '2026-03-31',
        last_login_at: null,
      },
    ]
    matrixState = [
      {
        capability_key: 'user_manage',
        description: '用户管理',
        admin: true,
        pm: true,
        tester: false,
      },
    ]

    apiMocks.fetchUsers.mockImplementation(() =>
      Promise.resolve({
        items: usersState,
        summary: {
          total: usersState.length,
          admin_count: usersState.filter((item) => item.role === 'admin').length,
          pm_count: usersState.filter((item) => item.role === 'pm').length,
          tester_count: usersState.filter((item) => item.role === 'tester').length,
        },
      }),
    )
    apiMocks.fetchPermissionMatrix.mockImplementation(() => Promise.resolve({ items: matrixState }))
    apiMocks.createUser.mockImplementation(async (_token, payload) => {
      usersState = [
        ...usersState,
        {
          id: 'user_003',
          username: payload.username,
          name: payload.name,
          role: payload.role,
          status: 'active',
          created_at: '2026-03-31',
          last_login_at: null,
        },
      ]
      return { user: usersState.at(-1) }
    })
    apiMocks.updateUserRole.mockImplementation(async (_token, userId, role) => {
      usersState = usersState.map((item) => (item.id === userId ? { ...item, role } : item))
      return { user: usersState.find((item) => item.id === userId) }
    })
    apiMocks.changeUserStatus.mockResolvedValue({})
    apiMocks.resetUserPassword.mockResolvedValue({})
  })

  afterEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  it('loads user directory and renders pm matrix permission as 有', async () => {
    render(<UserMgmtPage token="token-admin" />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '账号管理' })).toBeInTheDocument()
      expect(screen.getByText('wang_pm')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('tab', { name: '权限矩阵' }))

    await waitFor(() => {
      expect(screen.getByText('user_manage')).toBeInTheDocument()
      expect(screen.getAllByText('有').length).toBeGreaterThan(1)
    })
  })

  it('reloads real data after create and role update', async () => {
    render(<UserMgmtPage token="token-admin" />)

    await waitFor(() => {
      expect(screen.getByText('wang_pm')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '新建账号' }))
    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'li_tester' } })
    fireEvent.change(screen.getByLabelText('姓名'), { target: { value: '小李' } })
    fireEvent.change(screen.getByLabelText('初始密码'), { target: { value: 'Abc12345' } })
    fireEvent.click(screen.getByRole('button', { name: /创\s*建/ }))

    await waitFor(() => {
      expect(apiMocks.createUser).toHaveBeenCalledWith(
        'token-admin',
        expect.objectContaining({ username: 'li_tester', role: 'pm' }),
      )
      expect(apiMocks.fetchUsers).toHaveBeenCalledTimes(2)
      expect(screen.getByText('li_tester')).toBeInTheDocument()
    })

    fireEvent.click(screen.getAllByRole('button', { name: '编辑角色' })[1])
    fireEvent.mouseDown(screen.getAllByLabelText('新角色')[0])
    fireEvent.click(screen.getAllByText('系统管理员').at(-1))
    fireEvent.click(screen.getByRole('button', { name: /保\s*存/ }))

    await waitFor(() => {
      expect(apiMocks.updateUserRole).toHaveBeenCalledWith('token-admin', 'user_002', expect.any(String))
      expect(apiMocks.fetchUsers).toHaveBeenCalledTimes(3)
      expect(apiMocks.fetchPermissionMatrix).toHaveBeenCalledTimes(3)
    })
  })
})

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from '../App'


function jsonResponse(payload) {
  return Promise.resolve({
    ok: true,
    json: async () => payload,
  })
}


describe('App auth flow', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    cleanup()
  })

  it('shows the login screen when no session exists', () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => Promise.reject(new Error('should not fetch')))

    render(<App />)

    expect(screen.getByText('管理员登录')).toBeInTheDocument()
    expect(screen.getByLabelText('用户名')).toBeInTheDocument()
  })

  it('logs in and loads the user management directory', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    fetchSpy
      .mockImplementationOnce(() =>
        jsonResponse({
          code: '000000',
          message: 'success',
          data: {
            access_token: 'token-admin',
            user: { id: 'user_001', username: 'admin', name: '管理员', role: 'admin', status: 'active' },
            capabilities: ['user_manage'],
          },
        }),
      )
      .mockImplementationOnce(() =>
        jsonResponse({
          code: '000000',
          message: 'success',
          data: {
            items: [
              {
                id: 'user_001',
                username: 'admin',
                name: '管理员',
                role: 'admin',
                status: 'active',
                created_at: '2026-03-30',
                last_login_at: null,
              },
            ],
            summary: { total: 1, admin_count: 1, pm_count: 0, tester_count: 0 },
          },
        }),
      )
      .mockImplementationOnce(() =>
        jsonResponse({
          code: '000000',
          message: 'success',
          data: {
            items: [
              {
                capability_key: 'user_manage',
                description: '用户管理',
                admin: true,
                pm: false,
                tester: false,
              },
            ],
          },
        }),
      )

    render(<App />)

    fireEvent.change(screen.getAllByLabelText('用户名')[0], { target: { value: 'admin' } })
    fireEvent.change(screen.getAllByLabelText('密码')[0], { target: { value: 'Abc12345' } })
    fireEvent.click(screen.getByRole('button', { name: '登录系统' }))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '账号管理' })).toBeInTheDocument()
      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/auth/login'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/admin/users'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer token-admin' }),
      }),
    )
  })
})

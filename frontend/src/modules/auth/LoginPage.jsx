import { Alert, Button, Card, Input, Typography } from 'antd'
import { useState } from 'react'

const { Paragraph, Title } = Typography


export function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('Abc12345')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')

    try {
      await onLogin({ username, password })
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-shell">
      <Card className="auth-card" variant="borderless">
        <div className="hero-eyebrow">Formal Entry</div>
        <Title level={2} style={{ color: '#fff', marginTop: 12 }}>
          管理员登录
        </Title>
        <Paragraph className="hero-paragraph" style={{ maxWidth: 'none' }}>
          先进入正式后台会话，再按 capability 打开用户管理与后续模块菜单。
        </Paragraph>
        {error ? (
          <Alert
            type="error"
            showIcon
            message="登录失败"
            description={error}
            style={{ marginBottom: 16 }}
          />
        ) : null}
        <form onSubmit={handleSubmit} className="auth-form">
          <label className="auth-label" htmlFor="login-username">
            用户名
          </label>
          <Input
            id="login-username"
            aria-label="用户名"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            size="large"
          />

          <label className="auth-label" htmlFor="login-password">
            密码
          </label>
          <Input.Password
            id="login-password"
            aria-label="密码"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            size="large"
          />

          <Button type="primary" htmlType="submit" size="large" loading={submitting} block>
            登录系统
          </Button>
        </form>
      </Card>
    </div>
  )
}

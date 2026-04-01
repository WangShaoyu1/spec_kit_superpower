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
      <aside className="auth-ambience" aria-label="产品介绍">
        <div className="auth-ambience-inner">
          <div className="auth-ambience-kicker">SmartChef · Console</div>
          <h1>面向厨房智能体的运营中枢</h1>
          <p>
            在同一套控制台里串联用户与权限、指令与知识、对话方案与批量测试，并承接监控与告警；适合验收、回归与日常运维的固定节奏。
          </p>
        </div>
      </aside>
      <div className="auth-panel">
        <Card className="auth-card" variant="borderless">
          <div className="hero-eyebrow">身份校验</div>
          <Title
            level={2}
            style={{
              fontFamily: 'var(--font-display)',
              marginTop: 10,
              marginBottom: 8,
              color: 'var(--ink)',
              fontWeight: 600,
            }}
          >
            管理员登录
          </Title>
          <Paragraph className="hero-paragraph" style={{ maxWidth: 'none' }}>
            使用管理员账号进入后台；若会话过期，将自动回到本页。
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
              进入控制台
            </Button>
          </form>
        </Card>
      </div>
    </div>
  )
}

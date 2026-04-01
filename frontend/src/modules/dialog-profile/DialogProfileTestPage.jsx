import { Alert, Button, Card, Empty, Form, Input, Space, Tag, message } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import {
  createDialogProfileSession,
  fetchDialogProfileDetail,
  fetchDialogProfileSession,
  sendDialogProfileMessage,
} from '../../services/api'


function safeParseContext(text) {
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}


export function DialogProfileTestPage({ token }) {
  const navigate = useNavigate()
  const { profileId } = useParams()
  const [profile, setProfile] = useState(null)
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [currentDetail, setCurrentDetail] = useState(null)
  const [lastTrace, setLastTrace] = useState(null)
  const [loading, setLoading] = useState(true)
  const [messageForm] = Form.useForm()
  const [contextText, setContextText] = useState('{\n  "device_id": "device_a",\n  "page": "recipe",\n  "cooking": true\n}')

  const currentSession = useMemo(
    () => sessions.find((item) => item.id === currentSessionId) ?? null,
    [sessions, currentSessionId],
  )

  async function loadSession(sessionId) {
    const detail = await fetchDialogProfileSession(token, sessionId)
    setCurrentSessionId(sessionId)
    setCurrentDetail(detail)
  }

  async function createSession(sessionName) {
    const deviceContext = safeParseContext(contextText)
    if (!deviceContext) {
      message.error('设备上下文必须是合法 JSON')
      return
    }
    const created = await createDialogProfileSession(token, profileId, {
      name: sessionName,
      device_context: deviceContext,
    })
    setSessions((prev) => [created.session, ...prev])
    await loadSession(created.session.id)
  }

  useEffect(() => {
    async function bootstrap() {
      setLoading(true)
      try {
        const detail = await fetchDialogProfileDetail(token, profileId)
        setProfile(detail.profile)
        await createSession('默认会话')
      } finally {
        setLoading(false)
      }
    }
    void bootstrap()
  }, [token, profileId])

  async function handleSend(values) {
    const deviceContext = safeParseContext(contextText)
    if (!deviceContext || !currentSessionId) {
      message.error('请先确认设备上下文与测试会话')
      return
    }
    const result = await sendDialogProfileMessage(token, currentSessionId, {
      text: values.text,
      device_context: deviceContext,
    })
    setLastTrace(result.debug_trace)
    messageForm.resetFields()
    await loadSession(currentSessionId)
  }

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless" loading={loading}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
          <div>
            <div className="hero-eyebrow">Manual Test</div>
            <h2 className="page-title">{profile?.name ?? '手动测试'}</h2>
            <p className="page-lede">
              会话隔离、设备上下文模拟和调试 trace 全部以后端真实回读为准。
            </p>
          </div>
          <Space>
            <Button onClick={() => navigate(`/dialog-profiles/${profileId}`)}>返回详情</Button>
            <Button onClick={() => void createSession(`会话 ${sessions.length + 1}`)}>新建会话</Button>
          </Space>
        </div>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr 320px', gap: 18 }}>
        <Card className="module-card" variant="borderless" loading={loading}>
          <div className="chat-panel-label">测试会话</div>
          <div className="page-stack">
            {sessions.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => void loadSession(item.id)}
                className={`chat-session-item${item.id === currentSessionId ? ' chat-session-item--active' : ''}`}
                style={{ width: '100%' }}
              >
                <div className="chat-session-title">{item.name}</div>
                <div className="chat-session-meta">消息数 {item.message_count}</div>
              </button>
            ))}
          </div>
        </Card>

        <Card className="module-card" variant="borderless" loading={loading}>
          <div className="page-stack">
            {currentDetail?.messages?.length ? (
              <div className="page-stack" style={{ maxHeight: 420, overflow: 'auto' }}>
                {currentDetail.messages.map((item) => (
                  <div
                    key={item.id}
                    className={`chat-msg${item.role === 'assistant' ? ' chat-msg--assistant' : ' chat-msg--user'}`}
                  >
                    <div className="chat-msg-role">{item.role === 'assistant' ? '助手' : '用户'}</div>
                    <div className="chat-msg-text">{item.text}</div>
                    {item.response_time_ms !== null && item.response_time_ms !== undefined ? (
                      <div className="chat-msg-foot">
                        响应耗时 {item.response_time_ms} ms
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <Empty description="当前会话暂无消息" />
            )}

            <Form form={messageForm} layout="vertical" onFinish={handleSend}>
              <Form.Item name="text" label="测试消息" rules={[{ required: true }]}>
                <Input aria-label="测试消息" />
              </Form.Item>
              <Button type="primary" onClick={() => messageForm.submit()}>
                发送消息
              </Button>
            </Form>
          </div>
        </Card>

        <Card className="module-card" variant="borderless" loading={loading}>
          <div className="page-stack">
            <div>
              <div className="chat-panel-label">设备上下文</div>
              <Input.TextArea
                aria-label="设备上下文"
                rows={10}
                value={contextText}
                onChange={(event) => setContextText(event.target.value)}
              />
            </div>

            {currentSession ? (
              <Tag color="blue">当前会话: {currentSession.name}</Tag>
            ) : null}

            {lastTrace ? (
              <Alert
                type="info"
                showIcon
                message={`route: ${lastTrace.route?.type ?? '-'} (${lastTrace.route?.confidence ?? '-'})`}
                description={(
                  <div className="page-stack">
                    <div>intent: {lastTrace.intent?.name ?? '-'} ({lastTrace.intent?.confidence ?? '-'})</div>
                    <div>model: {lastTrace.model}</div>
                    <div>response: {lastTrace.response_text ?? '-'}</div>
                    <div>response_time_ms: {lastTrace.response_time_ms ?? '-'}</div>
                    <div>slots: {JSON.stringify(lastTrace.slots)}</div>
                    <div>device_context_snapshot: {JSON.stringify(lastTrace.device_context_snapshot ?? {})}</div>
                  </div>
                )}
              />
            ) : (
              <Alert
                type="warning"
                showIcon
                message="调试面板"
                description="发送消息后这里会显示 route / intent 置信度、slots、response、context snapshot。"
              />
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}

import { Alert, Button, Card, Form, Input, Space, Table, Tag, message } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { fetchMonitoringDeviceSessions, fetchMonitoringSessionDetail } from '../../services/api'


export function MonitoringDeviceLogsPage({ token }) {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState([])
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [currentDeviceId, setCurrentDeviceId] = useState('')
  const [form] = Form.useForm()

  useEffect(() => {
    if (!currentDeviceId) {
      return
    }
    void loadSessions(currentDeviceId)
  }, [token, currentDeviceId])

  async function loadSessions(deviceId) {
    setLoading(true)
    try {
      const payload = await fetchMonitoringDeviceSessions(token, { device_id: deviceId })
      setSessions(payload.items ?? [])
    } finally {
      setLoading(false)
    }
  }

  async function loadTrace(sessionId) {
    setLoading(true)
    try {
      const payload = await fetchMonitoringSessionDetail(token, sessionId)
      setDetail(payload)
    } finally {
      setLoading(false)
    }
  }

  async function handleSearch(values) {
    const deviceId = values.device_id?.trim() ?? ''
    setCurrentDeviceId(deviceId)
    setDetail(null)
    if (deviceId) {
      await loadSessions(deviceId)
      message.success(`已回读设备 ${deviceId} 的会话列表`)
    }
  }

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless">
        <div className="page-header-row">
          <div>
            <div className="hero-eyebrow">Trace Drilldown</div>
            <h2 className="page-title">设备日志与会话链路</h2>
            <p className="page-lede">
              按设备 ID 回读历史会话，并下钻到逐轮请求链路详情。
            </p>
          </div>
          <Button onClick={() => navigate('/monitoring')}>返回仪表盘</Button>
        </div>
      </Card>

      <Card className="module-card" variant="borderless">
        <Form form={form} layout="inline" onFinish={handleSearch}>
          <Form.Item name="device_id" label="设备 ID" rules={[{ required: true }]}>
            <Input aria-label="设备 ID" placeholder="例如 device_a" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">查询会话</Button>
          </Form.Item>
        </Form>
      </Card>

      <Card className="module-card" variant="borderless" loading={loading} title="会话列表">
        <Table
          rowKey="session_id"
          pagination={false}
          dataSource={sessions}
          columns={[
            { title: '会话 ID', dataIndex: 'session_id' },
            { title: '轮次', dataIndex: 'turn_count' },
            { title: '版本', dataIndex: 'version' },
            { title: '开始时间', dataIndex: 'started_at' },
            { title: '结束时间', dataIndex: 'ended_at' },
            {
              title: '操作',
              render: (_, row) => <Button size="small" onClick={() => loadTrace(row.session_id)}>查看链路</Button>,
            },
          ]}
        />
      </Card>

      <Card className="module-card" variant="borderless" loading={loading} title="链路详情">
        {detail?.session ? (
          <div className="page-stack">
            <Alert
              type="info"
              showIcon
              message={`设备 ${detail.session.device_id} / 会话 ${detail.session.session_id}`}
              description={`共 ${detail.session.turn_count} 轮`}
            />
            <Table
              rowKey="request_id"
              pagination={false}
              dataSource={detail.rounds}
              columns={[
                { title: '轮次', dataIndex: 'round_no' },
                { title: '输入', dataIndex: 'input_text' },
                { title: '耗时', dataIndex: 'latency_ms' },
                {
                  title: '路由',
                  render: (_, row) => `${row.trace?.route?.type ?? '-'} (${row.trace?.route?.confidence ?? '-'})`,
                },
                {
                  title: '意图',
                  render: (_, row) => `${row.trace?.intent?.name ?? '-'} (${row.trace?.intent?.confidence ?? '-'})`,
                },
                {
                  title: '槽位',
                  render: (_, row) => JSON.stringify(row.trace?.slots ?? {}),
                },
                {
                  title: '回复文本',
                  render: (_, row) => row.trace?.reply_text ?? '-',
                },
                {
                  title: '上下文快照',
                  render: (_, row) => JSON.stringify(row.trace?.device_context_snapshot ?? {}),
                },
                {
                  title: '状态',
                  render: (_, row) => (row.is_error ? <Tag color="red">异常</Tag> : <Tag color="green">正常</Tag>),
                },
              ]}
            />
          </div>
        ) : (
          <Alert type="warning" showIcon message="请先查询设备并选择某个会话" />
        )}
      </Card>
    </div>
  )
}

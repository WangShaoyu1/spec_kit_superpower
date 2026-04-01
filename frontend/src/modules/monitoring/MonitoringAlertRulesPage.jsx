import { Alert, Button, Card, Form, Input, Modal, Select, Space, Switch, Table, Tag, message } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { createMonitoringAlertRule, fetchMonitoringAlertRules, updateMonitoringAlertRule } from '../../services/api'


const METRIC_OPTIONS = [
  { value: 'accuracy_drop', label: '准确率下降' },
  { value: 'latency_p99_ms', label: 'P99 延迟超标' },
  { value: 'error_rate_spike', label: '错误率突增' },
]

const COMPARATOR_OPTIONS = [
  { value: 'gt', label: '>' },
  { value: 'gte', label: '>=' },
  { value: 'lt', label: '<' },
  { value: 'lte', label: '<=' },
]

const SEVERITY_COLORS = {
  info: 'blue',
  warn: 'orange',
  critical: 'red',
}


export function MonitoringAlertRulesPage({ token }) {
  const navigate = useNavigate()
  const [payload, setPayload] = useState({ rules: [], latest_events: [] })
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  async function loadRules() {
    setLoading(true)
    try {
      const nextPayload = await fetchMonitoringAlertRules(token)
      setPayload(nextPayload)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadRules()
  }, [token])

  async function handleCreate(values) {
    await createMonitoringAlertRule(token, {
      ...values,
      threshold: Number(values.threshold),
      window_minutes: Number(values.window_minutes),
    })
    setCreateOpen(false)
    form.resetFields()
    await loadRules()
    message.success('告警规则已创建')
  }

  async function handleToggle(rule) {
    await updateMonitoringAlertRule(token, rule.id, {
      enabled: !rule.enabled,
      threshold: rule.threshold,
      window_minutes: rule.window_minutes,
      severity: rule.severity,
    })
    await loadRules()
    message.success(!rule.enabled ? '规则已启用' : '规则已停用')
  }

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless">
        <div className="page-header-row">
          <div>
            <div className="hero-eyebrow">Alert Governance</div>
            <h2 className="page-title">告警规则</h2>
            <p className="page-lede">
              管理准确率、延迟和错误率相关规则，并回读最近触发事件。
            </p>
          </div>
          <Space>
            <Button onClick={() => navigate('/monitoring')}>返回仪表盘</Button>
            <Button type="primary" onClick={() => setCreateOpen(true)}>新建规则</Button>
          </Space>
        </div>
      </Card>

      <Card className="module-card" variant="borderless" loading={loading} title="规则列表">
        <Table
          rowKey="id"
          pagination={false}
          dataSource={payload.rules}
          columns={[
            { title: '名称', dataIndex: 'name' },
            { title: '指标', dataIndex: 'metric_key' },
            { title: '比较器', dataIndex: 'comparator' },
            { title: '阈值', dataIndex: 'threshold' },
            { title: '窗口（分钟）', dataIndex: 'window_minutes' },
            {
              title: '等级',
              render: (_, row) => <Tag color={SEVERITY_COLORS[row.severity] ?? 'default'}>{row.severity}</Tag>,
            },
            {
              title: '启用',
              render: (_, row) => <Switch checked={row.enabled} onChange={() => handleToggle(row)} />,
            },
          ]}
        />
      </Card>

      <Card className="module-card" variant="borderless" loading={loading} title="最近触发">
        {payload.latest_events.length > 0 ? (
          <div className="page-stack">
            {payload.latest_events.map((item) => (
              <Alert
                key={item.id}
                type={item.status === 'open' ? 'warning' : 'info'}
                showIcon
                message={item.rule_name}
                description={`metric=${item.metric_value} / status=${item.status}`}
              />
            ))}
          </div>
        ) : (
          <Alert type="success" showIcon message="最近没有触发事件" />
        )}
      </Card>

      <Modal
        title="新建告警规则"
        open={createOpen}
        destroyOnHidden
        onCancel={() => {
          setCreateOpen(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        okText="创建规则"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{ comparator: 'gt', severity: 'warn', window_minutes: 5 }}
        >
          <Form.Item name="name" label="规则名称" rules={[{ required: true }]}>
            <Input aria-label="规则名称" />
          </Form.Item>
          <Form.Item name="metric_key" label="指标" rules={[{ required: true }]}>
            <Select aria-label="指标" options={METRIC_OPTIONS} />
          </Form.Item>
          <Form.Item name="comparator" label="比较器" rules={[{ required: true }]}>
            <Select aria-label="比较器" options={COMPARATOR_OPTIONS} />
          </Form.Item>
          <Form.Item name="threshold" label="阈值" rules={[{ required: true }]}>
            <Input aria-label="阈值" />
          </Form.Item>
          <Form.Item name="window_minutes" label="持续窗口（分钟）" rules={[{ required: true }]}>
            <Input aria-label="持续窗口" />
          </Form.Item>
          <Form.Item name="severity" label="等级" rules={[{ required: true }]}>
            <Select aria-label="等级" options={[
              { value: 'info', label: 'info' },
              { value: 'warn', label: 'warn' },
              { value: 'critical', label: 'critical' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

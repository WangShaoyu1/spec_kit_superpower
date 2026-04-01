import { Alert, Button, Card, Col, Form, Input, Row, Select, Space, Statistic, Table, Tag, message } from 'antd'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { fetchMonitoringOverview, fetchMonitoringRequestLogs } from '../../services/api'


const ROUTE_OPTIONS = [
  { value: 'intent', label: '指令' },
  { value: 'knowledge', label: '知识' },
  { value: 'chitchat', label: '闲聊' },
]

const WINDOW_OPTIONS = [
  { value: '5m', label: '最近 5 分钟' },
  { value: '15m', label: '最近 15 分钟' },
  { value: '60m', label: '最近 60 分钟' },
]

const ERROR_OPTIONS = [
  { value: 'all', label: '全部' },
  { value: 'false', label: '正常' },
  { value: 'true', label: '异常' },
]

const ALERT_TONE = {
  info: 'blue',
  warn: 'orange',
  critical: 'red',
}


export function MonitoringDashboardPage({ token }) {
  const navigate = useNavigate()
  const [overview, setOverview] = useState({
    metrics: {
      request_count: 0,
      qps: 0,
      avg_latency_ms: 0,
      p95_latency_ms: 0,
      accuracy_rate: 0,
      error_rate: 0,
      average_turns: 0,
    },
    route_distribution: [],
    latest_alerts: [],
  })
  const [logsPayload, setLogsPayload] = useState({ items: [], pagination: { page: 1, page_size: 20, total: 0 } })
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    window: '15m',
    device_id: '',
    route: '',
    intent: '',
    latency_min_ms: '',
    latency_max_ms: '',
    is_error: 'all',
  })
  const [form] = Form.useForm()
  const filtersRef = useRef(filters)

  useEffect(() => {
    filtersRef.current = filters
  }, [filters])

  async function loadDashboard(nextFilters = filters, options = {}) {
    const { syncFilters = true } = options
    setLoading(true)
    try {
      const [overviewPayload, requestLogsPayload] = await Promise.all([
        fetchMonitoringOverview(token, { window: nextFilters.window }),
        fetchMonitoringRequestLogs(token, nextFilters),
      ])
      setOverview(overviewPayload)
      setLogsPayload(requestLogsPayload)
      if (syncFilters) {
        setFilters(nextFilters)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDashboard()
  }, [token])

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void loadDashboard(filtersRef.current, { syncFilters: false })
    }, 30000)
    return () => window.clearInterval(intervalId)
  }, [token])

  async function handleSearch(values) {
    const nextFilters = {
      window: values.window ?? '15m',
      device_id: values.device_id?.trim() ?? '',
      route: values.route ?? '',
      intent: values.intent?.trim() ?? '',
      latency_min_ms: values.latency_min_ms ? Number(values.latency_min_ms) : '',
      latency_max_ms: values.latency_max_ms ? Number(values.latency_max_ms) : '',
      is_error: values.is_error === 'all' || values.is_error === undefined ? '' : values.is_error === 'true',
    }
    await loadDashboard(nextFilters)
    message.success('监控数据已刷新')
  }

  async function handleRefresh() {
    await loadDashboard(filters)
    message.success('已回读最新监控指标')
  }

  const metrics = overview.metrics

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless">
        <div className="page-header-row">
          <div>
            <div className="hero-eyebrow">Runtime Observatory</div>
            <h2 className="page-title">监控仪表盘</h2>
            <p className="page-lede">
              统一回读运行态指标、请求日志与最近告警，避免发布后“看不见、查不清、反应慢”。
            </p>
          </div>
          <Space>
            <Tag color="gold">30s 轮询口径</Tag>
            <Button onClick={() => navigate('/monitoring/device-logs')}>设备日志</Button>
            <Button onClick={() => navigate('/monitoring/alert-rules')}>告警规则</Button>
            <Button type="primary" onClick={handleRefresh}>手动刷新</Button>
          </Space>
        </div>
      </Card>

      <Row gutter={18}>
        <Col span={6}>
          <Card className="module-card" variant="borderless"><Statistic title="总请求量" value={metrics.request_count ?? 0} /></Card>
        </Col>
        <Col span={6}>
          <Card className="module-card" variant="borderless"><Statistic title="QPS" value={metrics.qps ?? 0} precision={4} /></Card>
        </Col>
        <Col span={6}>
          <Card className="module-card" variant="borderless"><Statistic title="平均延迟 (ms)" value={metrics.avg_latency_ms ?? 0} /></Card>
        </Col>
        <Col span={6}>
          <Card className="module-card" variant="borderless"><Statistic title="P95 (ms)" value={metrics.p95_latency_ms ?? 0} /></Card>
        </Col>
      </Row>

      <Row gutter={18}>
        <Col span={8}>
          <Card className="module-card" variant="borderless"><Statistic title="线上准确率" value={metrics.accuracy_rate ?? 0} precision={4} /></Card>
        </Col>
        <Col span={8}>
          <Card className="module-card" variant="borderless"><Statistic title="错误率" value={metrics.error_rate ?? 0} precision={4} /></Card>
        </Col>
        <Col span={8}>
          <Card className="module-card" variant="borderless"><Statistic title="平均轮次" value={metrics.average_turns ?? 0} precision={2} /></Card>
        </Col>
      </Row>

      <Row gutter={18}>
        <Col span={10}>
          <Card className="module-card" variant="borderless" loading={loading} title="路由分布">
            <Space wrap>
              {overview.route_distribution.length > 0 ? overview.route_distribution.map((item) => (
                <Tag key={item.route_type} color="blue">
                  {item.route_type} / {item.count} / {(item.ratio * 100).toFixed(1)}%
                </Tag>
              )) : <Tag>暂无分布数据</Tag>}
            </Space>
          </Card>
        </Col>
        <Col span={14}>
          <Card className="module-card" variant="borderless" loading={loading} title="最近告警">
            {overview.latest_alerts.length > 0 ? (
              <div className="page-stack">
                {overview.latest_alerts.map((item) => (
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
              <Alert type="success" showIcon message="当前没有未恢复告警" />
            )}
          </Card>
        </Col>
      </Row>

      <Card className="module-card" variant="borderless" loading={loading}>
        <div className="page-stack">
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center' }}>
            <strong className="page-section-strong">请求日志</strong>
            <Tag color="purple">真实筛选后回读</Tag>
          </div>

          <Form
            form={form}
            layout="vertical"
            className="monitoring-logs-filter-form"
            onFinish={handleSearch}
            initialValues={filters}
          >
            <Row gutter={[20, 20]}>
              <Col xs={24} sm={12} md={8} xl={6}>
                <Form.Item name="window" label="时间窗口">
                  <Select aria-label="时间窗口" options={WINDOW_OPTIONS} />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8} xl={6}>
                <Form.Item name="device_id" label="设备 ID">
                  <Input aria-label="设备 ID" placeholder="例如 device_a" allowClear />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8} xl={6}>
                <Form.Item name="route" label="路由类型">
                  <Select
                    aria-label="路由类型"
                    allowClear
                    options={ROUTE_OPTIONS}
                    placeholder="全部路由"
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8} xl={6}>
                <Form.Item name="intent" label="意图">
                  <Input aria-label="意图" placeholder="例如 device.control" allowClear />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8} xl={6}>
                <Form.Item name="latency_min_ms" label="最小耗时 (ms)">
                  <Input aria-label="最小耗时 (ms)" placeholder="最小值" inputMode="numeric" allowClear />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8} xl={6}>
                <Form.Item name="latency_max_ms" label="最大耗时 (ms)">
                  <Input aria-label="最大耗时 (ms)" placeholder="最大值" inputMode="numeric" allowClear />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8} xl={6}>
                <Form.Item name="is_error" label="异常状态">
                  <Select aria-label="异常状态" options={ERROR_OPTIONS} />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} md={8} xl={6} className="monitoring-logs-filter-actions-col">
                <Space wrap size="middle">
                  <Button type="primary" htmlType="submit">
                    筛选日志
                  </Button>
                  <Button onClick={() => navigate('/monitoring/device-logs')}>进入链路排查</Button>
                </Space>
              </Col>
            </Row>
          </Form>

          <Table
            rowKey="id"
            pagination={false}
            dataSource={logsPayload.items}
            columns={[
              { title: '请求 ID', dataIndex: 'request_id' },
              { title: '设备', dataIndex: 'device_id' },
              { title: '会话', dataIndex: 'session_id' },
              { title: '路由', dataIndex: 'route_type' },
              { title: '意图', dataIndex: 'intent_name' },
              { title: '耗时', dataIndex: 'latency_ms' },
              {
                title: '异常',
                dataIndex: 'is_error',
                render: (value) => (value ? <Tag color="red">异常</Tag> : <Tag color="green">正常</Tag>),
              },
            ]}
          />
        </div>
      </Card>
    </div>
  )
}

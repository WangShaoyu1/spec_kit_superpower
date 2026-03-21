import { useEffect, useState, useCallback } from 'react';
import {
  Typography,
  Card,
  Table,
  Tag,
  Input,
  Select,
  DatePicker,
  Space,
  Button,
  Drawer,
  Timeline,
  Descriptions,
  Row,
  Col,
  Empty,
  Progress,
  Spin,
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  MessageOutlined,
  ClockCircleOutlined,
  ClearOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import useMonitoringStore from '../../stores/monitoringStore';
import { monitoringApi } from '../../services/monitoringApi';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;

const STATUS_MAP = {
  success: { color: 'success', label: '成功' },
  error: { color: 'error', label: '错误' },
};

const DOMAIN_MAP = {
  command: { color: 'blue', label: '指令' },
  knowledge: { color: 'green', label: '知识' },
  chitchat: { color: 'orange', label: '闲聊' },
};

function confidenceColor(pct) {
  if (pct >= 90) return '#52c41a';
  if (pct >= 70) return '#1677ff';
  if (pct >= 50) return '#faad14';
  return '#ff4d4f';
}

function latencyTagProps(ms) {
  if (ms < 200) return { color: 'success' };
  if (ms < 2000) return { color: 'processing' };
  if (ms < 4000) return { color: 'warning' };
  return { color: 'error' };
}

export default function DeviceLogs() {
  const {
    logs,
    logsTotal,
    logsPage,
    logsPageSize,
    logsLoading,
    logFilters,
    sessionTrace,
    sessionTraceLoading,
    fetchLogs,
    setLogFilters,
    setLogsPage,
    fetchSessionTrace,
  } = useMonitoringStore();

  const [deviceId, setDeviceId] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [domain, setDomain] = useState(undefined);
  const [status, setStatus] = useState(undefined);
  const [timeRange, setTimeRange] = useState(null);
  const [traceOpen, setTraceOpen] = useState(false);
  const [deviceSummary, setDeviceSummary] = useState(null);
  const [deviceSummaryLoading, setDeviceSummaryLoading] = useState(false);

  const composeFilters = useCallback(
    (overrides = {}) => {
      const d = overrides.device_id !== undefined ? overrides.device_id : deviceId;
      const s = overrides.session_id !== undefined ? overrides.session_id : sessionId;
      const dom = overrides.domain !== undefined ? overrides.domain : domain;
      const st = overrides.status !== undefined ? overrides.status : status;
      const tr = overrides.timeRange !== undefined ? overrides.timeRange : timeRange;
      const filters = {};
      if (d) filters.device_id = d;
      if (s) filters.session_id = s;
      if (dom) filters.domain = dom;
      if (st) filters.status = st;
      if (tr?.[0]) filters.start_time = tr[0].toISOString();
      if (tr?.[1]) filters.end_time = tr[1].toISOString();
      return filters;
    },
    [deviceId, sessionId, domain, status, timeRange],
  );

  const applyFilters = useCallback(() => {
    setLogFilters(composeFilters());
  }, [composeFilters, setLogFilters]);

  useEffect(() => {
    fetchLogs();
  }, [logsPage, fetchLogs]);

  useEffect(() => {
    applyFilters();
  }, []);

  const handleSearch = () => {
    applyFilters();
    fetchLogs();
  };

  const handleClear = () => {
    setDeviceId('');
    setSessionId('');
    setDomain(undefined);
    setStatus(undefined);
    setTimeRange(null);
    setLogFilters({});
    setTimeout(() => fetchLogs(), 0);
  };

  const handleViewTrace = (sid) => {
    fetchSessionTrace(sid);
    setTraceOpen(true);
  };

  const handleDeviceLink = (id) => {
    if (!id) return;
    setDeviceId(id);
    const filters = composeFilters({ device_id: id });
    setLogFilters(filters);
    setTimeout(() => fetchLogs(), 0);
  };

  useEffect(() => {
    const id = (logFilters.device_id || '').trim();
    if (!id) {
      setDeviceSummary(null);
      return;
    }
    let cancelled = false;
    setDeviceSummaryLoading(true);
    monitoringApi
      .getDeviceSessions(id, { page: 1, page_size: 20 })
      .then((res) => {
        if (cancelled) return;
        const data = res.data;
        const items = data.items || [];
        setDeviceSummary({
          device_id: id,
          total_sessions: data.total ?? 0,
          last_active: items[0]?.last_message_at ?? null,
        });
      })
      .catch(() => {
        if (!cancelled) setDeviceSummary(null);
      })
      .finally(() => {
        if (!cancelled) setDeviceSummaryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [logFilters.device_id]);

  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      width: 170,
      render: (v) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'),
    },
    {
      title: '设备',
      dataIndex: 'device_id',
      width: 120,
      ellipsis: true,
      render: (v) =>
        v ? (
          <Button type="link" size="small" style={{ padding: 0, height: 'auto' }} onClick={() => handleDeviceLink(v)}>
            <Text style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-sm)' }}>{v}</Text>
          </Button>
        ) : (
          '-'
        ),
    },
    {
      title: '输入',
      dataIndex: 'input_text',
      ellipsis: true,
    },
    {
      title: '领域',
      dataIndex: 'domain',
      width: 80,
      render: (v) => {
        const d = DOMAIN_MAP[v];
        return d ? <Tag color={d.color}>{d.label}</Tag> : v || '-';
      },
    },
    {
      title: '意图',
      dataIndex: 'intent',
      width: 140,
      ellipsis: true,
      render: (v) => v || '-',
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      width: 120,
      render: (v) => {
        if (v == null) return '-';
        const pct = Math.round(v * 100);
        const color = confidenceColor(pct);
        return (
          <Progress
            percent={pct}
            size="small"
            strokeColor={color}
            format={(p) => `${p}%`}
            style={{ marginBottom: 0 }}
          />
        );
      },
    },
    {
      title: '延迟',
      dataIndex: 'latency_ms',
      width: 100,
      render: (v) => {
        if (v == null) return '-';
        const props = latencyTagProps(v);
        return (
          <Tag {...props} style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-sm)', margin: 0 }}>
            {v}ms
          </Tag>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: (v) => {
        const s = STATUS_MAP[v];
        return s ? <Tag color={s.color}>{s.label}</Tag> : v;
      },
    },
    {
      title: '操作',
      width: 80,
      render: (_, record) =>
        record.session_id ? (
          <Button type="link" size="small" icon={<MessageOutlined />} onClick={() => handleViewTrace(record.session_id)}>
            会话
          </Button>
        ) : null,
    },
  ];

  const expandedRowRender = (record) => (
    <Descriptions column={2} size="small" bordered>
      <Descriptions.Item label="Request ID">{record.request_id}</Descriptions.Item>
      <Descriptions.Item label="Session ID">{record.session_id || '-'}</Descriptions.Item>
      <Descriptions.Item label="意图">{record.intent || '-'}</Descriptions.Item>
      <Descriptions.Item label="槽位">
        {record.slots && Object.keys(record.slots).length > 0 ? JSON.stringify(record.slots) : '-'}
      </Descriptions.Item>
      <Descriptions.Item label="回复" span={2}>
        <Paragraph ellipsis={{ rows: 3, expandable: true }} style={{ margin: 0 }}>
          {record.response_text || '-'}
        </Paragraph>
      </Descriptions.Item>
      {record.error_message && (
        <Descriptions.Item label="错误信息" span={2}>
          <Text type="danger">{record.error_message}</Text>
        </Descriptions.Item>
      )}
      <Descriptions.Item label="模型版本">{record.model_version || '-'}</Descriptions.Item>
    </Descriptions>
  );

  const trace = sessionTrace;
  const showDeviceInfo = !!(logFilters.device_id && String(logFilters.device_id).trim());

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        <SearchOutlined style={{ marginRight: 8 }} />
        设备日志
      </Title>

      {showDeviceInfo && (
        <Card
          variant="borderless"
          style={{ borderRadius: 12, marginBottom: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}
          styles={{ body: { padding: 'var(--space-6) 24px' } }}
        >
          <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 12 }}>
            设备信息
          </Text>
          <Spin spinning={deviceSummaryLoading}>
            <Row gutter={[16, 12]}>
              <Col xs={24} sm={12} md={8}>
                <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                  设备 ID
                </Text>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-sm)' }}>
                  {deviceSummary?.device_id || logFilters.device_id}
                </div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                  型号
                </Text>
                <div style={{ fontSize: 'var(--font-size-sm)' }}>—</div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                  固件
                </Text>
                <div style={{ fontSize: 'var(--font-size-sm)' }}>—</div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                  IP
                </Text>
                <div style={{ fontSize: 'var(--font-size-sm)' }}>—</div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                  最近活跃
                </Text>
                <div style={{ fontSize: 'var(--font-size-sm)' }}>
                  {deviceSummary?.last_active ? dayjs(deviceSummary.last_active).format('YYYY-MM-DD HH:mm:ss') : '—'}
                </div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                  会话总数
                </Text>
                <div style={{ fontSize: 'var(--font-size-sm)' }}>{deviceSummary?.total_sessions ?? '—'}</div>
              </Col>
            </Row>
          </Spin>
        </Card>
      )}

      <Card
        variant="borderless"
        style={{ borderRadius: 12, marginBottom: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}
        styles={{ body: { padding: '16px 24px' } }}
      >
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="设备 ID"
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
              prefix={<FilterOutlined style={{ color: '#bfbfbf' }} />}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="会话 ID"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={5}>
            <RangePicker
              showTime
              style={{ width: '100%' }}
              value={timeRange}
              onChange={(v) => setTimeRange(v)}
            />
          </Col>
          <Col xs={24} sm={12} md={3}>
            <Select
              placeholder="领域"
              value={domain}
              onChange={setDomain}
              allowClear
              style={{ width: '100%' }}
              options={[
                { value: 'command', label: '指令' },
                { value: 'knowledge', label: '知识' },
                { value: 'chitchat', label: '闲聊' },
              ]}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="状态"
              value={status}
              onChange={setStatus}
              allowClear
              style={{ width: '100%' }}
              options={[
                { value: 'success', label: '成功' },
                { value: 'error', label: '错误' },
              ]}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Space.Compact style={{ width: '100%' }}>
              <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                查询
              </Button>
              <Button icon={<ClearOutlined />} onClick={handleClear}>
                重置
              </Button>
            </Space.Compact>
          </Col>
        </Row>
      </Card>

      <Card variant="borderless" style={{ borderRadius: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={logs}
          loading={logsLoading}
          expandable={{ expandedRowRender }}
          locale={{ emptyText: '暂无日志' }}
          pagination={{
            current: logsPage,
            pageSize: logsPageSize,
            total: logsTotal,
            onChange: setLogsPage,
            showSizeChanger: false,
            showTotal: (total) => `共 ${total} 条`,
          }}
          size="middle"
          scroll={{ x: 1000 }}
        />
      </Card>

      <Drawer
        title="会话追踪"
        open={traceOpen}
        onClose={() => setTraceOpen(false)}
        width={560}
        loading={sessionTraceLoading}
      >
        {trace ? (
          <div>
            <Descriptions column={1} size="small" style={{ marginBottom: 24 }}>
              <Descriptions.Item label="Session ID">{trace.session_id}</Descriptions.Item>
              <Descriptions.Item label="设备">{trace.device_id || '-'}</Descriptions.Item>
              <Descriptions.Item label="消息数">{trace.total_messages}</Descriptions.Item>
              <Descriptions.Item label="时间范围">
                {trace.start_time
                  ? `${dayjs(trace.start_time).format('HH:mm:ss')} → ${dayjs(trace.end_time).format('HH:mm:ss')}`
                  : '-'}
              </Descriptions.Item>
            </Descriptions>

            {trace.messages && trace.messages.length > 0 ? (
              <Timeline
                items={trace.messages.map((msg) => ({
                  color: msg.status === 'error' ? 'red' : 'blue',
                  dot: <ClockCircleOutlined />,
                  children: (
                    <div style={{ paddingBottom: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <Text strong style={{ fontSize: 13 }}>{msg.input_text}</Text>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {msg.created_at ? dayjs(msg.created_at).format('HH:mm:ss') : ''}
                        </Text>
                      </div>
                      <div style={{ fontSize: 12, color: '#666' }}>
                        {msg.domain && <Tag color={DOMAIN_MAP[msg.domain]?.color} style={{ fontSize: 11 }}>{msg.domain}</Tag>}
                        {msg.intent && <Tag style={{ fontSize: 11 }}>{msg.intent}</Tag>}
                        {msg.latency_ms != null && <span style={{ marginLeft: 4 }}>{msg.latency_ms}ms</span>}
                      </div>
                      {msg.response_text && (
                        <Paragraph
                          type="secondary"
                          ellipsis={{ rows: 2, expandable: true }}
                          style={{ margin: '4px 0 0', fontSize: 12 }}
                        >
                          → {msg.response_text}
                        </Paragraph>
                      )}
                    </div>
                  ),
                }))}
              />
            ) : (
              <Empty description="暂无会话消息" />
            )}
          </div>
        ) : (
          <Empty description="请选择一个会话" />
        )}
      </Drawer>
    </div>
  );
}

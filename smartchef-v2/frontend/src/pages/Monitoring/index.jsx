import { useEffect, useState, useCallback, useMemo, memo } from 'react';
import {
  Typography,
  Card,
  Row,
  Col,
  Statistic,
  Select,
  Switch,
  Input,
  Button,
  Table,
  Tag,
  Space,
  Spin,
  Tooltip,
  Empty,
  Badge,
  DatePicker,
} from 'antd';
import {
  DashboardOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  AlertOutlined,
  ReloadOutlined,
  SyncOutlined,
  ThunderboltOutlined,
  FieldTimeOutlined,
  AimOutlined,
  CommentOutlined,
  SearchOutlined,
  CaretUpOutlined,
  CaretDownOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import useMonitoringStore from '../../stores/monitoringStore';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const DOMAIN_GRADIENTS = {
  command: 'linear-gradient(135deg, #1677ff, #69b1ff)',
  knowledge: 'linear-gradient(135deg, #52c41a, #95de64)',
  chitchat: 'linear-gradient(135deg, #722ed1, #b37feb)',
};

const DOMAIN_COLORS = {
  command: '#1677ff',
  knowledge: '#52c41a',
  chitchat: '#722ed1',
};

const TIME_OPTIONS = [
  { value: '1h', label: '最近 1 小时' },
  { value: '6h', label: '最近 6 小时' },
  { value: '24h', label: '最近 24 小时' },
  { value: '7d', label: '最近 7 天' },
  { value: '30d', label: '最近 30 天' },
];

const ROUTE_OPTIONS = [
  { value: '', label: '全部路由' },
  { value: 'command', label: 'command' },
  { value: 'knowledge', label: 'knowledge' },
  { value: 'chitchat', label: 'chitchat' },
];

const ERROR_OPTIONS = [
  { value: '', label: '全部' },
  { value: 'normal', label: '正常' },
  { value: 'error', label: '异常' },
];

const LATENCY_BAND_OPTIONS = [
  { value: '', label: '全部延迟' },
  { value: 'lt200', label: '<200ms' },
  { value: '200_500', label: '200–500ms' },
  { value: 'gt500', label: '>500ms' },
];

function trendMeta(delta, higherIsBetter) {
  if (delta == null || Number.isNaN(delta)) return null;
  if (Math.abs(delta) < 1e-6) return { icon: null, color: 'default', label: '持平' };
  const up = delta > 0;
  const better = higherIsBetter ? up : !up;
  return {
    icon: up ? CaretUpOutlined : CaretDownOutlined,
    color: better ? 'success' : 'error',
    label: up ? '上升' : '下降',
  };
}

const StatCard = memo(function StatCard({
  title,
  value,
  suffix,
  icon,
  color,
  precision,
  previousValue,
  /** when false, lower current vs previous is "good" (e.g. latency) */
  higherIsBetter = true,
}) {
  const delta =
    previousValue != null && typeof value === 'number' && typeof previousValue === 'number'
      ? value - previousValue
      : null;
  const meta = trendMeta(delta, higherIsBetter);

  const formatDelta = () => {
    if (delta == null) return '';
    if (suffix === '%') return `${delta > 0 ? '+' : ''}${delta.toFixed(1)} pp`;
    if (suffix === 'ms') return `${delta > 0 ? '+' : ''}${Math.round(delta)} ms`;
    if (Number.isInteger(value) && Number.isInteger(previousValue)) return `${delta > 0 ? '+' : ''}${delta}`;
    return `${delta > 0 ? '+' : ''}${delta.toFixed(2)}`;
  };

  return (
    <Card
      variant="borderless"
      style={{
        borderRadius: 12,
        boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
      }}
      styles={{ body: { padding: '20px 24px' } }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Text type="secondary" style={{ fontSize: 13 }}>{title}</Text>
          <div style={{ marginTop: 8 }}>
            <Statistic
              value={value}
              suffix={suffix}
              precision={precision}
              valueStyle={{ fontSize: 28, fontWeight: 600, color: color || 'inherit' }}
            />
          </div>
          {previousValue != null && meta?.icon ? (
            <Tag
              icon={<meta.icon />}
              color={meta.color}
              style={{ marginTop: 8, fontSize: 'var(--font-size-sm)', border: 'none' }}
            >
              较上期 {formatDelta()}
            </Tag>
          ) : previousValue != null && delta != null && Math.abs(delta) < 1e-9 ? (
            <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)', marginTop: 8, display: 'block' }}>
              与上期持平
            </Text>
          ) : null}
        </div>
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: `${color || '#1677ff'}12`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 22,
            color: color || '#1677ff',
          }}
        >
          {icon}
        </div>
      </div>
    </Card>
  );
});

const TrendChart = memo(function TrendChart({ data }) {
  if (!data || data.length === 0) {
    return <Empty description="暂无趋势数据" style={{ padding: '40px 0' }} />;
  }

  const maxReq = Math.max(...data.map((d) => d.request_count), 1);

  return (
    <div style={{ padding: '8px 0' }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 120 }}>
        {data.map((point, idx) => {
          const height = Math.max((point.request_count / maxReq) * 100, 2);
          const hasErrors = point.error_count > 0;
          return (
            <Tooltip
              key={idx}
              title={
                <div style={{ fontSize: 12 }}>
                  <div>{point.time_bucket?.slice(11, 16) || `#${idx + 1}`}</div>
                  <div>请求: {point.request_count}</div>
                  <div>错误: {point.error_count}</div>
                  <div>延迟: {point.avg_latency}ms</div>
                </div>
              }
            >
              <div
                style={{
                  flex: 1,
                  height: `${height}%`,
                  minWidth: 4,
                  maxWidth: 24,
                  borderRadius: '4px 4px 0 0',
                  background: hasErrors
                    ? 'linear-gradient(180deg, #ff4d4f 0%, #ff7875 100%)'
                    : 'linear-gradient(180deg, #1677ff 0%, #69b1ff 100%)',
                  transition: 'height 0.3s ease',
                  cursor: 'pointer',
                }}
              />
            </Tooltip>
          );
        })}
      </div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: 8,
          fontSize: 11,
          color: '#999',
        }}
      >
        <span>{data[0]?.time_bucket?.slice(11, 16) || ''}</span>
        <span>{data[data.length - 1]?.time_bucket?.slice(11, 16) || ''}</span>
      </div>
    </div>
  );
});

const DomainBar = memo(function DomainBar({ distribution, previousDistribution }) {
  const prevByDomain = useMemo(() => {
    const m = {};
    (previousDistribution || []).forEach((p) => {
      m[p.domain] = p.count;
    });
    return m;
  }, [previousDistribution]);

  if (!distribution || distribution.length === 0) {
    return <Empty description="暂无领域数据" style={{ padding: '20px 0' }} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {distribution.map((d) => {
        const prev = prevByDomain[d.domain];
        const trendUp = prev != null && d.count > prev;
        const trendDown = prev != null && d.count < prev;
        const grad = DOMAIN_GRADIENTS[d.domain] || 'linear-gradient(135deg, #8c8c8c, #bfbfbf)';

        return (
          <div key={d.domain}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6, flexWrap: 'wrap', gap: 8 }}>
              <Space size={8} wrap>
                <Tag color={DOMAIN_COLORS[d.domain] || '#999'} style={{ margin: 0 }}>
                  {d.domain}
                </Tag>
                <Text strong style={{ fontSize: 'var(--font-size-sm)' }}>{d.count}</Text>
                {prev != null && (
                  <Tag
                    color={trendUp ? 'success' : trendDown ? 'error' : 'default'}
                    style={{ margin: 0, border: 'none', fontSize: 'var(--font-size-sm)' }}
                  >
                    {trendUp ? '▲' : trendDown ? '▼' : '—'} <Text type="secondary">上期 {prev}</Text>
                  </Tag>
                )}
              </Space>
              <Text type="secondary" style={{ fontSize: 13 }}>{d.percentage}%</Text>
            </div>
            <div style={{ height: 8, borderRadius: 6, background: '#f0f0f0', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${Math.min(d.percentage, 100)}%`,
                  height: '100%',
                  background: grad,
                  borderRadius: 6,
                  transition: 'width 0.35s ease',
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
});

const LOG_COLUMNS = [
  {
    title: '时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 170,
    render: (v) => (
      <Text type="secondary" style={{ fontSize: 12 }}>
        {v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'}
      </Text>
    ),
  },
  {
    title: '设备ID',
    dataIndex: 'device_id',
    key: 'device_id',
    width: 130,
    ellipsis: true,
    render: (v) => <Text style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{v || '-'}</Text>,
  },
  {
    title: '输入',
    dataIndex: 'input_text',
    key: 'input_text',
    ellipsis: true,
    render: (v) => v || '-',
  },
  {
    title: '路由',
    dataIndex: 'domain',
    key: 'domain',
    width: 100,
    render: (v) => (v ? <Tag color={DOMAIN_COLORS[v] || 'default'}>{v}</Tag> : '-'),
  },
  {
    title: '意图',
    dataIndex: 'intent',
    key: 'intent',
    width: 140,
    ellipsis: true,
    render: (v) => (v ? <Text code style={{ fontSize: 12 }}>{v}</Text> : '-'),
  },
  {
    title: '置信度',
    dataIndex: 'confidence',
    key: 'confidence',
    width: 90,
    align: 'center',
    render: (v) =>
      v != null ? (
        <Text style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          {(v * 100).toFixed(1)}%
        </Text>
      ) : '-',
  },
  {
    title: '响应耗时',
    dataIndex: 'latency_ms',
    key: 'latency_ms',
    width: 100,
    align: 'center',
    render: (v) =>
      v != null ? (
        <Text style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          {v}ms
        </Text>
      ) : '-',
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 80,
    align: 'center',
    render: (v) =>
      v === 'error' ? <Tag color="error">异常</Tag> : <Tag color="success">正常</Tag>,
  },
];

function latencyParams(band) {
  if (band === 'lt200') return { latency_min: undefined, latency_max: 199 };
  if (band === '200_500') return { latency_min: 200, latency_max: 500 };
  if (band === 'gt500') return { latency_min: 501, latency_max: undefined };
  return { latency_min: undefined, latency_max: undefined };
}

export default function Monitoring() {
  const {
    dashboard,
    dashboardLoading,
    trendData,
    trendLoading,
    timeRange,
    autoRefresh,
    autoRefreshSecondsLeft,
    logs,
    logsTotal,
    logsPage,
    logsPageSize,
    logsLoading,
    dashboardCustomStart,
    dashboardCustomEnd,
    setTimeRange,
    setDashboardCustomRange,
    fetchDashboard,
    fetchTrend,
    fetchLogs,
    setLogFilters,
    setLogsPage,
    toggleAutoRefresh,
    clearAutoRefresh,
    resetAutoRefreshCountdown,
  } = useMonitoringStore();

  const [deviceIdFilter, setDeviceIdFilter] = useState('');
  const [routeFilter, setRouteFilter] = useState('');
  const [errorFilter, setErrorFilter] = useState('');
  const [intentFilter, setIntentFilter] = useState('');
  const [latencyBand, setLatencyBand] = useState('');
  const [logTimeRange, setLogTimeRange] = useState(null);

  const loadData = useCallback(() => {
    resetAutoRefreshCountdown();
    Promise.all([fetchDashboard(), fetchTrend()]);
  }, [fetchDashboard, fetchTrend, resetAutoRefreshCountdown]);

  useEffect(() => {
    return () => clearAutoRefresh();
  }, [clearAutoRefresh]);

  useEffect(() => {
    loadData();
  }, [loadData, timeRange, dashboardCustomStart, dashboardCustomEnd]);

  useEffect(() => {
    fetchLogs();
  }, [logsPage, fetchLogs]);

  const handleLogSearch = useCallback(() => {
    const { latency_min, latency_max } = latencyParams(latencyBand);
    const filters = {};
    if (deviceIdFilter) filters.device_id = deviceIdFilter;
    if (routeFilter) filters.domain = routeFilter;
    if (errorFilter === 'error') filters.status = 'error';
    else if (errorFilter === 'normal') filters.status = 'success';
    if (intentFilter.trim()) filters.intent = intentFilter.trim();
    if (latency_min != null) filters.latency_min = latency_min;
    if (latency_max != null) filters.latency_max = latency_max;
    if (logTimeRange?.[0]) filters.start_time = logTimeRange[0].toISOString();
    if (logTimeRange?.[1]) filters.end_time = logTimeRange[1].toISOString();
    setLogFilters(filters);
    fetchLogs();
  }, [
    deviceIdFilter,
    routeFilter,
    errorFilter,
    intentFilter,
    latencyBand,
    logTimeRange,
    setLogFilters,
    fetchLogs,
  ]);

  const handleLogReset = useCallback(() => {
    setDeviceIdFilter('');
    setRouteFilter('');
    setErrorFilter('');
    setIntentFilter('');
    setLatencyBand('');
    setLogTimeRange(null);
    setLogFilters({});
    fetchLogs();
  }, [setLogFilters, fetchLogs]);

  const d = dashboard || {};
  const prev = d.previous_period || {};

  const dashPickerValue =
    dashboardCustomStart && dashboardCustomEnd
      ? [dayjs(dashboardCustomStart), dayjs(dashboardCustomEnd)]
      : null;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <Title level={4} style={{ margin: 0 }}>
          <DashboardOutlined style={{ marginRight: 8 }} />
          监控中心
        </Title>
        <Space size="middle" wrap>
          <Space size={8} align="center">
            <Text type="secondary" style={{ fontSize: 13 }}>自动刷新</Text>
            <Switch
              checked={autoRefresh}
              onChange={toggleAutoRefresh}
              checkedChildren={<SyncOutlined spin />}
              size="small"
            />
            {autoRefresh ? (
              <Badge
                count={autoRefreshSecondsLeft}
                showZero
                style={{
                  backgroundColor: autoRefreshSecondsLeft <= 5 ? '#faad14' : '#1677ff',
                  fontVariantNumeric: 'tabular-nums',
                  boxShadow: 'none',
                }}
              />
            ) : null}
          </Space>
          <Select
            value={timeRange}
            onChange={(v) => {
              setTimeRange(v);
            }}
            options={TIME_OPTIONS}
            style={{ width: 150 }}
            size="small"
          />
          <RangePicker
            showTime
            size="small"
            value={dashPickerValue}
            onChange={(dates) => {
              if (dates?.[0] && dates?.[1]) {
                setDashboardCustomRange(dates[0].toISOString(), dates[1].toISOString());
              } else {
                setDashboardCustomRange(null, null);
              }
            }}
            style={{ minWidth: 280 }}
          />
          <Tooltip title="刷新">
            <ReloadOutlined
              onClick={loadData}
              spin={dashboardLoading}
              style={{ fontSize: 16, cursor: 'pointer', color: '#1677ff' }}
            />
          </Tooltip>
        </Space>
      </div>

      <Spin spinning={dashboardLoading}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <StatCard
              title="请求总量"
              value={d.request_count ?? 0}
              previousValue={prev.request_count}
              icon={<DashboardOutlined />}
              color="#1677ff"
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <StatCard
              title="成功率"
              value={d.success_rate ?? 0}
              suffix="%"
              precision={1}
              previousValue={prev.success_rate}
              icon={<CheckCircleOutlined />}
              color="#52c41a"
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <StatCard
              title="平均延迟"
              value={d.avg_latency ?? 0}
              suffix="ms"
              precision={0}
              previousValue={prev.avg_latency}
              higherIsBetter={false}
              icon={<ClockCircleOutlined />}
              color="#faad14"
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <StatCard
              title="活跃告警"
              value={d.active_alerts ?? 0}
              previousValue={undefined}
              higherIsBetter={false}
              icon={<AlertOutlined />}
              color={d.active_alerts > 0 ? '#ff4d4f' : '#8c8c8c'}
            />
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} sm={12} lg={6}>
            <StatCard
              title="实时 QPS"
              value={d.qps ?? 0}
              precision={2}
              previousValue={prev.qps}
              icon={<ThunderboltOutlined />}
              color="#722ed1"
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <StatCard
              title="P99 延迟"
              value={d.p99_latency ?? 0}
              suffix="ms"
              precision={0}
              previousValue={prev.p99_latency}
              higherIsBetter={false}
              icon={<FieldTimeOutlined />}
              color="#eb2f96"
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <StatCard
              title="意图准确率"
              value={d.intent_accuracy ?? 0}
              suffix="%"
              precision={1}
              previousValue={prev.intent_accuracy}
              icon={<AimOutlined />}
              color="#13c2c2"
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <StatCard
              title="对话轮次"
              value={d.dialog_turns ?? 0}
              precision={0}
              previousValue={prev.dialog_turns}
              icon={<CommentOutlined />}
              color="#597ef7"
            />
          </Col>
        </Row>
      </Spin>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={16}>
          <Card
            title="请求趋势"
            variant="borderless"
            style={{ borderRadius: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}
            loading={trendLoading}
          >
            <TrendChart data={trendData} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card
            title="领域分布"
            variant="borderless"
            style={{ borderRadius: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}
            loading={dashboardLoading}
          >
            <DomainBar
              distribution={d.domain_distribution}
              previousDistribution={prev.domain_distribution}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="请求日志"
        variant="borderless"
        style={{ borderRadius: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', marginTop: 16 }}
      >
        <div
          style={{
            display: 'flex',
            gap: 12,
            flexWrap: 'wrap',
            alignItems: 'center',
            marginBottom: 16,
          }}
        >
          <RangePicker showTime value={logTimeRange} onChange={(v) => setLogTimeRange(v)} style={{ minWidth: 260 }} />
          <Input
            placeholder="意图名称"
            value={intentFilter}
            onChange={(e) => setIntentFilter(e.target.value)}
            style={{ width: 160 }}
            allowClear
          />
          <Select
            value={latencyBand}
            onChange={setLatencyBand}
            options={LATENCY_BAND_OPTIONS}
            style={{ width: 140 }}
          />
          <Input
            placeholder="设备ID"
            value={deviceIdFilter}
            onChange={(e) => setDeviceIdFilter(e.target.value)}
            style={{ width: 160 }}
            allowClear
          />
          <Select
            value={routeFilter}
            onChange={setRouteFilter}
            options={ROUTE_OPTIONS}
            style={{ width: 140 }}
            placeholder="路由类型"
          />
          <Select
            value={errorFilter}
            onChange={setErrorFilter}
            options={ERROR_OPTIONS}
            style={{ width: 120 }}
            placeholder="是否异常"
          />
          <Button type="primary" icon={<SearchOutlined />} onClick={handleLogSearch}>
            查询
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleLogReset}>
            重置
          </Button>
        </div>

        <Table
          rowKey="id"
          columns={LOG_COLUMNS}
          dataSource={logs}
          loading={logsLoading}
          size="small"
          scroll={{ x: 1000 }}
          locale={{ emptyText: '暂无请求日志' }}
          pagination={{
            current: logsPage,
            pageSize: logsPageSize,
            total: logsTotal,
            showSizeChanger: false,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (p) => setLogsPage(p),
          }}
        />
      </Card>
    </div>
  );
}

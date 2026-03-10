import { useEffect, useState, useRef, useCallback } from 'react';
import {
  Card, Row, Col, Statistic, Table, Tag, Typography, Space, Select, Progress, Tooltip,
} from 'antd';
import {
  ThunderboltOutlined, ClockCircleOutlined, AimOutlined, BarChartOutlined,
} from '@ant-design/icons';
import api from '../../services/api';

const { Text } = Typography;

const DOMAIN_COLORS = {
  command: '#1677ff',
  knowledge: '#52c41a',
  chitchat: '#722ed1',
};

const DOMAIN_LABELS = {
  command: '指令',
  knowledge: '知识',
  chitchat: '闲聊',
};

const INTERVAL_OPTIONS = [
  { label: '10 秒', value: 10000 },
  { label: '30 秒', value: 30000 },
  { label: '1 分钟', value: 60000 },
  { label: '5 分钟', value: 300000 },
];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [interval, setInterval_] = useState(30000);
  const timerRef = useRef(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsRes, logsRes] = await Promise.all([
        api.get('/monitoring/stats', { params: { hours: 24 } }),
        api.get('/monitoring/logs', { params: { limit: 20 } }),
      ]);
      setStats(statsRes.data);
      setLogs(logsRes.data);
    } catch { /* 静默失败，面板自动重试 */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    clearInterval(timerRef.current);
    timerRef.current = setInterval(fetchData, interval);
    return () => clearInterval(timerRef.current);
  }, [interval, fetchData]);

  const totalRequests = stats?.total_requests || 0;
  const avgLatency = stats?.avg_latency_ms || 0;
  const domains = stats?.domain_distribution || {};
  const domainTotal = Object.values(domains).reduce((s, v) => s + v, 0) || 1;

  // 近似 QPS = 总请求 / (24 * 3600)
  const qps = totalRequests > 0 ? (totalRequests / (24 * 3600)).toFixed(2) : '0.00';

  // 准确率：用 command 域的占比近似（后端 stats 没有 accuracy 字段时用 N/A）
  const accuracy = stats?.intent_accuracy != null
    ? `${(stats.intent_accuracy * 100).toFixed(1)}%`
    : 'N/A';

  const logColumns = [
    { title: '设备ID', dataIndex: 'device_id', width: 120, ellipsis: true },
    { title: '输入', dataIndex: 'input_text', ellipsis: true },
    {
      title: '路由', dataIndex: 'domain', width: 80,
      render: (v) => <Tag color={DOMAIN_COLORS[v] || 'default'}>{DOMAIN_LABELS[v] || v}</Tag>,
    },
    { title: '意图', dataIndex: 'intent', width: 140, ellipsis: true },
    { title: '延迟', dataIndex: 'latency_ms', width: 80, render: (v) => `${v}ms` },
    {
      title: '时间', dataIndex: 'created_at', width: 170,
      render: (v) => new Date(v).toLocaleString('zh-CN'),
    },
  ];

  return (
    <div>
      {/* 刷新间隔选择器 */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
        <Space>
          <Text type="secondary">自动刷新：</Text>
          <Select
            size="small"
            value={interval}
            onChange={setInterval_}
            options={INTERVAL_OPTIONS}
            style={{ width: 100 }}
          />
        </Space>
      </div>

      {/* 指标卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card hoverable>
            <Statistic
              title="QPS（24h 均值）"
              value={qps}
              prefix={<ThunderboltOutlined style={{ color: '#1677ff' }} />}
              suffix="req/s"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable>
            <Statistic
              title="平均延迟"
              value={avgLatency}
              precision={1}
              prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
              suffix="ms"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable>
            <Statistic
              title="准确率"
              value={accuracy}
              prefix={<AimOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable>
            <Statistic
              title="今日请求数"
              value={totalRequests}
              prefix={<BarChartOutlined style={{ color: '#722ed1' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 路由分布 */}
      <Card title="路由分布" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={24} align="middle">
          {Object.entries(domains).map(([domain, count]) => {
            const pct = ((count / domainTotal) * 100).toFixed(1);
            return (
              <Col span={8} key={domain}>
                <Tooltip title={`${count} 次请求`}>
                  <div style={{ marginBottom: 8 }}>
                    <Space>
                      <Text strong>{DOMAIN_LABELS[domain] || domain}</Text>
                      <Text type="secondary">{pct}%</Text>
                    </Space>
                  </div>
                  <Progress
                    percent={parseFloat(pct)}
                    strokeColor={DOMAIN_COLORS[domain] || '#999'}
                    showInfo={false}
                  />
                </Tooltip>
              </Col>
            );
          })}
        </Row>
      </Card>

      {/* 最近请求列表 */}
      <Card title="最近请求" size="small">
        <Table
          rowKey="id"
          columns={logColumns}
          dataSource={logs}
          loading={loading}
          size="small"
          pagination={{ pageSize: 10, showSizeChanger: false }}
        />
      </Card>
    </div>
  );
}

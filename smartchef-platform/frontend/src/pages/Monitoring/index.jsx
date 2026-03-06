import { useEffect, useState, useRef } from 'react';
import {
  Card, Row, Col, Statistic, Table, Tag, Typography, Space, Input, Select, Button, message,
} from 'antd';
import { ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { Title, Text } = Typography;

const REFRESH_INTERVAL = 30000;

export default function MonitoringPage() {
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [deviceHistory, setDeviceHistory] = useState([]);
  const [searchDeviceId, setSearchDeviceId] = useState('');
  const [filterDomain, setFilterDomain] = useState(null);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef(null);

  const fetchStats = async () => {
    try {
      const res = await api.get('/monitoring/stats', { params: { hours: 24 } });
      setStats(res.data);
    } catch { /* */ }
  };

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = { limit: 100 };
      if (filterDomain) params.domain = filterDomain;
      const res = await api.get('/monitoring/logs', { params });
      setLogs(res.data);
    } catch { message.error('加载日志失败'); }
    finally { setLoading(false); }
  };

  const searchDevice = async () => {
    if (!searchDeviceId.trim()) return;
    try {
      const res = await api.get(`/monitoring/devices/${searchDeviceId}/history`);
      setDeviceHistory(res.data);
    } catch { message.error('查询设备失败'); }
  };

  useEffect(() => {
    fetchStats();
    fetchLogs();
    timerRef.current = setInterval(() => { fetchStats(); fetchLogs(); }, REFRESH_INTERVAL);
    return () => clearInterval(timerRef.current);
  }, []);

  useEffect(() => { fetchLogs(); }, [filterDomain]);

  const logColumns = [
    { title: '设备ID', dataIndex: 'device_id', width: 120, ellipsis: true },
    { title: '输入', dataIndex: 'input_text', ellipsis: true },
    { title: '域', dataIndex: 'domain', width: 80, render: v => <Tag>{v}</Tag> },
    { title: '意图', dataIndex: 'intent', width: 140 },
    { title: '延迟', dataIndex: 'latency_ms', width: 80, render: v => `${v}ms` },
    { title: '时间', dataIndex: 'created_at', width: 160, render: v => new Date(v).toLocaleString() },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>监控仪表盘</Title>
        <Text type="secondary">每 30 秒自动刷新</Text>
      </div>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card><Statistic title="总请求数 (24h)" value={stats?.total_requests || 0} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="平均延迟" value={stats?.avg_latency_ms || 0} suffix="ms" precision={1} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="活跃设备" value={stats?.unique_devices || 0} /></Card>
        </Col>
        <Col span={6}>
          <Card>
            <div style={{ marginBottom: 4 }}><Text type="secondary">域分布</Text></div>
            <Space wrap>
              {Object.entries(stats?.domain_distribution || {}).map(([k, v]) => (
                <Tag key={k} color={k === 'command' ? 'blue' : k === 'knowledge' ? 'green' : 'purple'}>
                  {k}: {v}
                </Tag>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>

      <Card title="设备ID查询" size="small" style={{ marginBottom: 16 }}>
        <Space>
          <Input placeholder="输入设备ID" value={searchDeviceId}
            onChange={e => setSearchDeviceId(e.target.value)} onPressEnter={searchDevice}
            style={{ width: 300 }}
          />
          <Button icon={<SearchOutlined />} onClick={searchDevice}>查询</Button>
        </Space>
        {deviceHistory.length > 0 && (
          <Table rowKey="id" columns={logColumns} dataSource={deviceHistory}
            size="small" pagination={false} style={{ marginTop: 12 }} scroll={{ y: 200 }}
          />
        )}
      </Card>

      <Card title="请求日志" size="small"
        extra={
          <Space>
            <Select allowClear placeholder="域过滤" value={filterDomain} onChange={setFilterDomain} style={{ width: 120 }}
              options={[{ label: 'command', value: 'command' }, { label: 'knowledge', value: 'knowledge' }, { label: 'chitchat', value: 'chitchat' }]}
            />
            <Button icon={<ReloadOutlined />} onClick={fetchLogs}>刷新</Button>
          </Space>
        }
      >
        <Table rowKey="id" columns={logColumns} dataSource={logs} loading={loading}
          size="small" pagination={{ pageSize: 20 }}
        />
      </Card>
    </div>
  );
}

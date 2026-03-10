import { useState } from 'react';
import {
  Card, Input, Button, Table, Tag, Space, Typography, DatePicker, Empty, Collapse, Descriptions, message,
} from 'antd';
import { SearchOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import api from '../../services/api';

const { Text } = Typography;
const { RangePicker } = DatePicker;

const DOMAIN_COLORS = { command: 'blue', knowledge: 'green', chitchat: 'purple' };
const DOMAIN_LABELS = { command: '指令', knowledge: '知识', chitchat: '闲聊' };

/**
 * 按时间间隔分组为"会话"：连续请求间隔 > gap 分钟则拆分为新会话。
 */
function groupIntoSessions(logs, gapMinutes = 5) {
  if (!logs.length) return [];
  const sorted = [...logs].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  const sessions = [];
  let current = { requests: [sorted[0]] };

  for (let i = 1; i < sorted.length; i++) {
    const prev = new Date(sorted[i - 1].created_at);
    const curr = new Date(sorted[i].created_at);
    if ((curr - prev) / 60000 > gapMinutes) {
      sessions.push(current);
      current = { requests: [] };
    }
    current.requests.push(sorted[i]);
  }
  sessions.push(current);

  return sessions.reverse().map((s, idx) => ({
    key: idx,
    start: s.requests[0].created_at,
    end: s.requests[s.requests.length - 1].created_at,
    count: s.requests.length,
    requests: s.requests,
  }));
}

export default function DeviceLogs() {
  const [deviceId, setDeviceId] = useState('');
  const [timeRange, setTimeRange] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    const id = deviceId.trim();
    if (!id) {
      message.warning('请输入设备 ID');
      return;
    }
    setLoading(true);
    setSearched(true);
    try {
      const res = await api.get(`/monitoring/devices/${id}/history`, {
        params: { limit: 200 },
      });
      let logs = res.data || [];

      // 客户端时间范围过滤
      if (timeRange && timeRange[0] && timeRange[1]) {
        const start = timeRange[0].startOf('day').valueOf();
        const end = timeRange[1].endOf('day').valueOf();
        logs = logs.filter((l) => {
          const t = new Date(l.created_at).getTime();
          return t >= start && t <= end;
        });
      }

      setSessions(groupIntoSessions(logs));
    } catch {
      message.error('查询设备历史失败');
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  const sessionColumns = [
    {
      title: '会话时段',
      key: 'time',
      render: (_, r) => (
        <Space>
          <ClockCircleOutlined />
          <Text>{dayjs(r.start).format('MM-DD HH:mm')}</Text>
          <Text type="secondary">→</Text>
          <Text>{dayjs(r.end).format('MM-DD HH:mm')}</Text>
        </Space>
      ),
    },
    {
      title: '请求数',
      dataIndex: 'count',
      width: 100,
      render: (v) => <Tag>{v} 轮</Tag>,
    },
  ];

  const renderRequestChain = (requests) => (
    <Collapse
      size="small"
      items={requests.map((req, idx) => ({
        key: req.id || idx,
        label: (
          <Space>
            <Tag>{idx + 1}</Tag>
            <Text ellipsis style={{ maxWidth: 300 }}>{req.input_text}</Text>
            <Tag color={DOMAIN_COLORS[req.domain]}>{DOMAIN_LABELS[req.domain] || req.domain}</Tag>
            <Text type="secondary">{req.latency_ms}ms</Text>
          </Space>
        ),
        children: (
          <Descriptions size="small" column={2} bordered>
            <Descriptions.Item label="用户输入" span={2}>{req.input_text}</Descriptions.Item>
            <Descriptions.Item label="路由域">{req.domain}</Descriptions.Item>
            <Descriptions.Item label="意图">{req.intent || '-'}</Descriptions.Item>
            <Descriptions.Item label="响应" span={2}>{req.response_text || '-'}</Descriptions.Item>
            <Descriptions.Item label="延迟">{req.latency_ms}ms</Descriptions.Item>
            <Descriptions.Item label="语言">{req.language || '-'}</Descriptions.Item>
            <Descriptions.Item label="时间" span={2}>
              {dayjs(req.created_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          </Descriptions>
        ),
      }))}
    />
  );

  return (
    <div>
      {/* 搜索栏 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input
            placeholder="输入设备 ID"
            prefix={<SearchOutlined />}
            value={deviceId}
            onChange={(e) => setDeviceId(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 280 }}
            allowClear
          />
          <RangePicker
            value={timeRange}
            onChange={setTimeRange}
            placeholder={['开始日期', '结束日期']}
          />
          <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch} loading={loading}>
            搜索
          </Button>
        </Space>
      </Card>

      {/* 会话列表 */}
      {searched && sessions.length === 0 && !loading && (
        <Empty description="未找到该设备的对话记录" />
      )}

      {sessions.length > 0 && (
        <Card title={`设备 ${deviceId} 的会话记录（共 ${sessions.length} 个会话）`} size="small">
          <Table
            rowKey="key"
            columns={sessionColumns}
            dataSource={sessions}
            loading={loading}
            size="small"
            pagination={{ pageSize: 10 }}
            expandable={{
              expandedRowRender: (record) => renderRequestChain(record.requests),
            }}
          />
        </Card>
      )}
    </div>
  );
}

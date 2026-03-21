import { useEffect, useState, useMemo } from 'react';
import {
  Typography,
  Card,
  Table,
  Tag,
  Switch,
  Button,
  Space,
  Row,
  Col,
  Statistic,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  Popconfirm,
  message,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  AlertOutlined,
  BellOutlined,
  CheckCircleOutlined,
  StopOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import useMonitoringStore from '../../stores/monitoringStore';

const { Title, Text } = Typography;

const METRIC_OPTIONS = [
  { value: 'accuracy_rate', label: '准确率' },
  { value: 'p95_latency', label: 'P95 延迟' },
  { value: 'p99_latency', label: 'P99 延迟' },
  { value: 'avg_latency', label: '平均延迟' },
  { value: 'error_rate', label: '错误率' },
  { value: 'qps', label: 'QPS' },
  { value: 'request_count', label: '请求数量' },
];

const OPERATOR_OPTIONS = [
  { value: 'gt', label: '大于 (>)' },
  { value: 'lt', label: '小于 (<)' },
  { value: 'gte', label: '大于等于 (>=)' },
  { value: 'lte', label: '小于等于 (<=)' },
  { value: 'eq', label: '等于 (=)' },
];

const WINDOW_UNIT_OPTIONS = [
  { value: 'seconds', label: '秒' },
  { value: 'minutes', label: '分钟' },
  { value: 'hours', label: '小时' },
];

const CHANNEL_OPTIONS = [
  { value: 'email', label: '邮件' },
  { value: 'webhook', label: 'Webhook' },
  { value: 'log', label: '日志' },
];

const OPERATOR_SYMBOL = { gt:'>', lt:'<', gte:'≥', lte:'≤', eq:'=' };

const LATENCY_METRICS = new Set(['p95_latency', 'p99_latency', 'avg_latency']);

const EVENT_STATUS_MAP = {
  pending: { color: 'default', label: '待处理' },
  firing: { color: 'error', label: '告警中' },
  resolved: { color: 'success', label: '已恢复' },
};

function windowMinutes(value, unit) {
  const v = Number(value) || 1;
  if (unit === 'hours') return Math.max(1, Math.round(v * 60));
  if (unit === 'seconds') return Math.max(1, Math.round(v / 60));
  return Math.max(1, Math.round(v));
}

function splitWindowForEdit(totalMinutes) {
  const m = totalMinutes || 5;
  if (m >= 60 && m % 60 === 0) return { window_value: m / 60, window_unit: 'hours' };
  return { window_value: m, window_unit: 'minutes' };
}

export default function AlertRules() {
  const {
    alertRules,
    alertRulesTotal,
    alertRulesPage,
    alertRulesLoading,
    alertEvents,
    alertEventsTotal,
    alertEventsPage,
    alertEventsLoading,
    fetchAlertRules,
    createAlertRule,
    updateAlertRule,
    deleteAlertRule,
    toggleAlertRule,
    setAlertRulesPage,
    fetchAlertEvents,
    setAlertEventsPage,
  } = useMonitoringStore();

  const [form] = Form.useForm();
  const metricWatch = Form.useWatch('metric', form);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [submitLoading, setSubmitLoading] = useState(false);

  useEffect(() => {
    fetchAlertRules();
    fetchAlertEvents();
  }, [fetchAlertRules, fetchAlertEvents]);

  const ruleStats = useMemo(() => {
    const rules = alertRules || [];
    const total = rules.length;
    const enabled = rules.filter((r) => r.is_enabled).length;
    const disabled = total - enabled;
    const firingEvents = (alertEvents || []).filter((e) => e.status === 'firing').length;
    return { total, enabled, disabled, activeAlerts: firingEvents };
  }, [alertRules, alertEvents]);

  const handleCreate = () => {
    setEditingRule(null);
    form.resetFields();
    form.setFieldsValue({
      window_value: 5,
      window_unit: 'minutes',
      metric: 'error_rate',
      operator: 'gt',
    });
    setModalOpen(true);
  };

  const handleEdit = (record) => {
    setEditingRule(record);
    const win = splitWindowForEdit(record.window_minutes);
    const base = {
      name: record.name,
      metric: record.metric,
      notification_channels: record.notification_channels || [],
      description: record.description,
      window_value: win.window_value,
      window_unit: win.window_unit,
    };
    if (record.metric === 'accuracy_rate') {
      form.setFieldsValue({
        ...base,
        accuracy_drop: Math.max(0, Math.min(100, 100 - record.threshold)),
        operator: 'lt',
      });
    } else if (LATENCY_METRICS.has(record.metric)) {
      form.setFieldsValue({
        ...base,
        threshold: record.threshold,
        operator: record.operator || 'gt',
      });
    } else {
      form.setFieldsValue({
        ...base,
        operator: record.operator,
        threshold: record.threshold,
      });
    }
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const window_minutes = windowMinutes(values.window_value, values.window_unit);

      const payload = {
        name: values.name,
        metric: values.metric,
        window_minutes,
        notification_channels: values.notification_channels,
        description: values.description,
      };

      if (values.metric === 'accuracy_rate') {
        const drop = Number(values.accuracy_drop) || 0;
        payload.operator = 'lt';
        payload.threshold = Math.max(0, Math.min(100, 100 - drop));
      } else {
        payload.operator = values.operator;
        payload.threshold = values.threshold;
      }

      setSubmitLoading(true);
      if (editingRule) {
        await updateAlertRule(editingRule.id, payload);
        message.success('规则已更新');
      } else {
        await createAlertRule(payload);
        message.success('规则已创建');
      }
      setModalOpen(false);
    } catch (e) {
      if (e?.errorFields) return;
      message.error(e?.message || '提交失败');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDelete = async (id) => {
    await deleteAlertRule(id);
    message.success('规则已删除');
  };

  const handleToggle = async (id, checked) => {
    await toggleAlertRule(id, checked);
  };

  const renderCondition = (_, r) => {
    if (r.metric === 'accuracy_rate') {
      const drop = Math.round(100 - r.threshold);
      return (
        <Text style={{ fontSize: 'var(--font-size-sm)' }}>
          下降超过 <Text strong>{drop}%</Text>（低于 <Text code>{r.threshold}%</Text>）
        </Text>
      );
    }
    if (LATENCY_METRICS.has(r.metric)) {
      return (
        <Text style={{ fontSize: 'var(--font-size-sm)' }}>
          超过 <Text code>{r.threshold}ms</Text>（{OPERATOR_SYMBOL[r.operator] || r.operator}）
        </Text>
      );
    }
    return (
      <Text code style={{ fontSize: 'var(--font-size-sm)' }}>
        {OPERATOR_SYMBOL[r.operator] || r.operator} {r.threshold}
      </Text>
    );
  };

  const renderWindow = (_, r) => {
    const m = r.window_minutes || 0;
    if (m >= 1440 && m % 1440 === 0) return `${m / 1440} 天`;
    if (m >= 60 && m % 60 === 0) return `${m / 60} 小时`;
    return `${m} 分钟`;
  };

  const ruleColumns = [
    { title: '名称', dataIndex: 'name', width: 180 },
    {
      title: '指标',
      dataIndex: 'metric',
      width: 120,
      render: (v) => METRIC_OPTIONS.find((m) => m.value === v)?.label || v,
    },
    { title: '条件', width: 200, render: renderCondition },
    { title: '窗口', width: 100, render: renderWindow },
    {
      title: '上次触发',
      dataIndex: 'last_fired_at',
      width: 170,
      render: (v) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '—'),
    },
    {
      title: '启用',
      dataIndex: 'is_enabled',
      width: 80,
      render: (v, r) => (
        <Switch checked={v} onChange={(checked) => handleToggle(r.id, checked)} size="small" />
      ),
    },
    {
      title: '通知渠道',
      dataIndex: 'notification_channels',
      width: 160,
      render: (channels) =>
        channels?.map((c) => (
          <Tag key={c}>{CHANNEL_OPTIONS.find((o) => o.value === c)?.label || c}</Tag>
        )),
    },
    {
      title: '操作',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="确认删除此规则？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const eventColumns = [
    { title: '规则', dataIndex: 'rule_name', width: 160 },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (v) => {
        const s = EVENT_STATUS_MAP[v];
        return s ? <Tag color={s.color}>{s.label}</Tag> : v;
      },
    },
    {
      title: '指标值',
      dataIndex: 'metric_value',
      width: 100,
      render: (v) => (v != null ? v.toFixed(2) : '-'),
    },
    {
      title: '阈值',
      dataIndex: 'threshold_value',
      width: 100,
      render: (v) => (v != null ? v.toFixed(2) : '-'),
    },
    {
      title: '触发时间',
      dataIndex: 'fired_at',
      width: 170,
      render: (v) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'),
    },
    {
      title: '恢复时间',
      dataIndex: 'resolved_at',
      width: 170,
      render: (v) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-'),
    },
    { title: '消息', dataIndex: 'message', ellipsis: true },
  ];

  const isAccuracy = metricWatch === 'accuracy_rate';
  const isLatency = metricWatch && LATENCY_METRICS.has(metricWatch);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0 }}>
          <AlertOutlined style={{ marginRight: 8 }} />
          告警规则
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建规则
        </Button>
      </div>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card
            variant="borderless"
            style={{ borderRadius: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}
            styles={{ body: { padding: '16px 20px' } }}
          >
            <Statistic
              title={<span style={{ fontSize: 13 }}>活跃告警</span>}
              value={ruleStats.activeAlerts}
              prefix={<AlertOutlined style={{ color: ruleStats.activeAlerts > 0 ? '#ff4d4f' : '#8c8c8c' }} />}
              valueStyle={{ color: ruleStats.activeAlerts > 0 ? '#ff4d4f' : 'inherit' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card
            variant="borderless"
            style={{ borderRadius: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}
            styles={{ body: { padding: '16px 20px' } }}
          >
            <Statistic
              title={<span style={{ fontSize: 13 }}>规则总数</span>}
              value={alertRulesTotal || ruleStats.total}
              prefix={<UnorderedListOutlined style={{ color: '#1677ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card
            variant="borderless"
            style={{ borderRadius: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}
            styles={{ body: { padding: '16px 20px' } }}
          >
            <Statistic
              title={<span style={{ fontSize: 13 }}>已启用</span>}
              value={ruleStats.enabled}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card
            variant="borderless"
            style={{ borderRadius: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}
            styles={{ body: { padding: '16px 20px' } }}
          >
            <Statistic
              title={<span style={{ fontSize: 13 }}>已禁用</span>}
              value={ruleStats.disabled}
              prefix={<StopOutlined style={{ color: '#8c8c8c' }} />}
              valueStyle={{ color: '#8c8c8c' }}
            />
          </Card>
        </Col>
      </Row>

      <Card
        variant="borderless"
        style={{ borderRadius: 12, marginBottom: 24, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}
      >
        <Table
          rowKey="id"
          columns={ruleColumns}
          dataSource={alertRules}
          loading={alertRulesLoading}
          locale={{ emptyText: '暂无告警规则' }}
          pagination={{
            current: alertRulesPage,
            pageSize: 20,
            total: alertRulesTotal,
            onChange: (p) => {
              setAlertRulesPage(p);
              fetchAlertRules();
            },
            showTotal: (total) => `共 ${total} 条`,
          }}
          size="middle"
          scroll={{ x: 1100 }}
        />
      </Card>

      <Card
        title={
          <Space>
            <BellOutlined />
            <span>告警事件</span>
          </Space>
        }
        variant="borderless"
        style={{ borderRadius: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}
      >
        <Table
          rowKey="id"
          columns={eventColumns}
          dataSource={alertEvents}
          loading={alertEventsLoading}
          locale={{ emptyText: '暂无告警事件' }}
          pagination={{
            current: alertEventsPage,
            pageSize: 20,
            total: alertEventsTotal,
            onChange: (p) => {
              setAlertEventsPage(p);
              fetchAlertEvents();
            },
            showTotal: (total) => `共 ${total} 条`,
          }}
          size="middle"
          scroll={{ x: 900 }}
        />
      </Card>

      <Modal
        title={editingRule ? '编辑规则' : '新建规则'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        confirmLoading={submitLoading}
        width={600}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="name" label="规则名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="如：错误率过高告警" maxLength={128} />
          </Form.Item>
          <Form.Item name="metric" label="监控指标" rules={[{ required: true, message: '请选择指标' }]}>
            <Select
              options={METRIC_OPTIONS}
              placeholder="选择指标"
              onChange={() => {
                form.setFieldsValue({ threshold: undefined, accuracy_drop: undefined });
              }}
            />
          </Form.Item>

          {isAccuracy ? (
            <Form.Item
              name="accuracy_drop"
              label="下降超过（%）"
              rules={[{ required: true, message: '请输入百分比' }]}
              initialValue={10}
            >
              <InputNumber min={0} max={99} precision={0} addonAfter="%" style={{ width: '100%' }} placeholder="相对下降幅度" />
            </Form.Item>
          ) : isLatency ? (
            <Space style={{ width: '100%' }} align="start" wrap>
              <Form.Item name="operator" label="条件" rules={[{ required: true }]}>
                <Select options={[{ value: 'gt', label: '超过' }, { value: 'gte', label: '不低于即超过含界' }]} style={{ width: 140 }} />
              </Form.Item>
              <Form.Item name="threshold" label="延迟阈值" rules={[{ required: true, message: '请输入 ms' }]}>
                <InputNumber min={0} addonAfter="ms" style={{ width: 160 }} />
              </Form.Item>
            </Space>
          ) : (
            <Space style={{ width: '100%' }} align="start" wrap>
              <Form.Item name="operator" label="操作符" rules={[{ required: true, message: '请选择' }]}>
                <Select options={OPERATOR_OPTIONS} style={{ width: 150 }} placeholder="选择操作符" />
              </Form.Item>
              <Form.Item name="threshold" label="阈值" rules={[{ required: true, message: '请输入阈值' }]}>
                <InputNumber style={{ width: 180 }} placeholder="阈值" />
              </Form.Item>
            </Space>
          )}

          <Space style={{ width: '100%' }} align="start" wrap>
            <Form.Item
              name="window_value"
              label="持续时间"
              rules={[{ required: true, message: '请输入' }]}
              initialValue={5}
            >
              <InputNumber min={1} style={{ width: 140 }} />
            </Form.Item>
            <Form.Item name="window_unit" label="单位" rules={[{ required: true }]} initialValue="minutes">
              <Select options={WINDOW_UNIT_OPTIONS} style={{ width: 120 }} />
            </Form.Item>
          </Space>

          <Form.Item name="notification_channels" label="通知渠道">
            <Select mode="multiple" options={CHANNEL_OPTIONS} placeholder="选择通知渠道" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} maxLength={500} placeholder="可选描述" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

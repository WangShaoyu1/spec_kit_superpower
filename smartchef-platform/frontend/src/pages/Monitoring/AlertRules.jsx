import { useEffect, useState } from 'react';
import {
  Card, Table, Button, Space, Modal, Form, Input, Select, InputNumber, Switch, Tag,
  Popconfirm, message, Typography,
} from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { Text } = Typography;

const METRIC_OPTIONS = [
  { label: '准确率 (accuracy)', value: 'accuracy' },
  { label: 'P95 延迟 (p95_latency)', value: 'p95_latency' },
  { label: 'P99 延迟 (p99_latency)', value: 'p99_latency' },
  { label: '错误率 (error_rate)', value: 'error_rate' },
];

const OPERATOR_OPTIONS = [
  { label: '大于 (>)', value: 'gt' },
  { label: '大于等于 (>=)', value: 'gte' },
  { label: '小于 (<)', value: 'lt' },
  { label: '小于等于 (<=)', value: 'lte' },
];

const OPERATOR_LABELS = { gt: '>', gte: '>=', lt: '<', lte: '<=' };

const NOTIFICATION_OPTIONS = [
  { label: '日志记录', value: 'log' },
  { label: '邮件通知', value: 'email' },
  { label: 'Webhook', value: 'webhook' },
];

export default function AlertRules() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  const fetchRules = async () => {
    setLoading(true);
    try {
      const res = await api.get('/monitoring/alerts');
      setRules(res.data);
    } catch {
      message.error('加载告警规则失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRules(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      await api.post('/monitoring/alerts', {
        name: values.name,
        metric_name: values.metric_name,
        operator: values.operator,
        threshold: values.threshold,
        duration_minutes: values.duration_minutes,
        notification_config: { channels: values.channels || ['log'] },
        is_enabled: true,
      });
      message.success('告警规则创建成功');
      setModalVisible(false);
      form.resetFields();
      fetchRules();
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '创建失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggle = async (record, checked) => {
    try {
      await api.patch(`/monitoring/alerts/${record.id}`, { is_enabled: checked });
      message.success(checked ? '已启用' : '已禁用');
      fetchRules();
    } catch {
      message.error('操作失败');
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/monitoring/alerts/${id}`);
      message.success('删除成功');
      fetchRules();
    } catch {
      message.error('删除失败');
    }
  };

  const columns = [
    { title: '规则名称', dataIndex: 'name', ellipsis: true },
    {
      title: '条件',
      key: 'condition',
      render: (_, r) => (
        <Text code>
          {r.metric_name} {OPERATOR_LABELS[r.operator] || r.operator} {r.threshold}
        </Text>
      ),
    },
    {
      title: '持续时间',
      dataIndex: 'duration_minutes',
      width: 100,
      render: (v) => `${v} 分钟`,
    },
    {
      title: '状态',
      dataIndex: 'is_enabled',
      width: 80,
      render: (v, r) => (
        <Switch size="small" checked={v} onChange={(checked) => handleToggle(r, checked)} />
      ),
    },
    {
      title: '启用标签',
      dataIndex: 'is_enabled',
      width: 80,
      render: (v) => <Tag color={v ? 'green' : 'default'}>{v ? '启用' : '禁用'}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, r) => (
        <Popconfirm title="确认删除该告警规则？" onConfirm={() => handleDelete(r.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => { form.resetFields(); setModalVisible(true); }}
        >
          新建规则
        </Button>
      </div>

      <Card size="small">
        <Table
          rowKey="id"
          columns={columns}
          dataSource={rules}
          loading={loading}
          size="small"
          pagination={false}
        />
      </Card>

      {/* 创建告警规则表单 */}
      <Modal
        title="新建告警规则"
        open={modalVisible}
        onOk={handleCreate}
        onCancel={() => setModalVisible(false)}
        confirmLoading={submitting}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="规则名称" rules={[{ required: true, message: '请输入规则名称' }]}>
            <Input placeholder="例：P95 延迟超标告警" />
          </Form.Item>
          <Form.Item name="metric_name" label="监控指标" rules={[{ required: true, message: '请选择指标' }]}>
            <Select options={METRIC_OPTIONS} placeholder="选择指标" />
          </Form.Item>
          <Space style={{ width: '100%' }} size="middle">
            <Form.Item name="operator" label="运算符" rules={[{ required: true, message: '请选择运算符' }]}>
              <Select options={OPERATOR_OPTIONS} placeholder="运算符" style={{ width: 150 }} />
            </Form.Item>
            <Form.Item name="threshold" label="阈值" rules={[{ required: true, message: '请输入阈值' }]}>
              <InputNumber placeholder="阈值" style={{ width: 150 }} step={0.01} />
            </Form.Item>
          </Space>
          <Form.Item
            name="duration_minutes"
            label="持续时间（分钟）"
            rules={[{ required: true, message: '请输入持续时间' }]}
            initialValue={5}
          >
            <InputNumber min={1} max={1440} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="channels" label="通知方式" initialValue={['log']}>
            <Select mode="multiple" options={NOTIFICATION_OPTIONS} placeholder="选择通知方式" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

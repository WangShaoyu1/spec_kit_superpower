import { useEffect, useState } from 'react';
import {
  Table, Button, Space, Tag, Input, Select, Modal, Form, message, Typography, Popconfirm, Card,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import api from '../../services/api';
import SlotEditor from './SlotEditor';
import TrainingDataEditor from './TrainingDataEditor';

const { Title } = Typography;

export default function IntentManager() {
  const [intents, setIntents] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingIntent, setEditingIntent] = useState(null);
  const [detailIntent, setDetailIntent] = useState(null);
  const [detailTab, setDetailTab] = useState('slots');
  const [form] = Form.useForm();

  const fetchIntents = async () => {
    setLoading(true);
    try {
      const params = {};
      if (categoryFilter) params.category = categoryFilter;
      const res = await api.get('/intents', { params });
      setIntents(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchIntents(); }, [categoryFilter]);

  const openCreate = () => {
    setEditingIntent(null);
    form.resetFields();
    setModalVisible(true);
  };

  const openEdit = (intent) => {
    setEditingIntent(intent);
    form.setFieldsValue(intent);
    setModalVisible(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editingIntent) {
        await api.patch(`/intents/${editingIntent.id}`, values);
        message.success('更新成功');
      } else {
        await api.post('/intents', values);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchIntents();
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '操作失败');
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/intents/${id}`);
      message.success('删除成功');
      fetchIntents();
    } catch (err) {
      message.error('删除失败');
    }
  };

  const columns = [
    { title: '意图标识', dataIndex: 'intent_key', key: 'intent_key', ellipsis: true },
    { title: '中文名称', dataIndex: 'display_name', key: 'display_name' },
    {
      title: '分类', dataIndex: 'category', key: 'category',
      render: (v) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: '槽位数', key: 'slots',
      render: (_, r) => r.slots?.length || 0,
    },
    { title: '训练数据', dataIndex: 'training_data_count', key: 'td_count' },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active',
      render: (v) => <Tag color={v ? 'green' : 'default'}>{v ? '启用' : '停用'}</Tag>,
    },
    {
      title: '操作', key: 'action', width: 200,
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => { setDetailIntent(record); setDetailTab('slots'); }}>
            详情
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const categories = [...new Set(intents.map((i) => i.category))];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>指令配置管理</Title>
        <Space>
          <Select
            allowClear placeholder="按分类筛选" style={{ width: 160 }}
            value={categoryFilter} onChange={setCategoryFilter}
            options={categories.map((c) => ({ label: c, value: c }))}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建意图</Button>
        </Space>
      </div>

      <Table
        rowKey="id" columns={columns} dataSource={intents}
        loading={loading} pagination={{ total, pageSize: 50 }}
      />

      <Modal
        title={editingIntent ? '编辑意图' : '新建意图'}
        open={modalVisible} onOk={handleSave} onCancel={() => setModalVisible(false)}
        width={560}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="intent_key" label="意图标识" rules={[{ required: true }]}
            extra="唯一标识，如 voice_cmd_start_cooking"
          >
            <Input disabled={!!editingIntent} />
          </Form.Item>
          <Form.Item name="display_name" label="中文名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="category" label="分类" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`${detailIntent?.display_name} - 详情`}
        open={!!detailIntent}
        onCancel={() => setDetailIntent(null)}
        footer={null} width={800}
      >
        {detailIntent && (
          <Card
            tabList={[
              { key: 'slots', tab: '槽位定义' },
              { key: 'training', tab: '训练数据' },
            ]}
            activeTabKey={detailTab}
            onTabChange={setDetailTab}
          >
            {detailTab === 'slots' && (
              <SlotEditor intentId={detailIntent.id} onUpdate={fetchIntents} />
            )}
            {detailTab === 'training' && (
              <TrainingDataEditor intentId={detailIntent.id} />
            )}
          </Card>
        )}
      </Modal>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { Table, Button, Form, Input, Select, Switch, InputNumber, Modal, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import api from '../../services/api';

const ENTITY_TYPES = [
  { label: '数字', value: 'number' },
  { label: '时间', value: 'time' },
  { label: '食物名称', value: 'food_name' },
  { label: '枚举', value: 'enum' },
  { label: '自由文本', value: 'free_text' },
];

export default function SlotEditor({ intentId, onUpdate }) {
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  const fetchSlots = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/intents/${intentId}`);
      setSlots(res.data.slots || []);
    } catch {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSlots(); }, [intentId]);

  const handleAdd = async () => {
    try {
      const values = await form.validateFields();
      await api.post(`/intents/${intentId}/slots`, values);
      message.success('添加成功');
      setModalVisible(false);
      form.resetFields();
      fetchSlots();
      onUpdate?.();
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '添加失败');
    }
  };

  const handleDelete = async (slotId) => {
    await api.delete(`/intents/slots/${slotId}`);
    message.success('删除成功');
    fetchSlots();
    onUpdate?.();
  };

  const columns = [
    { title: '标识', dataIndex: 'slot_key' },
    { title: '名称', dataIndex: 'display_name' },
    { title: '类型', dataIndex: 'entity_type' },
    { title: '必填', dataIndex: 'is_required', render: (v) => (v ? '是' : '否') },
    { title: '追问提示', dataIndex: 'prompt_text', ellipsis: true },
    {
      title: '操作', key: 'action', width: 80,
      render: (_, r) => (
        <Popconfirm title="确认删除？" onConfirm={() => handleDelete(r.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <Button icon={<PlusOutlined />} onClick={() => { form.resetFields(); setModalVisible(true); }}>
          添加槽位
        </Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={slots} loading={loading} pagination={false} size="small" />
      <Modal title="添加槽位" open={modalVisible} onOk={handleAdd} onCancel={() => setModalVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="slot_key" label="槽位标识" rules={[{ required: true }]}>
            <Input placeholder="如 duration" />
          </Form.Item>
          <Form.Item name="display_name" label="中文名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="entity_type" label="实体类型" rules={[{ required: true }]}>
            <Select options={ENTITY_TYPES} />
          </Form.Item>
          <Form.Item name="is_required" label="是否必填" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="prompt_text" label="追问提示">
            <Input.TextArea rows={2} placeholder="请问您要加热多长时间？" />
          </Form.Item>
          <Form.Item name="sort_order" label="排序" initialValue={0}>
            <InputNumber min={0} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

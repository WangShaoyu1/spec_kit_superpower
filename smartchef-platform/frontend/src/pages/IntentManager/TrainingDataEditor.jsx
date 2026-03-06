import { useEffect, useState } from 'react';
import { Table, Button, Input, Tag, message, Popconfirm, Space, Form, Modal } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import api from '../../services/api';

export default function TrainingDataEditor({ intentId }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [batchText, setBatchText] = useState('');
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/intents/${intentId}/training-data`);
      setData(res.data);
    } catch {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [intentId]);

  const handleAddSingle = async () => {
    try {
      const values = await form.validateFields();
      await api.post(`/intents/${intentId}/training-data`, values);
      message.success('添加成功');
      form.resetFields();
      fetchData();
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '添加失败');
    }
  };

  const handleBatchAdd = async () => {
    const lines = batchText.split('\n').map((l) => l.trim()).filter(Boolean);
    if (lines.length === 0) return message.warning('请输入训练数据');
    try {
      await api.post(
        `/intents/${intentId}/training-data/batch`,
        lines.map((text) => ({ text, language: 'zh' })),
      );
      message.success(`成功添加 ${lines.length} 条`);
      setModalVisible(false);
      setBatchText('');
      fetchData();
    } catch {
      message.error('批量添加失败');
    }
  };

  const handleDelete = async (id) => {
    await api.delete(`/intents/training-data/${id}`);
    message.success('删除成功');
    fetchData();
  };

  const columns = [
    { title: '语句', dataIndex: 'text', ellipsis: true },
    {
      title: '语言', dataIndex: 'language', width: 80,
      render: (v) => <Tag>{v === 'zh' ? '中文' : '英文'}</Tag>,
    },
    {
      title: '自动翻译', dataIndex: 'is_auto_translated', width: 90,
      render: (v) => (v ? <Tag color="orange">是</Tag> : null),
    },
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
      <Space style={{ marginBottom: 12 }}>
        <Form form={form} layout="inline">
          <Form.Item name="text" rules={[{ required: true, message: '请输入' }]}>
            <Input placeholder="输入训练语句" style={{ width: 300 }} />
          </Form.Item>
          <Form.Item>
            <Button icon={<PlusOutlined />} onClick={handleAddSingle}>添加</Button>
          </Form.Item>
        </Form>
        <Button onClick={() => setModalVisible(true)}>批量添加</Button>
      </Space>

      <Table rowKey="id" columns={columns} dataSource={data} loading={loading} size="small"
        pagination={{ pageSize: 20 }}
      />

      <Modal title="批量添加训练数据" open={modalVisible}
        onOk={handleBatchAdd} onCancel={() => setModalVisible(false)} width={600}
      >
        <p style={{ color: '#888' }}>每行一条训练语句：</p>
        <Input.TextArea
          rows={10} value={batchText} onChange={(e) => setBatchText(e.target.value)}
          placeholder="帮我设置温度到180度&#10;调高温度&#10;把温度调到200"
        />
      </Modal>
    </div>
  );
}

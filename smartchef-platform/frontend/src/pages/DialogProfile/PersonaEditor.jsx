import { useState } from 'react';
import { Modal, Table, Button, Form, Input, Space, message, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import api from '../../services/api';

export default function PersonaEditor({ visible, onClose, personas, onUpdate }) {
  const [createVisible, setCreateVisible] = useState(false);
  const [form] = Form.useForm();

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await api.post('/profiles/personas', values);
      message.success('创建成功');
      setCreateVisible(false);
      form.resetFields();
      onUpdate?.();
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '创建失败');
    }
  };

  const handleDelete = async (id) => {
    await api.delete(`/profiles/personas/${id}`);
    message.success('删除成功');
    onUpdate?.();
  };

  const columns = [
    { title: '名称', dataIndex: 'name', width: 100 },
    { title: '性格', dataIndex: 'personality', ellipsis: true },
    { title: '语气', dataIndex: 'tone_style', ellipsis: true },
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
    <Modal title="闲聊人设管理" open={visible} onCancel={onClose} footer={null} width={700}>
      <Button icon={<PlusOutlined />} onClick={() => { form.resetFields(); setCreateVisible(true); }}
        style={{ marginBottom: 12 }}
      >
        新建人设
      </Button>
      <Table rowKey="id" columns={columns} dataSource={personas} pagination={false} size="small" />

      <Modal title="新建人设" open={createVisible} onOk={handleCreate} onCancel={() => setCreateVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="助手名称" rules={[{ required: true }]}>
            <Input placeholder="如：小厨" />
          </Form.Item>
          <Form.Item name="personality" label="性格特征" rules={[{ required: true }]}>
            <Input.TextArea rows={2} placeholder="活泼友好、专业可靠、幽默风趣..." />
          </Form.Item>
          <Form.Item name="tone_style" label="语气风格" rules={[{ required: true }]}>
            <Input.TextArea rows={2} placeholder="亲切随和、简洁专业..." />
          </Form.Item>
          <Form.Item name="system_prompt" label="系统提示词" rules={[{ required: true }]}>
            <Input.TextArea rows={4} placeholder="你是一个友好的厨房助手..." />
          </Form.Item>
        </Form>
      </Modal>
    </Modal>
  );
}

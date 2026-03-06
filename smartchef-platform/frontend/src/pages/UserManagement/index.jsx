import { useEffect, useState } from 'react';
import { Table, Button, Tag, Typography, Space, Modal, Form, Input, Select, message } from 'antd';
import { PlusOutlined, UserOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { Title } = Typography;

export default function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [createVisible, setCreateVisible] = useState(false);
  const [form] = Form.useForm();

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await api.get('/auth/users');
      setUsers(res.data);
    } catch { message.error('加载用户失败'); }
    finally { setLoading(false); }
  };

  const fetchRoles = async () => {
    try {
      const res = await api.get('/auth/roles');
      setRoles(res.data);
    } catch { /* */ }
  };

  useEffect(() => { fetchUsers(); fetchRoles(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await api.post('/auth/users', values);
      message.success('创建成功');
      setCreateVisible(false);
      form.resetFields();
      fetchUsers();
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '创建失败');
    }
  };

  const columns = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '显示名', dataIndex: 'display_name', key: 'name' },
    {
      title: '角色', dataIndex: 'role', key: 'role',
      render: (r) => r ? <Tag color="blue">{r.name}</Tag> : <Tag>无</Tag>,
    },
    {
      title: '状态', dataIndex: 'is_active', key: 'active',
      render: (v) => v ? <Tag color="green">活跃</Tag> : <Tag color="red">禁用</Tag>,
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>用户管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setCreateVisible(true); }}>
          添加用户
        </Button>
      </div>

      <Table rowKey="id" columns={columns} dataSource={users} loading={loading} pagination={false} />

      <Modal title="添加用户" open={createVisible} onOk={handleCreate} onCancel={() => setCreateVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}><Input.Password /></Form.Item>
          <Form.Item name="display_name" label="显示名"><Input /></Form.Item>
          <Form.Item name="role_id" label="角色" rules={[{ required: true }]}>
            <Select placeholder="选择角色"
              options={roles.map(r => ({ label: r.name, value: r.id }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

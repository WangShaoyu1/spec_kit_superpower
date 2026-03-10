import { useEffect, useState, useCallback } from 'react';
import {
  Table, Button, Space, Tag, Input, Select, Modal, Form, message,
  Typography, Popconfirm, Switch, Tabs,
} from 'antd';
import {
  PlusOutlined, EditOutlined, SearchOutlined, UserOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons';
import api from '../../services/api';
import RoleEditor from './RoleEditor';

const { Title } = Typography;

export default function UserManagerPage() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [searchText, setSearchText] = useState('');
  const [roleFilter, setRoleFilter] = useState(null);
  const [form] = Form.useForm();

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/auth/users');
      setUsers(res.data);
    } catch {
      message.error('加载用户列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchRoles = useCallback(async () => {
    try {
      const res = await api.get('/auth/roles');
      setRoles(res.data);
    } catch { /* 静默失败 */ }
  }, []);

  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, [fetchUsers, fetchRoles]);

  // 创建用户
  const openCreate = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 编辑用户
  const openEdit = (user) => {
    setEditingUser(user);
    form.setFieldsValue({
      display_name: user.display_name,
      role_id: user.role_id,
    });
    setModalVisible(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editingUser) {
        await api.patch(`/auth/users/${editingUser.id}`, {
          display_name: values.display_name,
          role_id: values.role_id,
        });
        message.success('更新成功');
      } else {
        await api.post('/auth/users', values);
        message.success('创建成功');
      }
      setModalVisible(false);
      form.resetFields();
      fetchUsers();
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '操作失败');
    }
  };

  // 切换启用/禁用
  const handleToggleActive = async (user) => {
    try {
      await api.patch(`/auth/users/${user.id}`, { is_active: !user.is_active });
      message.success(user.is_active ? '已禁用' : '已启用');
      fetchUsers();
    } catch {
      message.error('操作失败');
    }
  };

  // 筛选后的用户列表
  const filteredUsers = users.filter((u) => {
    const matchText =
      !searchText ||
      u.username.toLowerCase().includes(searchText.toLowerCase()) ||
      (u.display_name || '').toLowerCase().includes(searchText.toLowerCase());
    const matchRole = !roleFilter || u.role_id === roleFilter;
    return matchText && matchRole;
  });

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      sorter: (a, b) => a.username.localeCompare(b.username),
    },
    {
      title: '显示名',
      dataIndex: 'display_name',
      key: 'display_name',
    },
    {
      title: '角色',
      dataIndex: 'role_name',
      key: 'role_name',
      render: (v) => v ? <Tag color="blue">{v}</Tag> : <Tag>未分配</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v, record) => (
        <Popconfirm
          title={v ? '确认禁用此用户？' : '确认启用此用户？'}
          onConfirm={() => handleToggleActive(record)}
        >
          <Switch checked={v} size="small" checkedChildren="活跃" unCheckedChildren="禁用" />
        </Popconfirm>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v) => v ? new Date(v).toLocaleString('zh-CN') : '-',
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)}>
          编辑
        </Button>
      ),
    },
  ];

  const userTab = (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Space>
          <Input
            placeholder="搜索用户名/显示名"
            prefix={<SearchOutlined />}
            allowClear
            style={{ width: 240 }}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
          <Select
            allowClear
            placeholder="按角色筛选"
            style={{ width: 160 }}
            value={roleFilter}
            onChange={setRoleFilter}
            options={roles.map((r) => ({ label: r.name, value: r.id }))}
          />
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          添加用户
        </Button>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={filteredUsers}
        loading={loading}
        pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 个用户` }}
      />

      <Modal
        title={editingUser ? '编辑用户' : '添加用户'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        destroyOnClose
        width={480}
      >
        <Form form={form} layout="vertical">
          {!editingUser && (
            <>
              <Form.Item
                name="username"
                label="用户名"
                rules={[{ required: true, message: '请输入用户名' }, { min: 2, message: '至少 2 个字符' }]}
              >
                <Input placeholder="唯一登录名" />
              </Form.Item>
              <Form.Item
                name="password"
                label="密码"
                rules={[{ required: true, message: '请输入密码' }, { min: 6, message: '至少 6 个字符' }]}
              >
                <Input.Password placeholder="至少 6 位" />
              </Form.Item>
            </>
          )}
          <Form.Item
            name="display_name"
            label="显示名"
            rules={[{ required: !editingUser, message: '请输入显示名' }]}
          >
            <Input placeholder="用户昵称" />
          </Form.Item>
          <Form.Item
            name="role_id"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select
              placeholder="选择角色"
              options={roles.map((r) => ({ label: r.name, value: r.id }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );

  const tabItems = [
    {
      key: 'users',
      label: (
        <span><UserOutlined /> 用户列表</span>
      ),
      children: userTab,
    },
    {
      key: 'roles',
      label: (
        <span><SafetyCertificateOutlined /> 角色管理</span>
      ),
      children: <RoleEditor roles={roles} onRolesChange={fetchRoles} />,
    },
  ];

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>用户与角色管理</Title>
      <Tabs items={tabItems} />
    </div>
  );
}

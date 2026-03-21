import { useEffect, useState, useCallback, useMemo } from 'react';
import {
  Typography,
  Button,
  Input,
  Select,
  Table,
  Tag,
  Card,
  Row,
  Col,
  Tabs,
  Space,
  Modal,
  Form,
  Switch,
  message,
  Popconfirm,
  Alert,
  Collapse,
  List,
  Badge,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  LockOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
  UserOutlined,
  BugOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import useUserStore from '../../stores/userStore';
import RoleEditor from './RoleEditor';
import { PermissionSummaryMatrix } from './PermissionMatrix';

const { Title, Text } = Typography;

const DEFAULT_RESET_PASSWORD = 'Abc12345';

/** Top border / theme accent for role cards and tag styling */
function getRoleAccentVar(role) {
  const n = (role?.name || '').toLowerCase();
  if (n.includes('系统管理') || n.includes('admin') || role?.name === '系统管理员') {
    return 'var(--role-admin-accent, #ff4d4f)';
  }
  if (n.includes('产品') || n === 'pm' || n.includes('产品经理')) {
    return 'var(--role-pm-accent, #1677ff)';
  }
  if (n.includes('测试') || n.includes('test') || n.includes('工程师')) {
    return 'var(--role-tester-accent, #52c41a)';
  }
  return 'var(--color-border, #e5e6eb)';
}

function getUserRoleTagProps(role) {
  const n = (role?.name || '').toLowerCase();
  if (n.includes('系统管理') || n.includes('admin') || role?.name === '系统管理员') {
    return {
      style: {
        color: 'var(--role-admin-accent, #ff4d4f)',
        borderColor: 'var(--role-admin-accent, #ff4d4f)',
        background: 'rgba(255, 77, 79, 0.09)',
      },
    };
  }
  if (n.includes('产品') || n === 'pm' || n.includes('产品经理')) {
    return {
      style: {
        color: 'var(--role-pm-accent, #1677ff)',
        borderColor: 'var(--role-pm-accent, #1677ff)',
        background: 'rgba(22, 119, 255, 0.09)',
      },
    };
  }
  if (n.includes('测试') || n.includes('test') || n.includes('工程师')) {
    return {
      style: {
        color: 'var(--role-tester-accent, #52c41a)',
        borderColor: 'var(--role-tester-accent, #52c41a)',
        background: 'rgba(82, 196, 26, 0.09)',
      },
    };
  }
  return { color: 'default' };
}

const STATUS_MAP = {
  active: { color: 'success', label: '正常' },
  disabled: { color: 'error', label: '已禁用' },
};

const USER_STAT_CARDS = [
  {
    key: 'total',
    label: '总账号',
    icon: <TeamOutlined />,
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    getValue: (s) => s.totalCount,
  },
  {
    key: 'admin',
    label: '管理员',
    icon: <SafetyCertificateOutlined />,
    gradient: 'linear-gradient(135deg, #1677ff 0%, #69b1ff 100%)',
    getValue: (s) => s.adminCount,
  },
  {
    key: 'pm',
    label: '产品经理',
    icon: <UserOutlined />,
    gradient: 'linear-gradient(135deg, #52c41a 0%, #95de64 100%)',
    getValue: (s) => s.pmCount,
  },
  {
    key: 'tester',
    label: '测试人员',
    icon: <BugOutlined />,
    gradient: 'linear-gradient(135deg, #faad14 0%, #ffc53d 100%)',
    getValue: (s) => s.testerCount,
  },
];

function UsersTab() {
  const [form] = Form.useForm();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [submitLoading, setSubmitLoading] = useState(false);

  const {
    users,
    usersLoading,
    usersTotal,
    usersPage,
    usersPageSize,
    usersSearch,
    usersStatus,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    resetPassword,
    setUsersSearch,
    setUsersStatus,
    setUsersPage,
    setUsersPageSize,
    roles,
    fetchRoles,
  } = useUserStore();

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers, usersPage, usersPageSize, usersSearch, usersStatus]);

  useEffect(() => {
    if (roles.length === 0) fetchRoles();
  }, [fetchRoles, roles.length]);

  const userStats = useMemo(() => {
    const roleName = (u) => (u.role?.name || u.role_name || '').toLowerCase();
    return {
      totalCount: usersTotal,
      adminCount: users.filter((u) => roleName(u).includes('admin') || roleName(u) === '管理员').length,
      pmCount: users.filter((u) => roleName(u).includes('product') || roleName(u).includes('pm') || roleName(u) === '产品经理').length,
      testerCount: users.filter((u) => roleName(u).includes('test') || roleName(u) === '测试人员').length,
    };
  }, [users, usersTotal]);

  const openCreate = useCallback(() => {
    setEditingUser(null);
    form.resetFields();
    setModalOpen(true);
  }, [form]);

  const openEdit = useCallback(
    (record) => {
      setEditingUser(record);
      form.setFieldsValue({
        username: record.username,
        name: record.name,
        role_id: record.role?.id,
      });
      setModalOpen(true);
    },
    [form],
  );

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      if (editingUser) {
        await updateUser(editingUser.id, { name: values.name });
        if (values.role_id && values.role_id !== editingUser.role?.id) {
          const { assignRole } = useUserStore.getState();
          await assignRole(editingUser.id, values.role_id);
        }
        message.success('更新成功');
      } else {
        await createUser(values);
        message.success('创建成功');
      }
      setModalOpen(false);
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '操作失败');
    } finally {
      setSubmitLoading(false);
    }
  }, [form, editingUser, createUser, updateUser]);

  const handleToggleStatus = useCallback(
    async (record) => {
      const newStatus = record.status === 'active' ? 'disabled' : 'active';
      try {
        await updateUser(record.id, { status: newStatus });
        message.success(newStatus === 'active' ? '已启用' : '已禁用');
      } catch (err) {
        message.error(err?.message || '操作失败');
      }
    },
    [updateUser],
  );

  const handleDelete = useCallback(
    async (record) => {
      try {
        await deleteUser(record.id);
        message.success('已删除');
      } catch (err) {
        message.error(err?.message || '删除失败');
      }
    },
    [deleteUser],
  );

  const handleResetPwdConfirm = useCallback(
    async (record) => {
      try {
        await resetPassword(record.id, DEFAULT_RESET_PASSWORD);
        message.success('密码已重置');
      } catch (err) {
        message.error(err?.message || '操作失败');
      }
    },
    [resetPassword],
  );

  const columns = useMemo(
    () => [
      {
        title: '用户名',
        dataIndex: 'username',
        key: 'username',
        width: 140,
        render: (text, record) => (
          <Space size={4}>
            <Text strong>{text}</Text>
            {record.is_builtin && (
              <Tag color="gold" style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px' }}>
                内置
              </Tag>
            )}
          </Space>
        ),
      },
      {
        title: '姓名',
        dataIndex: 'name',
        key: 'name',
        width: 120,
      },
      {
        title: '角色',
        dataIndex: 'role',
        key: 'role',
        width: 120,
        render: (role) =>
          role ? (
            <Tag icon={<SafetyCertificateOutlined />} {...getUserRoleTagProps(role)}>
              {role.name}
            </Tag>
          ) : (
            '-'
          ),
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 90,
        render: (status) => {
          const info = STATUS_MAP[status] || { color: 'default', label: status };
          return <Tag color={info.color}>{info.label}</Tag>;
        },
      },
      {
        title: '最后登录',
        dataIndex: 'last_login_at',
        key: 'last_login_at',
        width: 170,
        render: (val) => (
          <Text type="secondary" style={{ fontSize: 'var(--font-size-xs, 12px)' }}>
            {val ? dayjs(val).format('YYYY-MM-DD HH:mm') : '从未登录'}
          </Text>
        ),
      },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 170,
        render: (val) => (
          <Text type="secondary" style={{ fontSize: 'var(--font-size-xs, 12px)' }}>
            {val ? dayjs(val).format('YYYY-MM-DD HH:mm') : '-'}
          </Text>
        ),
      },
      {
        title: '操作',
        key: 'actions',
        width: 260,
        render: (_, record) => (
          <Space size={4}>
            <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(record)}>
              编辑
            </Button>
            <Switch
              size="small"
              checked={record.status === 'active'}
              checkedChildren="启用"
              unCheckedChildren="禁用"
              onChange={() => handleToggleStatus(record)}
              disabled={record.is_builtin}
            />
            <Popconfirm
              title="重置密码"
              description={`确定要重置该用户的密码为默认密码 '${DEFAULT_RESET_PASSWORD}' 吗？`}
              onConfirm={() => handleResetPwdConfirm(record)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" size="small" icon={<LockOutlined />}>
                重置密码
              </Button>
            </Popconfirm>
            <Popconfirm
              title="确定删除该用户？"
              description="仅可删除已禁用的用户"
              onConfirm={() => handleDelete(record)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
                disabled={record.is_builtin || record.status === 'active'}
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [openEdit, handleToggleStatus, handleDelete, handleResetPwdConfirm],
  );

  return (
    <>
      <div style={{ padding: '16px 24px' }}>
        <Row gutter={16}>
          {USER_STAT_CARDS.map((card) => (
            <Col span={6} key={card.key}>
              <Card
                style={{
                  borderRadius: 'var(--radius-lg, 12px)',
                  border: 'none',
                  overflow: 'hidden',
                  minWidth: 160,
                }}
                styles={{ body: { padding: '16px 20px' } }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: 'var(--radius-lg, 12px)',
                      background: card.gradient,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 20,
                      color: '#fff',
                      flexShrink: 0,
                      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    }}
                  >
                    {card.icon}
                  </div>
                  <div>
                    <Text type="secondary" style={{ fontSize: 'var(--font-size-xs, 12px)', display: 'block' }}>
                      {card.label}
                    </Text>
                    <Text
                      strong
                      style={{
                        fontSize: 'var(--font-size-2xl, 24px)',
                        fontFamily: 'var(--font-mono, monospace)',
                        lineHeight: 1.2,
                      }}
                    >
                      {card.getValue(userStats)}
                    </Text>
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
      <div
        style={{
          padding: '16px 24px',
          display: 'flex',
          gap: 12,
          borderBottom: '1px solid var(--color-border-light, #f0f0f0)',
          alignItems: 'center',
        }}
      >
        <Input
          placeholder="搜索用户名或姓名..."
          prefix={<SearchOutlined style={{ color: 'var(--color-text-tertiary, #bfbfbf)' }} />}
          allowClear
          style={{ width: 280 }}
          value={usersSearch}
          onChange={(e) => setUsersSearch(e.target.value)}
        />
        <Select
          value={usersStatus}
          onChange={setUsersStatus}
          options={[
            { value: '', label: '全部状态' },
            { value: 'active', label: '正常' },
            { value: 'disabled', label: '已禁用' },
          ]}
          style={{ width: 130 }}
        />
        <div style={{ flex: 1 }} />
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          新建用户
        </Button>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={users}
        loading={usersLoading}
        tableLayout="fixed"
        scroll={{ x: 1150 }}
        pagination={{
          current: usersPage,
          pageSize: usersPageSize,
          total: usersTotal,
          showSizeChanger: true,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p, ps) => {
            setUsersPage(p);
            if (ps !== usersPageSize) setUsersPageSize(ps);
          },
          style: { padding: '0 24px 16px' },
        }}
      />

      {/* Create/Edit user modal */}
      <Modal
        open={modalOpen}
        title={editingUser ? '编辑用户' : '新建用户'}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        confirmLoading={submitLoading}
        okText={editingUser ? '保存' : '创建'}
        cancelText="取消"
        width={480}
        centered
        destroyOnHidden
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { pattern: /^[a-zA-Z][a-zA-Z0-9_]{2,19}$/, message: '3-20位，字母开头，仅字母数字下划线' },
            ]}
          >
            <Input placeholder="登录用户名" disabled={!!editingUser} />
          </Form.Item>
          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="显示名称" maxLength={50} />
          </Form.Item>
          {!editingUser && (
            <Form.Item
              name="password"
              label="密码"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 8, message: '至少 8 位' },
                { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '需包含字母和数字' },
              ]}
            >
              <Input.Password placeholder="至少8位，包含字母和数字" />
            </Form.Item>
          )}
          <Form.Item
            name="role_id"
            label="角色"
            rules={[{ required: !editingUser, message: '请选择角色' }]}
          >
            <Select placeholder="选择角色">
              {roles.map((r) => (
                <Select.Option key={r.id} value={r.id}>
                  {r.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}

function RolesTab() {
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [focusPermissions, setFocusPermissions] = useState(false);
  const [rolePermMap, setRolePermMap] = useState({});
  const [permFetchLoading, setPermFetchLoading] = useState(false);

  const {
    roles,
    rolesLoading,
    fetchRoles,
    deleteRole,
    permissionModules,
    fetchPermissions,
    getRolePermissions,
  } = useUserStore();

  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);

  useEffect(() => {
    if (permissionModules.length === 0) fetchPermissions();
  }, [fetchPermissions, permissionModules.length]);

  useEffect(() => {
    if (roles.length === 0) {
      setRolePermMap({});
      return;
    }
    let cancelled = false;
    (async () => {
      setPermFetchLoading(true);
      try {
        const entries = await Promise.all(
          roles.map(async (r) => {
            try {
              const keys = await getRolePermissions(r.id);
              const list = Array.isArray(keys) ? keys : [];
              return [r.id, list];
            } catch {
              return [r.id, []];
            }
          }),
        );
        if (!cancelled) setRolePermMap(Object.fromEntries(entries));
      } finally {
        if (!cancelled) setPermFetchLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [roles, getRolePermissions]);

  const keyToLabel = useMemo(() => {
    const m = new Map();
    for (const mod of permissionModules) {
      for (const p of mod.permissions || []) {
        m.set(p.key, p.label);
      }
    }
    return m;
  }, [permissionModules]);

  const closeEditor = useCallback(() => {
    setEditorOpen(false);
    setEditingRole(null);
    setFocusPermissions(false);
  }, []);

  const openCreate = useCallback(() => {
    setEditingRole(null);
    setFocusPermissions(false);
    setEditorOpen(true);
  }, []);

  const openEdit = useCallback((record) => {
    setEditingRole(record);
    setFocusPermissions(false);
    setEditorOpen(true);
  }, []);

  const openPermissions = useCallback((record) => {
    setEditingRole(record);
    setFocusPermissions(true);
    setEditorOpen(true);
  }, []);

  const handleDelete = useCallback(
    async (record) => {
      try {
        await deleteRole(record.id);
        message.success('角色已删除');
      } catch (err) {
        message.error(err?.message || '删除失败');
      }
    },
    [deleteRole],
  );

  const columns = useMemo(
    () => [
      {
        title: '角色名称',
        dataIndex: 'name',
        key: 'name',
        render: (text, record) => (
          <Space size={4}>
            <Text strong>{text}</Text>
            {record.is_builtin && (
              <Tag color="gold" style={{ fontSize: 10, lineHeight: '16px', padding: '0 4px' }}>
                内置
              </Tag>
            )}
          </Space>
        ),
      },
      {
        title: '描述',
        dataIndex: 'description',
        key: 'description',
        ellipsis: true,
        render: (text) => text || <Text type="secondary">-</Text>,
      },
      {
        title: '用户数',
        dataIndex: 'user_count',
        key: 'user_count',
        width: 90,
        align: 'center',
        render: (v) => (
          <Text style={{ fontFamily: 'var(--font-mono, monospace)', fontWeight: 600 }}>
            {v ?? 0}
          </Text>
        ),
      },
      {
        title: '权限数',
        dataIndex: 'permission_count',
        key: 'permission_count',
        width: 90,
        align: 'center',
        render: (v) => (
          <Text style={{ fontFamily: 'var(--font-mono, monospace)', fontWeight: 600 }}>
            {v ?? 0}
          </Text>
        ),
      },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 170,
        render: (val) => (
          <Text type="secondary" style={{ fontSize: 'var(--font-size-xs, 12px)' }}>
            {val ? dayjs(val).format('YYYY-MM-DD HH:mm') : '-'}
          </Text>
        ),
      },
      {
        title: '操作',
        key: 'actions',
        width: 160,
        render: (_, record) => (
          <Space size={4}>
            <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(record)}>
              编辑
            </Button>
            <Button
              type="link"
              size="small"
              icon={<SafetyCertificateOutlined />}
              onClick={() => openPermissions(record)}
            >
              权限管理
            </Button>
            <Popconfirm
              title="确定删除该角色？"
              description="角色下不可有用户"
              onConfirm={() => handleDelete(record)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
                disabled={record.is_builtin || (record.user_count ?? 0) > 0}
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [openEdit, openPermissions, handleDelete],
  );

  const roleCardStyle = {
    borderRadius: 'var(--radius-xl, 12px)',
    boxShadow: 'var(--role-card-shadow, 0 1px 4px rgba(0,0,0,0.06))',
    borderTop: '3px solid',
  };

  return (
    <>
      <Alert
        message="权限说明"
        description="权限校验以能力点为准，不绑定角色名。角色是能力点的预设组合。"
        type="info"
        showIcon
        style={{ margin: '16px 24px 0' }}
      />
      <div
        style={{
          padding: '16px 24px',
          display: 'flex',
          justifyContent: 'flex-end',
          borderBottom: '1px solid var(--color-border-light, #f0f0f0)',
        }}
      >
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          新建角色
        </Button>
      </div>

      <div style={{ padding: '16px 24px 0' }}>
        <Row gutter={[16, 16]}>
          {roles.map((r) => {
            const keys = rolePermMap[r.id] || [];
            const labels = keys.map((k) => keyToLabel.get(k)).filter(Boolean);
            const preview = labels.slice(0, 6);
            const rest = labels.length > 6 ? labels.length - 6 : 0;
            const capCount = r.permission_count ?? keys.length;
            const accent = getRoleAccentVar(r);
            return (
              <Col span={8} key={r.id}>
                <Card
                  variant="borderless"
                  style={{
                    ...roleCardStyle,
                    borderTopColor: accent,
                  }}
                  styles={{ body: { padding: '16px 18px' } }}
                  actions={[
                    <Button
                      key="edit"
                      type="link"
                      size="small"
                      icon={<EditOutlined />}
                      onClick={() => openEdit(r)}
                    >
                      编辑
                    </Button>,
                    <Button
                      key="perm"
                      type="link"
                      size="small"
                      icon={<SafetyCertificateOutlined />}
                      onClick={() => openPermissions(r)}
                    >
                      权限管理
                    </Button>,
                  ]}
                >
                  <Space direction="vertical" size={10} style={{ width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap' }}>
                      <Title level={5} style={{ margin: 0, flex: '1 1 auto' }}>
                        {r.name}
                      </Title>
                      <Badge
                        count={capCount}
                        overflowCount={999}
                        showZero
                        style={{ background: accent }}
                        title="能力点数量"
                      />
                    </div>
                    <Text type="secondary" style={{ fontSize: 'var(--font-size-sm, 13px)', display: 'block' }}>
                      {r.description?.trim() ? r.description : '—'}
                    </Text>
                    <div>
                      <Text type="secondary" style={{ fontSize: 'var(--font-size-xs, 12px)' }}>
                        关键能力
                      </Text>
                      <List
                        size="small"
                        dataSource={preview}
                        locale={{ emptyText: permFetchLoading ? '加载中…' : '暂无权限数据' }}
                        renderItem={(item) => (
                          <List.Item style={{ padding: '4px 0', border: 'none' }}>
                            <Text style={{ fontSize: 'var(--font-size-sm, 13px)' }}>· {item}</Text>
                          </List.Item>
                        )}
                      />
                      {rest > 0 && (
                        <Text type="secondary" style={{ fontSize: 'var(--font-size-xs, 12px)' }}>
                          等{rest}项
                        </Text>
                      )}
                    </div>
                  </Space>
                </Card>
              </Col>
            );
          })}
        </Row>
      </div>

      <div style={{ padding: '24px' }}>
        <Text strong style={{ display: 'block', marginBottom: 8 }}>
          权限对照（只读）
        </Text>
        <Text type="secondary" style={{ fontSize: 'var(--font-size-xs, 12px)', display: 'block', marginBottom: 8 }}>
          行为 granted / denied / 同模块部分授权 一览；编辑请在「权限管理」或下方详细列表中进行。
        </Text>
        <PermissionSummaryMatrix
          modules={permissionModules}
          roles={roles}
          rolePermissionsMap={rolePermMap}
          loading={permFetchLoading || rolesLoading}
        />
      </div>

      <Collapse
        bordered={false}
        style={{ margin: '0 24px 24px', background: 'var(--color-fill, #fafafa)' }}
        items={[
          {
            key: 'role-table',
            label: '详细列表（表格）',
            children: (
              <Table
                rowKey="id"
                columns={columns}
                dataSource={roles}
                loading={rolesLoading}
                pagination={false}
                style={{ width: '100%' }}
              />
            ),
          },
        ]}
      />

      <RoleEditor
        open={editorOpen}
        role={editingRole}
        focusPermissions={focusPermissions}
        onClose={closeEditor}
      />
    </>
  );
}

const TAB_ITEMS = [
  { key: 'users', label: '用户管理', children: <UsersTab /> },
  { key: 'roles', label: '角色管理', children: <RolesTab /> },
];

export default function UserManager() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6, 24px)' }}>
      <div>
        <Title level={4} style={{ marginBottom: 4 }}>
          用户与权限管理
        </Title>
        <Text type="secondary" style={{ fontSize: 'var(--font-size-sm, 13px)' }}>
          管理系统用户账号、角色和权限分配
        </Text>
      </div>

      <Card style={{ minWidth: 0 }} styles={{ body: { padding: 0 } }}>
        <Tabs
          items={TAB_ITEMS}
          style={{ padding: '0 24px' }}
          size="large"
        />
      </Card>
    </div>
  );
}

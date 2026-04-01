import { Alert, Button, Card, Col, Form, Input, Modal, Row, Select, Statistic, Switch, Tabs, Tag, message } from 'antd'
import { useEffect, useMemo, useState } from 'react'

import {
  changeUserStatus,
  createUser,
  fetchPermissionMatrix,
  fetchUsers,
  resetUserPassword,
  updateUserRole,
} from '../../services/api'

const ROLE_LABELS = {
  admin: { label: '系统管理员', color: 'red' },
  pm: { label: '产品经理', color: 'blue' },
  tester: { label: '测试人员', color: 'green' },
}


function RoleTag({ role }) {
  const meta = ROLE_LABELS[role] ?? { label: role, color: 'default' }
  return <Tag color={meta.color}>{meta.label}</Tag>
}


export function UserMgmtPage({ token }) {
  const [directory, setDirectory] = useState({ items: [], summary: { total: 0, admin_count: 0, pm_count: 0, tester_count: 0 } })
  const [permissionMatrix, setPermissionMatrix] = useState([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [previewRole, setPreviewRole] = useState('')
  const [createForm] = Form.useForm()
  const [editForm] = Form.useForm()

  async function loadData() {
    setLoading(true)
    try {
      const [usersData, matrixData] = await Promise.all([
        fetchUsers(token),
        fetchPermissionMatrix(token),
      ])
      setDirectory(usersData)
      setPermissionMatrix(matrixData.items)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadData()
  }, [token])

  const rolePreview = useMemo(() => {
    if (!previewRole) {
      return []
    }
    return permissionMatrix.filter((item) => {
      if (previewRole === 'admin') return item.admin
      if (previewRole === 'pm') return item.pm
      return item.tester
    })
  }, [permissionMatrix, previewRole])

  async function handleCreate(values) {
    await createUser(token, values)
    setCreateOpen(false)
    createForm.resetFields()
    await loadData()
    message.success(`账号 ${values.username} 创建成功`)
  }

  async function handleRoleSave() {
    const values = await editForm.validateFields()
    await updateUserRole(token, editingUser.id, values.role)
    setEditingUser(null)
    setPreviewRole('')
    editForm.resetFields()
    await loadData()
    message.success('角色已更新')
  }

  async function handleStatusToggle(user) {
    const nextStatus = user.status === 'active' ? 'disabled' : 'active'
    await changeUserStatus(token, user.id, nextStatus)
    await loadData()
    message.success(nextStatus === 'active' ? '账号已启用' : '账号已禁用')
  }

  async function handleResetPassword(user) {
    await resetUserPassword(token, user.id)
    message.success(`${user.username} 密码已重置，请通过线下渠道通知用户`)
  }

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless">
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center' }}>
          <div>
            <div className="hero-eyebrow">User Management</div>
            <h2 style={{ color: '#fff', marginBottom: 8 }}>账号管理</h2>
            <p style={{ margin: 0, color: 'rgba(214, 224, 236, 0.78)' }}>
              正式实现账号创建、角色调整、启停用、密码重置与权限矩阵回读。
            </p>
          </div>
          <Button type="primary" size="large" onClick={() => setCreateOpen(true)}>
            新建账号
          </Button>
        </div>
      </Card>

      <Row gutter={18}>
        <Col span={6}>
          <Card className="module-card" variant="borderless">
            <Statistic title="总账号数" value={directory.summary.total} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="module-card" variant="borderless">
            <Statistic title="管理员" value={directory.summary.admin_count} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="module-card" variant="borderless">
            <Statistic title="产品经理" value={directory.summary.pm_count} />
          </Card>
        </Col>
        <Col span={6}>
          <Card className="module-card" variant="borderless">
            <Statistic title="测试人员" value={directory.summary.tester_count} />
          </Card>
        </Col>
      </Row>

      <Tabs
        defaultActiveKey="accounts"
        items={[
          {
            key: 'accounts',
            label: '账号管理',
            children: (
              <Card className="module-card" variant="borderless" loading={loading}>
                <div className="directory-table-wrap">
                  <table className="directory-table">
                    <thead>
                      <tr>
                        <th>用户名</th>
                        <th>姓名</th>
                        <th>角色</th>
                        <th>状态</th>
                        <th>创建日期</th>
                        <th>最后登录</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {directory.items.map((user) => (
                        <tr key={user.id}>
                          <td>{user.username}</td>
                          <td>{user.name}</td>
                          <td><RoleTag role={user.role} /></td>
                          <td>
                            <Tag color={user.status === 'active' ? 'green' : 'default'}>
                              {user.status === 'active' ? '启用' : '禁用'}
                            </Tag>
                          </td>
                          <td>{user.created_at}</td>
                          <td>{user.last_login_at ?? '-'}</td>
                          <td>
                            <div className="table-actions">
                              <Button size="small" onClick={() => {
                                setEditingUser(user)
                                editForm.setFieldsValue({ role: user.role })
                                setPreviewRole(user.role)
                              }}>
                                编辑角色
                              </Button>
                              <Button size="small" onClick={() => handleResetPassword(user)}>
                                重置密码
                              </Button>
                              <Switch
                                checked={user.status === 'active'}
                                checkedChildren="启用"
                                unCheckedChildren="禁用"
                                onChange={() => handleStatusToggle(user)}
                              />
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            ),
          },
          {
            key: 'matrix',
            label: '权限矩阵',
            children: (
              <Card className="module-card" variant="borderless" loading={loading}>
                <div className="directory-table-wrap">
                  <table className="directory-table">
                    <thead>
                      <tr>
                        <th>能力点</th>
                        <th>说明</th>
                        <th>管理员</th>
                        <th>产品经理</th>
                        <th>测试人员</th>
                      </tr>
                    </thead>
                    <tbody>
                      {permissionMatrix.map((item) => (
                        <tr key={item.capability_key}>
                          <td>{item.capability_key}</td>
                          <td>{item.description}</td>
                          <td>{item.admin ? '有' : '-'}</td>
                          <td>{item.pm ? '有' : '-'}</td>
                          <td>{item.tester ? '有' : '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            ),
          },
        ]}
      />

      <Modal
        title="创建账号"
        open={createOpen}
        onCancel={() => {
          setCreateOpen(false)
          createForm.resetFields()
        }}
        onOk={() => createForm.submit()}
        okText="创建"
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate} initialValues={{ role: 'pm' }}>
          <Form.Item name="username" label="用户名" rules={[{ required: true }, { pattern: /^[A-Za-z0-9_]{3,20}$/ }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="姓名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="初始密码" rules={[{ required: true }, { min: 8 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true }]}>
            <Select
              aria-label="角色"
              options={[
                { value: 'admin', label: '系统管理员' },
                { value: 'pm', label: '产品经理' },
                { value: 'tester', label: '测试人员' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={editingUser ? `编辑角色 - ${editingUser.name}` : '编辑角色'}
        open={Boolean(editingUser)}
        onCancel={() => {
          setEditingUser(null)
          setPreviewRole('')
          editForm.resetFields()
        }}
        onOk={handleRoleSave}
        okText="保存"
      >
        {editingUser ? (
          <div className="page-stack">
            <Form form={editForm} layout="vertical">
              <Form.Item name="role" label="新角色" rules={[{ required: true }]}>
                <Select
                  aria-label="新角色"
                  onChange={(value) => setPreviewRole(value)}
                  options={[
                    { value: 'admin', label: '系统管理员' },
                    { value: 'pm', label: '产品经理' },
                    { value: 'tester', label: '测试人员' },
                  ]}
                />
              </Form.Item>
            </Form>
            <Alert type="info" showIcon message="权限预览" description="切换角色后，下方能力点列表会跟着变化。" />
            <div className="preview-list">
              {rolePreview.map((item) => (
                <Tag key={item.capability_key} color="gold">
                  {item.description}
                </Tag>
              ))}
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  )
}

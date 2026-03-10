import { useState } from 'react';
import {
  Table, Button, Space, Tag, Modal, Form, Input, Checkbox, message,
  Typography, Popconfirm, Card,
} from 'antd';
import { PlusOutlined, EditOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { Text } = Typography;

// 权限模块定义：模块 key、显示名、可用操作列表
const PERMISSION_MODULES = [
  { key: 'intent_management', label: '意图管理', ops: ['read', 'write', 'delete'] },
  { key: 'knowledge_management', label: '知识库管理', ops: ['read', 'write', 'delete'] },
  { key: 'dialog_profile', label: '对话方案', ops: ['read', 'write', 'delete'] },
  { key: 'testing', label: '测试', ops: ['manual', 'batch'] },
  { key: 'monitoring', label: '监控', ops: ['dashboard'] },
  { key: 'user_management', label: '用户管理', ops: [] },
  { key: 'version_publish', label: '版本发布', ops: [] },
];

// 操作列的中文映射
const OP_LABELS = {
  read: '读取',
  write: '写入',
  delete: '删除',
  manual: '手动测试',
  batch: '批量测试',
  dashboard: '仪表盘',
};

/**
 * 将 PERMISSION_MODULES 定义的扁平化权限矩阵转换为后端 permissions dict。
 * 无子操作的模块存为顶层布尔值，有子操作的存为嵌套 { op: bool } 对象。
 */
function matrixToPermissions(matrix) {
  const result = {};
  for (const mod of PERMISSION_MODULES) {
    if (mod.ops.length === 0) {
      if (matrix[mod.key]) result[mod.key] = true;
    } else {
      const obj = {};
      let hasAny = false;
      for (const op of mod.ops) {
        const val = !!(matrix[`${mod.key}.${op}`]);
        obj[op] = val;
        if (val) hasAny = true;
      }
      if (hasAny) result[mod.key] = obj;
    }
  }
  return result;
}

/**
 * 将后端 permissions dict 还原为扁平化矩阵供 Checkbox 使用。
 */
function permissionsToMatrix(permissions) {
  const matrix = {};
  if (!permissions) return matrix;
  for (const mod of PERMISSION_MODULES) {
    if (mod.ops.length === 0) {
      matrix[mod.key] = !!permissions[mod.key];
    } else {
      const sub = permissions[mod.key];
      for (const op of mod.ops) {
        matrix[`${mod.key}.${op}`] = !!(sub && sub[op]);
      }
    }
  }
  return matrix;
}

export default function RoleEditor({ roles, onRolesChange }) {
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [permMatrix, setPermMatrix] = useState({});
  const [form] = Form.useForm();

  const openCreate = () => {
    setEditingRole(null);
    form.resetFields();
    setPermMatrix({});
    setModalVisible(true);
  };

  const openEdit = (role) => {
    setEditingRole(role);
    form.setFieldsValue({ name: role.name });
    setPermMatrix(permissionsToMatrix(role.permissions));
    setModalVisible(true);
  };

  const togglePerm = (key) => {
    setPermMatrix((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // 模块全选/取消
  const toggleModuleAll = (mod, checked) => {
    setPermMatrix((prev) => {
      const next = { ...prev };
      if (mod.ops.length === 0) {
        next[mod.key] = checked;
      } else {
        for (const op of mod.ops) {
          next[`${mod.key}.${op}`] = checked;
        }
      }
      return next;
    });
  };

  const isModuleAllChecked = (mod) => {
    if (mod.ops.length === 0) return !!permMatrix[mod.key];
    return mod.ops.every((op) => !!permMatrix[`${mod.key}.${op}`]);
  };

  const isModulePartial = (mod) => {
    if (mod.ops.length === 0) return false;
    const checked = mod.ops.filter((op) => !!permMatrix[`${mod.key}.${op}`]);
    return checked.length > 0 && checked.length < mod.ops.length;
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const permissions = matrixToPermissions(permMatrix);
      const payload = { name: values.name, permissions };
      if (editingRole) {
        await api.patch(`/auth/roles/${editingRole.id}`, payload);
        message.success('角色更新成功');
      } else {
        await api.post('/auth/roles', payload);
        message.success('角色创建成功');
      }
      setModalVisible(false);
      onRolesChange();
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '操作失败');
    }
  };

  // 权限矩阵表格数据源
  const matrixDataSource = PERMISSION_MODULES.map((mod) => ({
    key: mod.key,
    ...mod,
  }));

  // 收集所有可能的操作列（去重、有序）
  const allOps = [...new Set(PERMISSION_MODULES.flatMap((m) => m.ops))];

  const matrixColumns = [
    {
      title: '权限模块',
      dataIndex: 'label',
      key: 'label',
      width: 160,
      render: (label, record) => (
        <Checkbox
          checked={isModuleAllChecked(record)}
          indeterminate={isModulePartial(record)}
          onChange={(e) => toggleModuleAll(record, e.target.checked)}
        >
          <Text strong>{label}</Text>
        </Checkbox>
      ),
    },
    ...allOps.map((op) => ({
      title: OP_LABELS[op] || op,
      key: op,
      width: 100,
      align: 'center',
      render: (_, record) => {
        if (record.ops.length === 0) return <Text type="secondary">—</Text>;
        if (!record.ops.includes(op)) return <Text type="secondary">—</Text>;
        const permKey = `${record.key}.${op}`;
        return (
          <Checkbox
            checked={!!permMatrix[permKey]}
            onChange={() => togglePerm(permKey)}
          />
        );
      },
    })),
  ];

  const roleColumns = [
    { title: '角色名称', dataIndex: 'name', key: 'name' },
    {
      title: '类型',
      dataIndex: 'is_system',
      key: 'is_system',
      render: (v) => v ? <Tag color="red">系统</Tag> : <Tag color="green">自定义</Tag>,
    },
    {
      title: '权限概览',
      key: 'perms',
      render: (_, record) => {
        const keys = Object.keys(record.permissions || {});
        if (keys.length === 0) return <Text type="secondary">无权限</Text>;
        return (
          <Space wrap>
            {keys.map((k) => {
              const mod = PERMISSION_MODULES.find((m) => m.key === k);
              return <Tag key={k}>{mod?.label || k}</Tag>;
            })}
          </Space>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button
          size="small"
          icon={<EditOutlined />}
          disabled={record.is_system}
          onClick={() => openEdit(record)}
        >
          编辑
        </Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          新建角色
        </Button>
      </div>

      <Table
        rowKey="id"
        columns={roleColumns}
        dataSource={roles}
        pagination={false}
      />

      <Modal
        title={editingRole ? `编辑角色：${editingRole.name}` : '新建角色'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        width={720}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginBottom: 16 }}>
          <Form.Item
            name="name"
            label="角色名称"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input placeholder="如：管理员、编辑员、测试员" />
          </Form.Item>
        </Form>

        <Card title="权限矩阵" size="small">
          <Table
            rowKey="key"
            columns={matrixColumns}
            dataSource={matrixDataSource}
            pagination={false}
            size="small"
            bordered
          />
        </Card>
      </Modal>
    </div>
  );
}

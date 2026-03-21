import { useState, useEffect, useCallback, useRef } from 'react';
import { Modal, Form, Input, message } from 'antd';
import PermissionMatrix from './PermissionMatrix';
import useUserStore from '../../stores/userStore';

export default function RoleEditor({ open, role, onClose, focusPermissions = false }) {
  const [form] = Form.useForm();
  const [selectedKeys, setSelectedKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [permLoading, setPermLoading] = useState(false);

  const {
    permissionModules,
    fetchPermissions,
    createRole,
    updateRole,
    getRolePermissions,
    updateRolePermissions,
  } = useUserStore();

  const isEdit = !!role;
  const permAnchorRef = useRef(null);

  useEffect(() => {
    if (!open || !focusPermissions) return;
    const id = requestAnimationFrame(() => {
      permAnchorRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' });
    });
    return () => cancelAnimationFrame(id);
  }, [open, focusPermissions, role?.id]);

  useEffect(() => {
    if (!open) return;

    if (permissionModules.length === 0) {
      fetchPermissions();
    }

    if (role) {
      form.setFieldsValue({ name: role.name, description: role.description });
      setPermLoading(true);
      getRolePermissions(role.id)
        .then((keys) => setSelectedKeys(keys))
        .catch(() => setSelectedKeys([]))
        .finally(() => setPermLoading(false));
    } else {
      form.resetFields();
      setSelectedKeys([]);
    }
  }, [open, role, form, fetchPermissions, getRolePermissions, permissionModules.length]);

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      if (isEdit) {
        await updateRole(role.id, values);
        await updateRolePermissions(role.id, selectedKeys);
        message.success('角色已更新');
      } else {
        await createRole({ ...values, permission_keys: selectedKeys });
        message.success('角色已创建');
      }
      onClose?.();
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '操作失败');
    } finally {
      setLoading(false);
    }
  }, [form, isEdit, role, selectedKeys, createRole, updateRole, updateRolePermissions, onClose]);

  return (
    <Modal
      open={open}
      title={isEdit ? '编辑角色' : '新建角色'}
      onCancel={onClose}
      onOk={handleSubmit}
      confirmLoading={loading}
      okText={isEdit ? '保存' : '创建'}
      cancelText="取消"
      width={680}
      centered
      destroyOnHidden
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item
          name="name"
          label="角色名称"
          rules={[{ required: true, message: '请输入角色名称' }]}
        >
          <Input
            placeholder="例如: 测试工程师"
            disabled={role?.is_builtin}
            maxLength={30}
          />
        </Form.Item>
        <Form.Item name="description" label="描述">
          <Input.TextArea rows={2} placeholder="角色描述..." maxLength={200} />
        </Form.Item>
        <Form.Item label="权限配置">
          <div ref={permAnchorRef}>
            <PermissionMatrix
              modules={permissionModules}
              selectedKeys={selectedKeys}
              onChange={setSelectedKeys}
              loading={permLoading}
            />
          </div>
        </Form.Item>
      </Form>
    </Modal>
  );
}

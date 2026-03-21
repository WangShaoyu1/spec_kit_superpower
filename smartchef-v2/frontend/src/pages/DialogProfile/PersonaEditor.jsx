import { useEffect, useCallback } from 'react';
import { Modal, Form, Input, Slider, InputNumber, Row, Col } from 'antd';

export default function PersonaEditor({
  open,
  persona,
  onSave,
  onCancel,
  loading = false,
}) {
  const [form] = Form.useForm();
  const isEdit = !!persona;

  useEffect(() => {
    if (open) {
      if (persona) {
        form.setFieldsValue({
          name: persona.name,
          system_prompt: persona.system_prompt,
          personality: persona.personality,
          temperature: persona.temperature ?? 0.7,
          max_tokens: persona.max_tokens ?? 1024,
        });
      } else {
        form.resetFields();
        form.setFieldsValue({ temperature: 0.7, max_tokens: 1024 });
      }
    }
  }, [open, persona, form]);

  const handleOk = useCallback(async () => {
    try {
      const values = await form.validateFields();
      onSave?.(values);
    } catch {
      // validation errors shown by form
    }
  }, [form, onSave]);

  return (
    <Modal
      open={open}
      title={isEdit ? '编辑人设' : '新建人设'}
      onCancel={onCancel}
      onOk={handleOk}
      confirmLoading={loading}
      okText={isEdit ? '保存' : '创建'}
      cancelText="取消"
      width={640}
      centered
      destroyOnHidden
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item
          name="name"
          label="人设名称"
          rules={[{ required: true, message: '请输入人设名称' }]}
        >
          <Input placeholder="例如: 友好厨师助手" maxLength={100} />
        </Form.Item>

        <Form.Item
          name="system_prompt"
          label="系统提示词"
          rules={[{ required: true, message: '请输入系统提示词' }]}
          extra="定义 AI 助手的角色和行为方式"
        >
          <Input.TextArea
            rows={6}
            placeholder="你是一个专业的烹饪助手，热情友好，善于根据用户的食材和口味偏好推荐菜谱..."
            maxLength={10000}
            showCount
            style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-sm)' }}
          />
        </Form.Item>

        <Form.Item name="personality" label="性格描述">
          <Input.TextArea
            rows={2}
            placeholder="热情、专业、幽默..."
            maxLength={500}
          />
        </Form.Item>

        <Row gutter={24}>
          <Col span={14}>
            <Form.Item name="temperature" label="Temperature（创造性）">
              <Slider
                min={0}
                max={2}
                step={0.1}
                marks={{
                  0: '精确',
                  0.7: '平衡',
                  1.5: '创造',
                  2: '随机',
                }}
              />
            </Form.Item>
          </Col>
          <Col span={10}>
            <Form.Item
              name="max_tokens"
              label="最大 Token 数"
              rules={[{ required: true, message: '请输入' }]}
            >
              <InputNumber
                min={1}
                max={8192}
                step={256}
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
        </Row>
      </Form>
    </Modal>
  );
}

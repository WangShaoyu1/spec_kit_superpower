import { Form, Select, Switch, InputNumber, Input, Button, Card } from 'antd';
import { MobileOutlined } from '@ant-design/icons';

const COOKING_STATUS_OPTIONS = [
  { label: '空闲', value: 'idle' },
  { label: '烹饪中', value: 'cooking' },
  { label: '已暂停', value: 'paused' },
];

const CURRENT_PAGE_OPTIONS = [
  { label: '主页', value: 'home' },
  { label: '烹饪进度', value: 'cooking_progress' },
  { label: '菜谱浏览', value: 'recipe_browser' },
  { label: '菜谱详情', value: 'recipe_detail' },
  { label: '设置', value: 'settings' },
  { label: '其他', value: 'other' },
];

const DEFAULT_VALUES = {
  cooking_status: 'idle',
  door_closed: true,
  current_temp: 25,
  current_page: 'home',
  screen_info: '',
};

/**
 * 设备上下文模拟器 - 用于手动测试时模拟设备状态
 * @param {Function} onSubmit - 提交回调，接收 device_context 对象
 * @param {Object} initialValues - 初始表单值
 */
export default function DeviceContextSimulator({ onSubmit, initialValues }) {
  const [form] = Form.useForm();

  const handleSubmit = () => {
    form.validateFields().then((values) => {
      const device_context = {
        cooking_status: values.cooking_status,
        door_closed: values.door_closed,
        current_temp: values.current_temp,
        current_page: values.current_page,
        screen_info: values.screen_info?.trim() || undefined,
      };
      onSubmit?.(device_context);
    });
  };

  const handleReset = () => {
    form.setFieldsValue(DEFAULT_VALUES);
  };

  return (
    <Card
      title="设备上下文模拟"
      size="small"
      extra={
        <Button type="link" size="small" onClick={handleReset}>
          重置
        </Button>
      }
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ ...DEFAULT_VALUES, ...initialValues }}
        size="small"
      >
        <Form.Item
          name="cooking_status"
          label="烹饪状态"
          rules={[{ required: true }]}
        >
          <Select
            placeholder="选择烹饪状态"
            options={COOKING_STATUS_OPTIONS}
          />
        </Form.Item>

        <Form.Item
          name="door_closed"
          label="炉门状态"
          valuePropName="checked"
        >
          <Switch checkedChildren="关" unCheckedChildren="开" />
        </Form.Item>

        <Form.Item
          name="current_temp"
          label="当前温度 (℃)"
          rules={[{ required: true }]}
        >
          <InputNumber
            min={0}
            max={300}
            placeholder="25"
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          name="current_page"
          label="当前页面"
          rules={[{ required: true }]}
        >
          <Select
            placeholder="选择当前页面"
            options={CURRENT_PAGE_OPTIONS}
          />
        </Form.Item>

        <Form.Item
          name="screen_info"
          label="屏幕信息"
        >
          <Input.TextArea
            rows={3}
            placeholder="可填写当前屏幕显示的文本摘要，用于上下文理解"
          />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="button"
            icon={<MobileOutlined />}
            block
            onClick={handleSubmit}
          >
            应用设备上下文
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}

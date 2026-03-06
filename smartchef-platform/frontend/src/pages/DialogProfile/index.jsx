import { useEffect, useState } from 'react';
import {
  Table, Button, Space, Tag, Modal, Form, Input, Select, InputNumber,
  message, Typography, Popconfirm, Card, Descriptions,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import api from '../../services/api';
import PersonaEditor from './PersonaEditor';
import ModelSelector from './ModelSelector';

const { Title } = Typography;

const STATUS_MAP = {
  draft: { color: 'default', text: '草稿' },
  testing: { color: 'blue', text: '测试中' },
  published: { color: 'green', text: '已发布' },
  archived: { color: 'red', text: '已归档' },
};

const ROUTING_OPTIONS = [
  { label: '指令优先', value: 'command_first' },
  { label: '知识优先', value: 'knowledge_first' },
  { label: '均衡', value: 'balanced' },
];

export default function DialogProfilePage() {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editing, setEditing] = useState(null);
  const [detailProfile, setDetailProfile] = useState(null);
  const [personas, setPersonas] = useState([]);
  const [personaModalVisible, setPersonaModalVisible] = useState(false);
  const [form] = Form.useForm();

  const fetchProfiles = async () => {
    setLoading(true);
    try {
      const res = await api.get('/profiles');
      setProfiles(res.data);
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  const fetchPersonas = async () => {
    try {
      const res = await api.get('/profiles/personas/list');
      setPersonas(res.data);
    } catch { /* empty */ }
  };

  useEffect(() => { fetchProfiles(); fetchPersonas(); }, []);

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({ routing_strategy: 'command_first', session_timeout_minutes: 10 });
    setModalVisible(true);
  };

  const openEdit = (profile) => {
    setEditing(profile);
    form.setFieldsValue(profile);
    setModalVisible(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editing) {
        await api.patch(`/profiles/${editing.id}`, values);
        message.success('更新成功');
      } else {
        await api.post('/profiles', values);
        message.success('创建成功');
      }
      setModalVisible(false);
      fetchProfiles();
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '操作失败');
    }
  };

  const handleDelete = async (id) => {
    await api.delete(`/profiles/${id}`);
    message.success('删除成功');
    fetchProfiles();
  };

  const columns = [
    { title: '方案名称', dataIndex: 'name', key: 'name' },
    { title: '大模型', dataIndex: 'llm_provider', key: 'llm' },
    {
      title: '路由策略', dataIndex: 'routing_strategy', key: 'routing',
      render: (v) => ROUTING_OPTIONS.find((o) => o.value === v)?.label || v,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (v) => <Tag color={STATUS_MAP[v]?.color}>{STATUS_MAP[v]?.text || v}</Tag>,
    },
    { title: '超时(分)', dataIndex: 'session_timeout_minutes', key: 'timeout', width: 80 },
    {
      title: '操作', key: 'action', width: 200,
      render: (_, r) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => setDetailProfile(r)}>详情</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(r)} />
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>对话方案配置</Title>
        <Space>
          <Button onClick={() => setPersonaModalVisible(true)}>管理人设</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>新建方案</Button>
        </Space>
      </div>

      <Table rowKey="id" columns={columns} dataSource={profiles} loading={loading} pagination={false} />

      <Modal title={editing ? '编辑方案' : '新建方案'} open={modalVisible}
        onOk={handleSave} onCancel={() => setModalVisible(false)} width={640}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="方案名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="llm_provider" label="大模型" rules={[{ required: true }]}>
            <ModelSelector />
          </Form.Item>
          <Form.Item name="persona_id" label="闲聊人设">
            <Select allowClear placeholder="选择人设"
              options={personas.map((p) => ({ label: `${p.name} - ${p.personality.slice(0, 30)}`, value: p.id }))}
            />
          </Form.Item>
          <Form.Item name="routing_strategy" label="路由策略"><Select options={ROUTING_OPTIONS} /></Form.Item>
          <Form.Item name="session_timeout_minutes" label="会话超时(分钟)">
            <InputNumber min={1} max={60} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="方案详情" open={!!detailProfile} onCancel={() => setDetailProfile(null)} footer={null} width={640}>
        {detailProfile && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="名称">{detailProfile.name}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={STATUS_MAP[detailProfile.status]?.color}>{STATUS_MAP[detailProfile.status]?.text}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="大模型">{detailProfile.llm_provider}</Descriptions.Item>
            <Descriptions.Item label="路由策略">{detailProfile.routing_strategy}</Descriptions.Item>
            <Descriptions.Item label="超时">{detailProfile.session_timeout_minutes} 分钟</Descriptions.Item>
            <Descriptions.Item label="人设">{detailProfile.persona?.name || '未设置'}</Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>{detailProfile.description || '-'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      <PersonaEditor
        visible={personaModalVisible}
        onClose={() => setPersonaModalVisible(false)}
        personas={personas}
        onUpdate={fetchPersonas}
      />
    </div>
  );
}

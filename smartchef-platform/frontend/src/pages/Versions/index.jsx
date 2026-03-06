import { useEffect, useState } from 'react';
import { Table, Button, Tag, Typography, Space, Modal, Form, Input, Select, message, Popconfirm } from 'antd';
import { RocketOutlined, CheckCircleOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { Title } = Typography;

export default function VersionsPage() {
  const [versions, setVersions] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [publishVisible, setPublishVisible] = useState(false);
  const [form] = Form.useForm();

  const fetchVersions = async () => {
    setLoading(true);
    try {
      const res = await api.get('/versions');
      setVersions(res.data);
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  const fetchProfiles = async () => {
    try {
      const res = await api.get('/profiles');
      setProfiles(res.data);
    } catch { /* empty */ }
  };

  useEffect(() => { fetchVersions(); fetchProfiles(); }, []);

  const handlePublish = async () => {
    try {
      const values = await form.validateFields();
      await api.post('/versions', null, { params: values });
      message.success('发布成功，所有设备会话已重置');
      setPublishVisible(false);
      form.resetFields();
      fetchVersions();
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '发布失败');
    }
  };

  const handleActivate = async (id) => {
    try {
      await api.post(`/versions/${id}/activate`);
      message.success('切换成功，所有设备会话已重置');
      fetchVersions();
    } catch (err) {
      message.error(err.response?.data?.detail || '操作失败');
    }
  };

  const columns = [
    { title: '版本号', dataIndex: 'version_tag', key: 'tag' },
    { title: '描述', dataIndex: 'description', key: 'desc', ellipsis: true },
    {
      title: '状态', dataIndex: 'is_active', key: 'status',
      render: (v) => v ? <Tag icon={<CheckCircleOutlined />} color="success">生产中</Tag> : <Tag>非活跃</Tag>,
    },
    { title: '发布时间', dataIndex: 'created_at', key: 'time', render: (v) => new Date(v).toLocaleString() },
    {
      title: '操作', key: 'action', width: 120,
      render: (_, r) => !r.is_active && (
        <Popconfirm title="切换到此版本会重置所有设备会话，确认？" onConfirm={() => handleActivate(r.id)}>
          <Button size="small" type="link">激活</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>版本管理</Title>
        <Button type="primary" icon={<RocketOutlined />} onClick={() => { form.resetFields(); setPublishVisible(true); }}>
          发布新版本
        </Button>
      </div>

      <Table rowKey="id" columns={columns} dataSource={versions} loading={loading} pagination={false} />

      <Modal title="发布新版本" open={publishVisible} onOk={handlePublish} onCancel={() => setPublishVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="profile_id" label="对话方案" rules={[{ required: true }]}>
            <Select placeholder="选择要发布的方案"
              options={profiles.map(p => ({ label: `${p.name} (${p.llm_provider})`, value: p.id }))}
            />
          </Form.Item>
          <Form.Item name="version_tag" label="版本号" rules={[{ required: true }]}>
            <Input placeholder="如：v1.0.0" />
          </Form.Item>
          <Form.Item name="description" label="版本描述"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

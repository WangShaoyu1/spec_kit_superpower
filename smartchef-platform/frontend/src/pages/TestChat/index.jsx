import { useEffect, useState, useRef } from 'react';
import {
  Card, Button, Space, Input, Select, Typography, Tag, Collapse, Descriptions,
  message, Form, Modal, Empty, Spin, Divider,
} from 'antd';
import { SendOutlined, PlusOutlined, SettingOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { Title, Text } = Typography;

const DEVICE_CONTEXT_PRESETS = [
  { label: '空闲 - 主页', value: { cooking_status: 'idle', door_closed: true, current_temp: 25, current_page: 'home' } },
  { label: '正在烹饪', value: { cooking_status: 'cooking', door_closed: true, current_temp: 180, current_page: 'cooking_progress' } },
  { label: '菜谱浏览', value: { cooking_status: 'idle', door_closed: true, current_temp: 25, current_page: 'recipe_browser' } },
];

export default function TestChatPage() {
  const [profiles, setProfiles] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const [createVisible, setCreateVisible] = useState(false);
  const [form] = Form.useForm();
  const chatEndRef = useRef(null);

  const fetchProfiles = async () => {
    try {
      const res = await api.get('/profiles');
      setProfiles(res.data);
    } catch { /* empty */ }
  };

  const fetchSessions = async () => {
    try {
      const res = await api.get('/test/sessions');
      setSessions(res.data);
    } catch { /* empty */ }
  };

  useEffect(() => { fetchProfiles(); fetchSessions(); }, []);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatHistory]);

  const handleCreateSession = async () => {
    try {
      const values = await form.validateFields();
      const preset = DEVICE_CONTEXT_PRESETS.find(p => p.label === values.context_preset);
      const resp = await api.post('/test/sessions', {
        name: values.name,
        profile_id: values.profile_id,
        device_context: preset?.value || null,
        notes: values.notes,
      });
      message.success('会话创建成功');
      setCreateVisible(false);
      form.resetFields();
      fetchSessions();
      setCurrentSession(resp.data);
      setChatHistory([]);
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '创建失败');
    }
  };

  const handleSend = async () => {
    if (!inputText.trim() || !currentSession) return;
    const text = inputText.trim();
    setInputText('');
    setChatHistory(prev => [...prev, { role: 'user', text }]);
    setSending(true);

    try {
      const resp = await api.post('/test/chat', { session_id: currentSession.id, text });
      setChatHistory(prev => [...prev, { role: 'assistant', ...resp.data }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'error', text: '请求失败: ' + (err.response?.data?.detail || err.message) }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 200px)' }}>
      <Card title="测试会话" style={{ width: 280, overflow: 'auto' }}
        extra={<Button size="small" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setCreateVisible(true); }}>新建</Button>}
      >
        {sessions.map(s => (
          <Card key={s.id} size="small" hoverable
            onClick={() => { setCurrentSession(s); setChatHistory([]); }}
            style={{ marginBottom: 8, borderColor: currentSession?.id === s.id ? '#1890ff' : undefined }}
          >
            <Text strong>{s.name}</Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>{new Date(s.created_at).toLocaleString()}</Text>
          </Card>
        ))}
        {sessions.length === 0 && <Empty description="暂无测试会话" />}
      </Card>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Card style={{ flex: 1, overflow: 'auto', marginBottom: 8 }}
          title={currentSession ? `💬 ${currentSession.name}` : '请选择或创建测试会话'}
        >
          <div style={{ padding: '8px 0' }}>
            {chatHistory.map((msg, idx) => (
              <div key={idx} style={{ marginBottom: 16 }}>
                {msg.role === 'user' ? (
                  <div style={{ textAlign: 'right' }}>
                    <Tag color="blue">用户</Tag>
                    <div style={{ background: '#e6f7ff', padding: '8px 12px', borderRadius: 8, display: 'inline-block', maxWidth: '70%', textAlign: 'left' }}>
                      {msg.text}
                    </div>
                  </div>
                ) : msg.role === 'error' ? (
                  <div><Tag color="red">错误</Tag> <Text type="danger">{msg.text}</Text></div>
                ) : (
                  <div>
                    <Tag color="green">助手</Tag>
                    <div style={{ background: '#f6ffed', padding: '8px 12px', borderRadius: 8, display: 'inline-block', maxWidth: '80%' }}>
                      <div>{msg.response_text}</div>
                    </div>
                    <Collapse ghost size="small" style={{ marginTop: 4 }}
                      items={[{
                        key: '1',
                        label: <Text type="secondary" style={{ fontSize: 12 }}>调试信息 ({msg.latency_ms}ms)</Text>,
                        children: (
                          <Descriptions size="small" column={2} bordered>
                            <Descriptions.Item label="域">{msg.domain}</Descriptions.Item>
                            <Descriptions.Item label="路由置信度">{msg.route_confidence}</Descriptions.Item>
                            <Descriptions.Item label="意图">{msg.intent || '-'}</Descriptions.Item>
                            <Descriptions.Item label="意图置信度">{msg.intent_confidence ?? '-'}</Descriptions.Item>
                            <Descriptions.Item label="槽位" span={2}>
                              {Object.entries(msg.slots || {}).map(([k, v]) => <Tag key={k}>{k}={v}</Tag>)}
                              {Object.keys(msg.slots || {}).length === 0 && '-'}
                            </Descriptions.Item>
                            <Descriptions.Item label="需要后续" span={2}>{msg.needs_followup ? '是' : '否'}</Descriptions.Item>
                          </Descriptions>
                        ),
                      }]}
                    />
                  </div>
                )}
              </div>
            ))}
            {sending && <Spin tip="思考中..." />}
            <div ref={chatEndRef} />
          </div>
        </Card>

        <Space.Compact style={{ width: '100%' }}>
          <Input
            placeholder={currentSession ? "输入测试语句..." : "请先选择测试会话"}
            value={inputText}
            onChange={e => setInputText(e.target.value)}
            onPressEnter={handleSend}
            disabled={!currentSession || sending}
            size="large"
          />
          <Button type="primary" icon={<SendOutlined />} size="large"
            onClick={handleSend} disabled={!currentSession || sending || !inputText.trim()}
          >
            发送
          </Button>
        </Space.Compact>
      </div>

      <Modal title="新建测试会话" open={createVisible} onOk={handleCreateSession} onCancel={() => setCreateVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="会话名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="profile_id" label="对话方案" rules={[{ required: true }]}>
            <Select placeholder="选择对话方案"
              options={profiles.map(p => ({ label: `${p.name} (${p.llm_provider})`, value: p.id }))}
            />
          </Form.Item>
          <Form.Item name="context_preset" label="模拟设备上下文">
            <Select allowClear placeholder="选择预设上下文"
              options={DEVICE_CONTEXT_PRESETS.map(p => ({ label: p.label, value: p.label }))}
            />
          </Form.Item>
          <Form.Item name="notes" label="备注"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

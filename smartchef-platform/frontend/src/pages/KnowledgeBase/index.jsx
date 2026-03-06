import { useEffect, useState } from 'react';
import {
  Card, Button, Space, Typography, Table, Tag, Modal, Form, Input, message, Popconfirm, Empty,
} from 'antd';
import { PlusOutlined, UploadOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import api from '../../services/api';
import DocumentUpload from './DocumentUpload';

const { Title, Text } = Typography;

export default function KnowledgeBasePage() {
  const [bases, setBases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [createVisible, setCreateVisible] = useState(false);
  const [selectedBase, setSelectedBase] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [uploadVisible, setUploadVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [form] = Form.useForm();

  const fetchBases = async () => {
    setLoading(true);
    try {
      const res = await api.get('/knowledge/bases');
      setBases(res.data);
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  const fetchDocuments = async (kbId) => {
    setDocsLoading(true);
    try {
      const res = await api.get(`/knowledge/bases/${kbId}/documents`);
      setDocuments(res.data);
    } catch { message.error('加载文档失败'); }
    finally { setDocsLoading(false); }
  };

  useEffect(() => { fetchBases(); }, []);
  useEffect(() => { if (selectedBase) fetchDocuments(selectedBase.id); }, [selectedBase]);

  const handleCreateBase = async () => {
    try {
      const values = await form.validateFields();
      await api.post('/knowledge/bases', values);
      message.success('创建成功');
      setCreateVisible(false);
      form.resetFields();
      fetchBases();
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '创建失败');
    }
  };

  const handleDeleteBase = async (id) => {
    await api.delete(`/knowledge/bases/${id}`);
    message.success('删除成功');
    if (selectedBase?.id === id) { setSelectedBase(null); setDocuments([]); }
    fetchBases();
  };

  const handleDeleteDoc = async (docId) => {
    await api.delete(`/knowledge/documents/${docId}`);
    message.success('删除成功');
    fetchDocuments(selectedBase.id);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    try {
      const res = await api.post('/knowledge/search', {
        query: searchQuery,
        knowledge_base_id: selectedBase?.id || null,
        top_k: 5,
      });
      setSearchResults(res.data);
    } catch { message.error('搜索失败'); }
  };

  const baseColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '文档数', dataIndex: 'document_count', key: 'document_count', width: 80 },
    {
      title: '操作', key: 'action', width: 160,
      render: (_, r) => (
        <Space>
          <Button size="small" onClick={() => setSelectedBase(r)}>管理</Button>
          <Popconfirm title="确认删除？" onConfirm={() => handleDeleteBase(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const docColumns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '格式', dataIndex: 'source_format', key: 'format', width: 80,
      render: (v) => <Tag>{v}</Tag> },
    { title: '状态', dataIndex: 'index_status', key: 'status', width: 100,
      render: (v) => <Tag color={v === 'indexed' ? 'green' : v === 'failed' ? 'red' : 'orange'}>{v}</Tag> },
    { title: '操作', key: 'action', width: 80,
      render: (_, r) => (
        <Popconfirm title="确认删除？" onConfirm={() => handleDeleteDoc(r.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>知识库管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setCreateVisible(true); }}>
          新建知识库
        </Button>
      </div>

      <Table rowKey="id" columns={baseColumns} dataSource={bases} loading={loading} pagination={false} size="small" />

      {selectedBase && (
        <Card title={`📚 ${selectedBase.name} - 文档管理`} style={{ marginTop: 16 }}
          extra={<Button icon={<UploadOutlined />} onClick={() => setUploadVisible(true)}>上传文档</Button>}
        >
          <Table rowKey="id" columns={docColumns} dataSource={documents} loading={docsLoading} size="small" />

          <div style={{ marginTop: 16 }}>
            <Text strong>知识检索测试</Text>
            <Space style={{ marginTop: 8, width: '100%' }}>
              <Input placeholder="输入查询语句..." value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onPressEnter={handleSearch} style={{ width: 400 }}
              />
              <Button icon={<SearchOutlined />} onClick={handleSearch}>搜索</Button>
            </Space>
            {searchResults.length > 0 && (
              <div style={{ marginTop: 12 }}>
                {searchResults.map((r, i) => (
                  <Card key={i} size="small" style={{ marginBottom: 8 }}>
                    <Text strong>{r.document_title}</Text>
                    <Tag color="blue" style={{ marginLeft: 8 }}>相似度: {r.score}</Tag>
                    <div style={{ marginTop: 4 }}><Text type="secondary">{r.chunk_text}</Text></div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </Card>
      )}

      <Modal title="新建知识库" open={createVisible} onOk={handleCreateBase} onCancel={() => setCreateVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Modal>

      <DocumentUpload
        visible={uploadVisible}
        kbId={selectedBase?.id}
        onClose={() => setUploadVisible(false)}
        onSuccess={() => { setUploadVisible(false); fetchDocuments(selectedBase.id); fetchBases(); }}
      />
    </div>
  );
}

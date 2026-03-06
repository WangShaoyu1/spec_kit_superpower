import { useEffect, useState } from 'react';
import {
  Card, Button, Table, Tag, Typography, Space, Modal, Form, Input, Select,
  InputNumber, message, Progress, Collapse, Descriptions, Empty,
} from 'antd';
import { PlusOutlined, FileTextOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { Title, Text } = Typography;

export default function BatchTestPage() {
  const [jobs, setJobs] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [createVisible, setCreateVisible] = useState(false);
  const [detailJob, setDetailJob] = useState(null);
  const [detailCases, setDetailCases] = useState([]);
  const [form] = Form.useForm();

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await api.get('/batch-test/jobs');
      setJobs(res.data);
    } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  const fetchProfiles = async () => {
    try { const res = await api.get('/profiles'); setProfiles(res.data); } catch { /* */ }
  };

  useEffect(() => { fetchJobs(); fetchProfiles(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      const lines = values.test_cases_text.split('\n').filter(l => l.trim());
      const test_cases = lines.map(line => {
        const parts = line.split('|');
        return {
          input_text: parts[0]?.trim() || '',
          expected_intent: parts[1]?.trim() || null,
          expected_domain: parts[2]?.trim() || null,
        };
      }).filter(tc => tc.input_text);

      if (!test_cases.length) { message.error('请输入测试用例'); return; }

      await api.post('/batch-test/jobs', {
        name: values.name, profile_id: values.profile_id,
        test_cases, accuracy_threshold: values.accuracy_threshold / 100,
        latency_threshold_ms: values.latency_threshold_ms,
      });
      message.success('批量测试完成');
      setCreateVisible(false);
      form.resetFields();
      fetchJobs();
    } catch (err) {
      if (err.response) message.error(err.response.data?.detail || '执行失败');
    }
  };

  const viewDetail = async (job) => {
    setDetailJob(job);
    try {
      const res = await api.get(`/batch-test/jobs/${job.id}/cases`);
      setDetailCases(res.data);
    } catch { message.error('加载详情失败'); }
  };

  const columns = [
    { title: '名称', dataIndex: 'name' },
    { title: '状态', dataIndex: 'status', width: 80,
      render: v => <Tag color={v === 'completed' ? 'green' : v === 'running' ? 'blue' : 'default'}>{v}</Tag> },
    { title: '用例数', dataIndex: 'total_cases', width: 80 },
    { title: '准确率', dataIndex: 'accuracy', width: 100,
      render: v => v != null ? <Progress percent={Math.round(v * 100)} size="small" /> : '-' },
    { title: '平均延迟', dataIndex: 'avg_latency_ms', width: 100, render: v => v ? `${v.toFixed(0)}ms` : '-' },
    { title: '操作', width: 80, render: (_, r) => <Button size="small" icon={<FileTextOutlined />} onClick={() => viewDetail(r)}>详情</Button> },
  ];

  const caseColumns = [
    { title: '输入', dataIndex: 'input_text', ellipsis: true },
    { title: '期望意图', dataIndex: 'expected_intent', width: 120 },
    { title: '实际意图', dataIndex: 'actual_intent', width: 120 },
    { title: '域', dataIndex: 'actual_domain', width: 80, render: v => <Tag>{v}</Tag> },
    { title: '置信度', dataIndex: 'intent_confidence', width: 80, render: v => v?.toFixed(2) },
    { title: '延迟', dataIndex: 'latency_ms', width: 80, render: v => v ? `${v}ms` : '-' },
    { title: '通过', dataIndex: 'passed', width: 60,
      render: v => v ? <Tag color="green">通过</Tag> : <Tag color="red">失败</Tag> },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>批量测试与分析</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setCreateVisible(true); }}>
          新建测试
        </Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={jobs} loading={loading} pagination={false} />

      <Modal title={`测试详情: ${detailJob?.name || ''}`} open={!!detailJob} onCancel={() => setDetailJob(null)} footer={null} width={1000}>
        {detailJob?.report && (
          <Card size="small" style={{ marginBottom: 16 }}>
            <Descriptions size="small" column={4}>
              <Descriptions.Item label="总体">{detailJob.report.overall_pass ? <Tag color="green">达标</Tag> : <Tag color="red">不达标</Tag>}</Descriptions.Item>
              <Descriptions.Item label="准确率">{(detailJob.accuracy * 100).toFixed(1)}%</Descriptions.Item>
              <Descriptions.Item label="平均延迟">{detailJob.avg_latency_ms?.toFixed(0)}ms</Descriptions.Item>
              <Descriptions.Item label="通过/失败">{detailJob.passed_cases}/{detailJob.failed_cases}</Descriptions.Item>
            </Descriptions>
            {(detailJob.report.issues || []).map((issue, i) => (
              <div key={i} style={{ marginTop: 8, padding: 8, background: '#fff2f0', borderRadius: 4 }}>
                <Tag color={issue.severity === 'high' ? 'red' : 'orange'}>{issue.severity}</Tag>
                <Text>{issue.message}</Text>
                <div><Text type="secondary">{issue.recommendation}</Text></div>
              </div>
            ))}
          </Card>
        )}
        <Table rowKey={(r, i) => i} columns={caseColumns} dataSource={detailCases} size="small" scroll={{ y: 400 }} />
      </Modal>

      <Modal title="新建批量测试" open={createVisible} onOk={handleCreate} onCancel={() => setCreateVisible(false)} width={640}>
        <Form form={form} layout="vertical" initialValues={{ accuracy_threshold: 95, latency_threshold_ms: 200 }}>
          <Form.Item name="name" label="测试名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="profile_id" label="对话方案" rules={[{ required: true }]}>
            <Select options={profiles.map(p => ({ label: `${p.name} (${p.llm_provider})`, value: p.id }))} />
          </Form.Item>
          <Space>
            <Form.Item name="accuracy_threshold" label="准确率阈值(%)"><InputNumber min={0} max={100} /></Form.Item>
            <Form.Item name="latency_threshold_ms" label="延迟阈值(ms)"><InputNumber min={0} /></Form.Item>
          </Space>
          <Form.Item name="test_cases_text" label="测试用例 (每行: 输入文本|期望意图|期望域)" rules={[{ required: true }]}>
            <Input.TextArea rows={10} placeholder={"开始烹饪|voice_cmd_start_cooking|command\n红烧肉怎么做||knowledge\n你好||chitchat"} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

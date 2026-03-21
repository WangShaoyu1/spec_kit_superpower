import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Button,
  Card,
  Row,
  Col,
  Tabs,
  Table,
  Tag,
  Space,
  Progress,
  Modal,
  Form,
  Input,
  Select,
  Statistic,
  List,
  Spin,
  message,
  Empty,
  Popconfirm,
  Dropdown,
  InputNumber,
  Switch,
  Steps,
  Checkbox,
} from 'antd';
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ImportOutlined,
  ExportOutlined,
  DeleteOutlined,
  EditOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  BarChartOutlined,
  BulbOutlined,
  WarningOutlined,
  ThunderboltOutlined,
  DownOutlined,
  AppstoreOutlined,
  HeatMapOutlined,
  FlagOutlined,
} from '@ant-design/icons';
import useBatchTestStore from '../../stores/batchTestStore';
import { intentLibraryApi } from '../../services/intentLibraryApi';

const { Title, Text } = Typography;

const STATUS_TAG = {
  draft: { color: 'default', label: '草稿' },
  ready: { color: 'blue', label: '就绪' },
  running: { color: 'processing', label: '运行中' },
  completed: { color: 'success', label: '已完成' },
  failed: { color: 'error', label: '失败' },
};

const DOMAIN_OPTIONS = [
  { value: 'command', label: '指令 (command)' },
  { value: 'knowledge', label: '知识 (knowledge)' },
  { value: 'chitchat', label: '闲聊 (chitchat)' },
];

const FAILURE_LABELS = {
  timeout: '超时 / 执行错误',
  intent_mismatch: '意图不一致',
  domain_mismatch: '域不一致',
  slot_error: '槽位错误',
  low_confidence: '低置信度',
};

function GenerateCaseCostHint({ form }) {
  const names = Form.useWatch('intent_names', form) || [];
  const samples = Form.useWatch('samples_per_intent', form) ?? 5;
  const ink = Form.useWatch('include_knowledge', form);
  const ich = Form.useWatch('include_chitchat', form);
  const base = (Array.isArray(names) ? names.length : 0) * (samples || 0);
  const extraK = ink ? Math.min(8, samples || 5) : 0;
  const extraC = ich ? Math.min(8, samples || 5) : 0;
  const est = base + extraK + extraC;
  return (
    <Card size="small" variant="borderless" style={{ background: 'var(--color-fill)', borderRadius: 12 }}>
      <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
        估算生成条数：<Text strong style={{ fontFamily: 'var(--font-mono)', color: '#1677ff' }}>{est}</Text>（约{' '}
        {est} 次文案合成调用，实际以服务端为准）
      </Text>
    </Card>
  );
}

export default function BatchTestDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('cases');
  const [caseModalOpen, setCaseModalOpen] = useState(false);
  const [editingCase, setEditingCase] = useState(null);
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [importText, setImportText] = useState('');
  const [genModalOpen, setGenModalOpen] = useState(false);
  const [genSubmitting, setGenSubmitting] = useState(false);
  const [genIntentOptions, setGenIntentOptions] = useState([]);
  const [caseForm] = Form.useForm();
  const [genForm] = Form.useForm();
  const fileInputRef = useRef(null);

  const {
    currentBatch,
    detailLoading,
    cases,
    casesTotal,
    casesPage,
    casesLoading,
    runs,
    runsTotal,
    runsPage,
    runsLoading,
    analysis,
    analysisLoading,
    executing,
    fetchDetail,
    fetchCases,
    addCase,
    updateCase,
    deleteCase,
    importCases,
    exportCases,
    executeBatch,
    fetchRuns,
    fetchAnalysis,
    triggerAnalysis,
    generateCases,
    setCasesPage,
    setRunsPage,
    clearDetail,
  } = useBatchTestStore();

  useEffect(() => {
    fetchDetail(id);
    fetchCases(id);
    return () => clearDetail();
  }, [id, fetchDetail, fetchCases, clearDetail]);

  useEffect(() => {
    if (activeTab === 'runs') fetchRuns(id);
    if (activeTab === 'analysis') fetchAnalysis(id);
  }, [activeTab, id, fetchRuns, fetchAnalysis]);

  useEffect(() => {
    fetchCases(id);
  }, [casesPage, id, fetchCases]);

  useEffect(() => {
    if (activeTab === 'runs') fetchRuns(id);
  }, [runsPage, activeTab, id, fetchRuns]);

  useEffect(() => {
    if (!genModalOpen) return;
    let cancelled = false;
    (async () => {
      const names = new Set();
      try {
        const libRes = await intentLibraryApi.listLibraries({ page: 1, page_size: 50 });
        const libData = libRes.data;
        const libs = libData?.items || libData || [];
        for (const lib of libs) {
          const dsRes = await intentLibraryApi.listDatasets(lib.id, { page: 1, page_size: 30 });
          const dsData = dsRes.data;
          const datasets = dsData?.items || dsData || [];
          for (const ds of datasets) {
            const intRes = await intentLibraryApi.listIntents(ds.id, { page: 1, page_size: 500 });
            const intData = intRes.data;
            const intents = intData?.items || intData || [];
            for (const it of intents) {
              const n = it.name || it.intent_name || it.label;
              if (n) names.add(String(n));
            }
          }
        }
      } catch {
        /* ignore */
      }
      if (!cancelled) setGenIntentOptions([...names].sort());
    })();
    return () => {
      cancelled = true;
    };
  }, [genModalOpen]);

  const handleExecute = useCallback(async () => {
    try {
      await executeBatch(id);
      message.success('执行完成');
      await fetchDetail(id);
      fetchRuns(id);
    } catch (err) {
      message.error(err?.message || '执行失败');
    }
  }, [id, executeBatch, fetchRuns, fetchDetail]);

  const handleAddCase = useCallback(() => {
    setEditingCase(null);
    caseForm.resetFields();
    setCaseModalOpen(true);
  }, [caseForm]);

  const handleEditCase = useCallback(
    (record) => {
      setEditingCase(record);
      caseForm.setFieldsValue({
        input_text: record.input_text,
        expected_intent: record.expected_intent,
        expected_domain: record.expected_domain,
        expected_slots: record.expected_slots ? JSON.stringify(record.expected_slots) : '{}',
      });
      setCaseModalOpen(true);
    },
    [caseForm],
  );

  const handleCaseSubmit = useCallback(async () => {
    try {
      const values = await caseForm.validateFields();
      let slots = {};
      if (values.expected_slots) {
        try {
          slots = JSON.parse(values.expected_slots);
        } catch {
          message.error('期望槽位必须是合法的 JSON');
          return;
        }
      }
      const payload = { ...values, expected_slots: slots };
      if (editingCase) {
        await updateCase(id, editingCase.id, payload);
        message.success('更新成功');
      } else {
        await addCase(id, payload);
        message.success('添加成功');
      }
      setCaseModalOpen(false);
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '操作失败');
    }
  }, [caseForm, editingCase, id, addCase, updateCase]);

  const handleDeleteCase = useCallback(
    async (caseId) => {
      try {
        await deleteCase(id, caseId);
        message.success('删除成功');
      } catch (err) {
        message.error(err?.message || '删除失败');
      }
    },
    [id, deleteCase],
  );

  const handleImport = useCallback(async () => {
    try {
      const parsed = JSON.parse(importText);
      const items = Array.isArray(parsed) ? parsed : parsed.cases || [];
      if (!items.length) {
        message.error('未找到有效用例');
        return;
      }
      const res = await importCases(id, items);
      message.success(`成功导入 ${res?.imported || items.length} 条用例`);
      setImportModalOpen(false);
      setImportText('');
    } catch (err) {
      if (err instanceof SyntaxError) {
        message.error('JSON 格式不正确');
      } else {
        message.error(err?.message || '导入失败');
      }
    }
  }, [importText, id, importCases]);

  const handleFileImport = useCallback(
    (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (evt) => {
        setImportText(evt.target.result);
        setImportModalOpen(true);
      };
      reader.readAsText(file);
      e.target.value = '';
    },
    [],
  );

  const downloadBlob = useCallback((blob, filename) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  const handleExportJson = useCallback(async () => {
    try {
      const data = await exportCases(id);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      downloadBlob(blob, `batch-${id}-cases.json`);
    } catch (err) {
      message.error(err?.message || '导出失败');
    }
  }, [id, exportCases, downloadBlob]);

  const handleExportCsv = useCallback(async () => {
    try {
      const data = await exportCases(id);
      const bom = '\uFEFF';
      const rows = (Array.isArray(data) ? data : data?.cases || []).map((r) => ({
        input_text: r.input_text ?? '',
        expected_intent: r.expected_intent ?? '',
        expected_domain: r.expected_domain ?? '',
        expected_slots: JSON.stringify(r.expected_slots ?? {}),
      }));
      const header = 'input_text,expected_intent,expected_domain,expected_slots';
      const lines = [header, ...rows.map((r) => [r.input_text, r.expected_intent, r.expected_domain, r.expected_slots].join(','))];
      const blob = new Blob([bom + lines.join('\n')], { type: 'text/csv;charset=utf-8' });
      downloadBlob(blob, `batch-${id}-cases.csv`);
    } catch (err) {
      message.error(err?.message || '导出失败');
    }
  }, [id, exportCases, downloadBlob]);

  const openGenModal = useCallback(() => {
    genForm.resetFields();
    genForm.setFieldsValue({
      intent_names: [],
      samples_per_intent: 5,
      include_knowledge: false,
      include_chitchat: false,
    });
    setGenModalOpen(true);
  }, [genForm]);

  const handleGenSubmit = useCallback(async () => {
    try {
      const v = await genForm.validateFields();
      const names = v.intent_names || [];
      if (!names.length) {
        message.warning('请至少选择一个意图');
        return;
      }
      setGenSubmitting(true);
      await generateCases(id, {
        intent_names: names,
        samples_per_intent: v.samples_per_intent ?? 5,
        include_knowledge: !!v.include_knowledge,
        include_chitchat: !!v.include_chitchat,
      });
      message.success('用例已生成');
      setGenModalOpen(false);
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '生成失败');
    } finally {
      setGenSubmitting(false);
    }
  }, [genForm, id, generateCases]);

  const handleTriggerAnalysis = useCallback(async () => {
    try {
      await triggerAnalysis(id);
      await fetchDetail(id);
      message.success('分析完成');
    } catch (err) {
      message.error(err?.message || '分析失败');
    }
  }, [id, triggerAnalysis, fetchDetail]);

  const exportMenuItems = useMemo(
    () => [
      { key: 'json', label: '导出 JSON', onClick: handleExportJson },
      { key: 'csv', label: '导出 CSV (Excel 可打开)', onClick: handleExportCsv },
    ],
    [handleExportJson, handleExportCsv],
  );

  const caseColumns = useMemo(
    () => [
      {
        title: '#',
        dataIndex: 'sort_order',
        key: 'sort_order',
        width: 60,
        render: (v, _, idx) => <Text type="secondary">{idx + 1}</Text>,
      },
      {
        title: '输入文本',
        dataIndex: 'input_text',
        key: 'input_text',
        ellipsis: true,
      },
      {
        title: '期望意图',
        dataIndex: 'expected_intent',
        key: 'expected_intent',
        width: 150,
        render: (v) => v ? <Tag color="blue">{v}</Tag> : <Text type="secondary">-</Text>,
      },
      {
        title: '期望域',
        dataIndex: 'expected_domain',
        key: 'expected_domain',
        width: 120,
        render: (v) => v ? <Tag>{v}</Tag> : <Text type="secondary">-</Text>,
      },
      {
        title: '操作',
        key: 'actions',
        width: 120,
        render: (_, record) => (
          <Space size={4}>
            <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditCase(record)} />
            <Popconfirm title="确定删除？" onConfirm={() => handleDeleteCase(record.id)}>
              <Button type="link" size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [handleEditCase, handleDeleteCase],
  );

  const runColumns = useMemo(
    () => [
      {
        title: '输入',
        dataIndex: 'input_text',
        key: 'input_text',
        ellipsis: true,
      },
      {
        title: '期望意图',
        dataIndex: 'expected_intent',
        key: 'expected_intent',
        width: 130,
        render: (v) => v || '-',
      },
      {
        title: '实际意图',
        dataIndex: 'actual_intent',
        key: 'actual_intent',
        width: 130,
        render: (v, r) => {
          if (!v) return '-';
          const hit = r.is_intent_hit;
          return <Tag color={hit ? 'success' : hit === false ? 'error' : 'default'}>{v}</Tag>;
        },
      },
      {
        title: '域',
        dataIndex: 'actual_domain',
        key: 'actual_domain',
        width: 100,
        render: (v, r) => {
          if (!v) return '-';
          const hit = r.is_domain_hit;
          return <Tag color={hit ? 'success' : hit === false ? 'error' : 'default'}>{v}</Tag>;
        },
      },
      {
        title: '置信度',
        dataIndex: 'confidence',
        key: 'confidence',
        width: 90,
        align: 'center',
        render: (v) =>
          v != null ? (
            <Text style={{ fontFamily: 'var(--font-mono)' }}>{(v * 100).toFixed(1)}%</Text>
          ) : (
            '-'
          ),
      },
      {
        title: '延迟',
        dataIndex: 'latency_ms',
        key: 'latency_ms',
        width: 80,
        align: 'center',
        render: (v) =>
          v != null ? (
            <Text
              type={v > 500 ? 'danger' : v > 200 ? 'warning' : undefined}
              style={{ fontFamily: 'var(--font-mono)' }}
            >
              {v}ms
            </Text>
          ) : (
            '-'
          ),
      },
      {
        title: '结果',
        key: 'result',
        width: 70,
        align: 'center',
        render: (_, r) => {
          if (r.error_message) return <Tag color="error">错误</Tag>;
          if (r.is_intent_hit) return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />;
          if (r.is_intent_hit === false) return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 16 }} />;
          return <Text type="secondary">-</Text>;
        },
      },
    ],
    [],
  );

  if (detailLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 120 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!currentBatch) {
    return (
      <Empty description="未找到批量测试">
        <Button onClick={() => navigate('/batch-test')}>返回列表</Button>
      </Empty>
    );
  }

  const batch = currentBatch;
  const statusCfg = STATUS_TAG[batch.status] || { color: 'default', label: batch.status };
  const progress =
    batch.total_cases > 0 ? Math.round((batch.completed_cases / batch.total_cases) * 100) : 0;
  const canExecute = ['ready', 'completed', 'failed'].includes(batch.status) && batch.total_cases > 0;
  const f1Score =
    batch.precision_score != null &&
    batch.recall_score != null &&
    batch.precision_score + batch.recall_score > 0
      ? (2 * batch.precision_score * batch.recall_score) / (batch.precision_score + batch.recall_score)
      : null;

  const cardSurface = {
    borderRadius: 12,
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Space align="center" size={12}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/batch-test')} />
          <div>
            <Space align="center" size={8}>
              <Title level={4} style={{ margin: 0 }}>
                {batch.name}
              </Title>
              <Tag color={statusCfg.color}>{statusCfg.label}</Tag>
            </Space>
            {batch.description && (
              <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)', display: 'block', marginTop: 2 }}>
                {batch.description}
              </Text>
            )}
          </div>
        </Space>
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={handleExecute}
          loading={executing}
          disabled={!canExecute}
        >
          执行测试
        </Button>
      </div>

      {/* Info card — 8 overview metrics */}
      <Card variant="borderless" style={cardSurface} styles={{ body: { padding: '20px 24px' } }}>
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={8} md={6} lg={3}>
            <Statistic title="总用例" value={batch.total_cases} />
          </Col>
          <Col xs={12} sm={8} md={6} lg={3}>
            <Statistic title="已完成" value={batch.completed_cases} />
          </Col>
          <Col xs={12} sm={8} md={6} lg={3}>
            <Statistic
              title="准确率"
              value={batch.accuracy != null ? (batch.accuracy * 100).toFixed(1) : '-'}
              suffix={batch.accuracy != null ? '%' : ''}
            />
          </Col>
          <Col xs={12} sm={8} md={6} lg={3}>
            <Statistic
              title="精确率"
              value={batch.precision_score != null ? (batch.precision_score * 100).toFixed(1) : '-'}
              suffix={batch.precision_score != null ? '%' : ''}
            />
          </Col>
          <Col xs={12} sm={8} md={6} lg={3}>
            <Statistic
              title="召回率"
              value={batch.recall_score != null ? (batch.recall_score * 100).toFixed(1) : '-'}
              suffix={batch.recall_score != null ? '%' : ''}
            />
          </Col>
          <Col xs={12} sm={8} md={6} lg={3}>
            <Statistic
              title="F1-Score"
              value={f1Score != null ? (f1Score * 100).toFixed(1) : '-'}
              suffix={f1Score != null ? '%' : ''}
            />
          </Col>
          <Col xs={12} sm={8} md={6} lg={3}>
            <Statistic
              title="P99 延迟"
              value={batch.p99_latency_ms != null ? batch.p99_latency_ms : '-'}
              suffix={batch.p99_latency_ms != null ? 'ms' : ''}
            />
          </Col>
          <Col xs={12} sm={8} md={6} lg={3}>
            <Text type="secondary" style={{ display: 'block', marginBottom: 8, fontSize: 'var(--font-size-xs)' }}>
              执行进度
            </Text>
            <Progress
              percent={progress}
              status={batch.status === 'running' ? 'active' : batch.status === 'failed' ? 'exception' : undefined}
              size="small"
            />
          </Col>
        </Row>
      </Card>

      {/* Tabs */}
      <Card styles={{ body: { padding: 0 } }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          style={{ padding: '0 24px' }}
          items={[
            {
              key: 'cases',
              label: '用例管理',
              children: (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '0 0 16px' }}>
                    <Button icon={<PlusOutlined />} onClick={handleAddCase}>
                      添加用例
                    </Button>
                    <Button
                      icon={<ImportOutlined />}
                      onClick={() => setImportModalOpen(true)}
                    >
                      导入
                    </Button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".json"
                      style={{ display: 'none' }}
                      onChange={handleFileImport}
                    />
                    <Button
                      icon={<ImportOutlined />}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      从文件导入
                    </Button>
                    <Button type="primary" ghost icon={<ThunderboltOutlined />} onClick={openGenModal}>
                      AI 生成用例
                    </Button>
                    <Dropdown menu={{ items: exportMenuItems }} trigger={['click']}>
                      <Button icon={<ExportOutlined />}>
                        导出 <DownOutlined />
                      </Button>
                    </Dropdown>
                  </div>
                  <Table
                    rowKey="id"
                    columns={caseColumns}
                    dataSource={cases}
                    loading={casesLoading}
                    scroll={{ x: 1000 }}
                    pagination={{
                      current: casesPage,
                      pageSize: 50,
                      total: casesTotal,
                      showTotal: (t) => `共 ${t} 条`,
                      onChange: (p) => setCasesPage(p),
                    }}
                    locale={{
                      emptyText: (
                        <Empty
                          image={Empty.PRESENTED_IMAGE_SIMPLE}
                          description="暂无测试用例"
                          style={{ padding: '32px 0' }}
                        >
                          <Space>
                            <Button icon={<PlusOutlined />} onClick={handleAddCase}>
                              手动添加
                            </Button>
                            <Button icon={<ImportOutlined />} onClick={() => setImportModalOpen(true)}>
                              JSON 导入
                            </Button>
                          </Space>
                        </Empty>
                      ),
                    }}
                  />
                </div>
              ),
            },
            {
              key: 'runs',
              label: '执行结果',
              children: (
                <Table
                  rowKey="id"
                  columns={runColumns}
                  dataSource={runs}
                  loading={runsLoading}
                  scroll={{ x: 1000 }}
                  rowClassName={(record) => (record.is_intent_hit === false ? 'ant-table-row-error' : '')}
                  pagination={{
                    current: runsPage,
                    pageSize: 50,
                    total: runsTotal,
                    showTotal: (t) => `共 ${t} 条`,
                    onChange: (p) => setRunsPage(p),
                  }}
                  locale={{
                    emptyText: (
                      <Empty
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                        description="尚未执行测试"
                        style={{ padding: '32px 0' }}
                      />
                    ),
                  }}
                />
              ),
            },
            {
              key: 'analysis',
              label: '智能分析',
              children: <AnalysisTab
                analysis={analysis}
                loading={analysisLoading}
                onTrigger={handleTriggerAnalysis}
                batchStatus={batch.status}
              />,
            },
          ]}
        />
      </Card>

      {/* Case add/edit modal */}
      <Modal
        open={caseModalOpen}
        title={editingCase ? '编辑用例' : '添加用例'}
        onCancel={() => setCaseModalOpen(false)}
        onOk={handleCaseSubmit}
        okText={editingCase ? '保存' : '添加'}
        cancelText="取消"
        width={560}
        centered
        destroyOnHidden
      >
        <Form form={caseForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="input_text"
            label="输入文本"
            rules={[{ required: true, message: '请输入测试文本' }]}
          >
            <Input.TextArea rows={2} placeholder="用户输入文本" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="expected_intent" label="期望意图">
                <Input placeholder="set_timer" maxLength={128} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="expected_domain" label="期望域">
                <Select placeholder="选择域" allowClear options={DOMAIN_OPTIONS} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="expected_slots" label="期望槽位 (JSON)">
            <Input.TextArea rows={2} placeholder='{"duration": "5分钟"}' />
          </Form.Item>
        </Form>
      </Modal>

      {/* Import modal */}
      <Modal
        open={importModalOpen}
        title="导入测试用例"
        onCancel={() => { setImportModalOpen(false); setImportText(''); }}
        onOk={handleImport}
        okText="导入"
        cancelText="取消"
        width={640}
        centered
      >
        <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
          粘贴 JSON 数组，每个元素包含 input_text（必填）、expected_intent、expected_domain、expected_slots
        </Text>
        <Input.TextArea
          rows={12}
          value={importText}
          onChange={(e) => setImportText(e.target.value)}
          placeholder={`[\n  {"input_text": "设定5分钟计时器", "expected_intent": "set_timer", "expected_domain": "command"},\n  {"input_text": "今天天气怎么样", "expected_intent": "weather_query", "expected_domain": "knowledge"}\n]`}
          style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}
        />
      </Modal>

      <Modal
        title="AI 生成用例"
        open={genModalOpen}
        onCancel={() => setGenModalOpen(false)}
        onOk={handleGenSubmit}
        confirmLoading={genSubmitting}
        width={680}
        okText="生成"
        cancelText="取消"
        centered
        destroyOnHidden
      >
        <Form form={genForm} layout="vertical" style={{ marginTop: 8 }}>
          <GenerateCaseCostHint form={genForm} />
          <Form.Item
            name="intent_names"
            label="覆盖意图"
            rules={[
              {
                validator: (_, v) =>
                  Array.isArray(v) && v.length > 0 ? Promise.resolve() : Promise.reject(new Error('请至少选择一个意图')),
              },
            ]}
          >
            {!genIntentOptions.length ? (
              <Empty description="未从意图库加载到意图，仍可手动添加用例" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : (
              <div
                style={{
                  maxHeight: 240,
                  overflow: 'auto',
                  border: '1px solid var(--color-border-light)',
                  borderRadius: 12,
                  padding: 'var(--space-3)',
                }}
              >
                <Checkbox.Group style={{ width: '100%' }}>
                  <Row gutter={[8, 4]}>
                    {genIntentOptions.map((n) => (
                      <Col xs={24} sm={12} key={n}>
                        <Checkbox value={n}>{n}</Checkbox>
                      </Col>
                    ))}
                  </Row>
                </Checkbox.Group>
              </div>
            )}
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="samples_per_intent" label="每意图样本数" rules={[{ required: true, type: 'number', min: 1 }]}>
                <InputNumber min={1} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="include_knowledge" label="知识边界" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="include_chitchat" label="闲聊边界" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
}

function ConfusionHeatGrid({ confusion }) {
  const { rows, cols, matrix, maxV } = useMemo(() => {
    const exp = new Set();
    const act = new Set();
    (confusion || []).forEach((c) => {
      exp.add(c.expected);
      act.add(c.actual);
    });
    const r = [...exp].sort();
    const a = [...act].sort();
    const m = {};
    let max = 0;
    (confusion || []).forEach((c) => {
      const k = `${c.expected}||${c.actual}`;
      m[k] = (m[k] || 0) + c.count;
      max = Math.max(max, m[k]);
    });
    return { rows: r, cols: a, matrix: m, maxV: max };
  }, [confusion]);

  const cell = (e, ca) => matrix[`${e}||${ca}`] || 0;
  const bg = (v) => {
    if (!v || !maxV) return 'var(--color-fill)';
    const t = v / maxV;
    return `rgba(255, 77, 79, ${0.08 + t * 0.5})`;
  };

  if (!rows.length || !cols.length) {
    return <Text type="secondary">暂无混淆数据</Text>;
  }

  return (
    <div style={{ overflow: 'auto', maxWidth: '100%' }}>
      <table style={{ borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)', width: '100%' }}>
        <thead>
          <tr>
            <th
              style={{
                padding: 8,
                border: '1px solid var(--color-border-light)',
                background: 'var(--color-fill)',
              }}
            >
              期望 \ 实际
            </th>
            {cols.map((c) => (
              <th
                key={c}
                style={{
                  padding: 8,
                  border: '1px solid var(--color-border-light)',
                  background: 'var(--color-fill)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((e) => (
            <tr key={e}>
              <td
                style={{
                  padding: 8,
                  fontWeight: 600,
                  border: '1px solid var(--color-border-light)',
                  background: 'var(--color-fill)',
                }}
              >
                {e}
              </td>
              {cols.map((a) => {
                const v = cell(e, a);
                return (
                  <td
                    key={a}
                    style={{
                      padding: 8,
                      textAlign: 'center',
                      border: '1px solid var(--color-border-light)',
                      background: bg(v),
                      fontFamily: 'var(--font-mono)',
                      minWidth: 48,
                    }}
                  >
                    {v || '—'}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const analysisCardStyle = {
  borderRadius: 12,
  boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
};

const INTENT_RANK_COLUMNS = [
  { title: '意图', dataIndex: 'intent', key: 'intent', render: (v) => <Tag color="blue">{v}</Tag> },
  { title: '正确/总数', key: 'ct', render: (_, r) => `${r.correct} / ${r.total}` },
  {
    title: '准确率',
    dataIndex: 'accuracy',
    key: 'accuracy',
    align: 'center',
    render: (v) => (
      <Text
        style={{
          fontFamily: 'var(--font-mono)',
          color: v >= 0.95 ? '#52c41a' : v >= 0.9 ? '#faad14' : '#ff4d4f',
        }}
      >
        {v != null ? `${(v * 100).toFixed(1)}%` : '-'}
      </Text>
    ),
  },
];

function AnalysisTab({ analysis, loading, onTrigger, batchStatus }) {
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
        <Spin />
      </div>
    );
  }

  if (!analysis) {
    return (
      <Empty description="暂无分析报告" style={{ padding: '48px 0' }}>
        <Button
          type="primary"
          icon={<BarChartOutlined />}
          onClick={onTrigger}
          disabled={!['completed', 'failed'].includes(batchStatus)}
        >
          生成分析报告
        </Button>
      </Empty>
    );
  }

  const {
    summary = {},
    confusion_top_n = [],
    slot_error_distribution = [],
    low_score_samples = [],
    recommendations = [],
  } = analysis;

  const intentRank = summary.intent_accuracy_rank || [];
  const failureAttr = summary.failure_attribution || {};

  const recSteps = recommendations.map((text, i) => {
    const color = i === 0 ? '#ff4d4f' : i === 1 ? '#faad14' : '#1677ff';
    const pri = i === 0 ? 'P0' : i === 1 ? 'P1' : 'P2';
    return {
      title: (
        <Space>
          <Tag color={i === 0 ? 'red' : i === 1 ? 'orange' : 'blue'}>{pri}</Tag>
          <Text>{text}</Text>
        </Space>
      ),
      icon: <BulbOutlined style={{ color }} />,
    };
  });

  const metricCards = (
    <Row gutter={[16, 16]}>
      <Col xs={12} md={8} lg={6}>
        <Card variant="borderless" size="small" style={analysisCardStyle}>
          <Statistic title="总用例" value={summary.total || 0} />
        </Card>
      </Col>
      <Col xs={12} md={8} lg={6}>
        <Card variant="borderless" size="small" style={analysisCardStyle}>
          <Statistic title="通过" value={summary.passed || 0} valueStyle={{ color: '#52c41a' }} />
        </Card>
      </Col>
      <Col xs={12} md={8} lg={6}>
        <Card variant="borderless" size="small" style={analysisCardStyle}>
          <Statistic title="失败" value={summary.failed || 0} valueStyle={{ color: '#ff4d4f' }} />
        </Card>
      </Col>
      <Col xs={12} md={8} lg={6}>
        <Card variant="borderless" size="small" style={analysisCardStyle}>
          <Statistic
            title="准确率"
            value={summary.accuracy != null ? (summary.accuracy * 100).toFixed(1) : '-'}
            suffix={summary.accuracy != null ? '%' : ''}
            valueStyle={{
              color:
                summary.accuracy >= 0.95 ? '#52c41a' : summary.accuracy >= 0.9 ? '#faad14' : '#ff4d4f',
            }}
          />
        </Card>
      </Col>
      <Col xs={12} md={8} lg={6}>
        <Card variant="borderless" size="small" style={analysisCardStyle}>
          <Statistic
            title="F1-Score"
            value={summary.f1_score != null ? (summary.f1_score * 100).toFixed(1) : '-'}
            suffix={summary.f1_score != null ? '%' : ''}
          />
        </Card>
      </Col>
      <Col xs={12} md={8} lg={6}>
        <Card variant="borderless" size="small" style={analysisCardStyle}>
          <Statistic title="平均延迟" value={summary.avg_latency || 0} suffix="ms" />
        </Card>
      </Col>
      <Col xs={12} md={8} lg={6}>
        <Card variant="borderless" size="small" style={analysisCardStyle}>
          <Statistic title="P99 延迟" value={summary.p99_latency ?? 0} suffix="ms" />
        </Card>
      </Col>
      <Col xs={12} md={8} lg={6}>
        <Card variant="borderless" size="small" style={analysisCardStyle}>
          <Statistic
            title="错误数"
            value={summary.errors || 0}
            valueStyle={summary.errors > 0 ? { color: '#ff4d4f' } : undefined}
          />
        </Card>
      </Col>
    </Row>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', padding: '0 0 var(--space-6)' }}>
      <Tabs
        items={[
          {
            key: 'overview',
            label: (
              <Space>
                <AppstoreOutlined />
                总体结论
              </Space>
            ),
            children: (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
                {metricCards}
                {slot_error_distribution.length > 0 && (
                  <Card variant="borderless" title="槽位错误分布" style={analysisCardStyle}>
                    <Table
                      rowKey="slot_key"
                      dataSource={slot_error_distribution}
                      pagination={false}
                      size="small"
                      columns={[
                        { title: '槽位', dataIndex: 'slot_key', key: 'slot_key' },
                        { title: '缺失', dataIndex: 'missing_count', width: 90, align: 'center' },
                        { title: '错误', dataIndex: 'wrong_count', width: 90, align: 'center' },
                      ]}
                    />
                  </Card>
                )}
                {low_score_samples.length > 0 && (
                  <Card
                    variant="borderless"
                    title={
                      <Space>
                        <WarningOutlined style={{ color: '#ff4d4f' }} />
                        低置信度样本
                      </Space>
                    }
                    style={analysisCardStyle}
                  >
                    <Table
                      rowKey="case_id"
                      dataSource={low_score_samples}
                      pagination={false}
                      size="small"
                      columns={[
                        { title: '输入', dataIndex: 'input', ellipsis: true },
                        { title: '期望', dataIndex: 'expected', width: 120 },
                        { title: '实际', dataIndex: 'actual', width: 120 },
                        {
                          title: '置信度',
                          dataIndex: 'confidence',
                          width: 90,
                          align: 'center',
                          render: (v) => (
                            <Text type="danger" style={{ fontFamily: 'var(--font-mono)' }}>
                              {v != null ? `${(v * 100).toFixed(1)}%` : '-'}
                            </Text>
                          ),
                        },
                      ]}
                    />
                  </Card>
                )}
              </div>
            ),
          },
          {
            key: 'rank',
            label: '意图准确率排名',
            children: (
              <Card variant="borderless" style={analysisCardStyle}>
                {intentRank.length ? (
                  <Table
                    rowKey="intent"
                    dataSource={[...intentRank].sort((a, b) => a.accuracy - b.accuracy)}
                    pagination={false}
                    size="small"
                    columns={INTENT_RANK_COLUMNS}
                  />
                ) : (
                  <Text type="secondary">暂无分意图统计（需用例含期望意图并执行测试）</Text>
                )}
              </Card>
            ),
          },
          {
            key: 'confusion',
            label: (
              <Space>
                <HeatMapOutlined />
                混淆矩阵
              </Space>
            ),
            children: (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                <Card variant="borderless" title="热力图（基于混淆对）" style={analysisCardStyle}>
                  <ConfusionHeatGrid confusion={confusion_top_n} />
                </Card>
                {confusion_top_n.length > 0 && (
                  <Card variant="borderless" title="Top 混淆明细" style={analysisCardStyle}>
                    <Table
                      rowKey={(r, i) => i}
                      dataSource={confusion_top_n}
                      pagination={false}
                      size="small"
                      columns={[
                        {
                          title: '期望意图',
                          dataIndex: 'expected',
                          render: (v) => <Tag color="blue">{v}</Tag>,
                        },
                        {
                          title: '实际意图',
                          dataIndex: 'actual',
                          render: (v) => <Tag color="error">{v}</Tag>,
                        },
                        { title: '次数', dataIndex: 'count', width: 90, align: 'center' },
                      ]}
                    />
                  </Card>
                )}
                {!confusion_top_n.length && <Text type="secondary">暂无混淆对数据</Text>}
              </div>
            ),
          },
          {
            key: 'failure',
            label: (
              <Space>
                <FlagOutlined />
                失败归因
              </Space>
            ),
            children: (
              <Row gutter={[16, 16]}>
                {Object.entries(FAILURE_LABELS).map(([key, label]) => {
                  const block = failureAttr[key] || { count: 0, samples: [] };
                  if (!block.count) return null;
                  return (
                    <Col xs={24} md={12} key={key}>
                      <Card variant="borderless" title={`${label}（${block.count}）`} style={analysisCardStyle}>
                        <List
                          size="small"
                          dataSource={block.samples || []}
                          renderItem={(s) => (
                            <List.Item style={{ paddingLeft: 0 }}>
                              <Text ellipsis style={{ maxWidth: '100%' }}>
                                {s.input || '—'}（期:{s.expected_intent || '-'} / 实:{s.actual_intent || '-'}）
                              </Text>
                            </List.Item>
                          )}
                        />
                      </Card>
                    </Col>
                  );
                })}
                {!Object.values(failureAttr).some((b) => b?.count > 0) && (
                  <Col span={24}>
                    <Text type="secondary">暂无失败样本分类（可能全部通过或需重新生成分析）</Text>
                  </Col>
                )}
              </Row>
            ),
          },
          {
            key: 'recs',
            label: (
              <Space>
                <BulbOutlined style={{ color: '#faad14' }} />
                优化建议
              </Space>
            ),
            children: (
              <Card variant="borderless" style={analysisCardStyle}>
                {recSteps.length > 0 ? (
                  <Steps direction="vertical" items={recSteps} />
                ) : (
                  <Text type="secondary">暂无建议</Text>
                )}
              </Card>
            ),
          },
        ]}
      />

      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button icon={<BarChartOutlined />} onClick={onTrigger}>
          重新生成分析
        </Button>
      </div>
    </div>
  );
}

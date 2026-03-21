import { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Button,
  Input,
  Select,
  Table,
  Tag,
  Card,
  Row,
  Col,
  Space,
  Modal,
  Form,
  message,
  Empty,
  Steps,
  Radio,
  InputNumber,
  Switch,
  Upload,
  Transfer,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  ExperimentOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  EyeOutlined,
  DeleteOutlined,
  ReloadOutlined,
  DownloadOutlined,
  RedoOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import useBatchTestStore from '../../stores/batchTestStore';
import { profileApi } from '../../services/profileApi';
import { intentLibraryApi } from '../../services/intentLibraryApi';
import DangerConfirmModal from '../../components/DangerConfirmModal';

const { Title, Text } = Typography;

const ACCURACY_THRESHOLD = 0.85;

const CASE_SOURCE = { MANUAL: 'manual', LLM: 'llm', EXCEL: 'excel' };

const STATUS_OPTIONS = [
  { value: '', label: '全部状态' },
  { value: 'draft', label: '草稿' },
  { value: 'ready', label: '就绪' },
  { value: 'running', label: '运行中' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' },
];

const PASS_OPTIONS = [
  { value: '', label: '全部达标状态' },
  { value: 'pass', label: '达标' },
  { value: 'fail', label: '未达标' },
];

const STATUS_TAG = {
  draft: { color: 'default', label: '草稿' },
  ready: { color: 'blue', label: '就绪' },
  running: { color: 'processing', label: '运行中' },
  completed: { color: 'success', label: '已完成' },
  failed: { color: 'error', label: '失败' },
};

const STAT_CARDS = [
  {
    key: 'total',
    field: 'total',
    label: '测试总数',
    icon: <ExperimentOutlined />,
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  {
    key: 'running',
    field: 'running',
    label: '运行中',
    icon: <PlayCircleOutlined />,
    gradient: 'linear-gradient(135deg, #faad14 0%, #ffc53d 100%)',
  },
  {
    key: 'completed',
    field: 'completed',
    label: '已完成',
    icon: <CheckCircleOutlined />,
    gradient: 'linear-gradient(135deg, #52c41a 0%, #95de64 100%)',
  },
  {
    key: 'below_threshold',
    label: '未达标',
    icon: <WarningOutlined />,
    gradient: 'linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%)',
    computed: true,
  },
];

function parseBatchCsv(text) {
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  if (lines.length < 2) {
    return { error: '至少需要表头与一行数据', rows: [] };
  }
  const headers = lines[0].split(',').map((h) => h.trim().replace(/^"|"$/g, ''));
  const required = 'input_text';
  if (!headers.includes(required)) {
    return { error: `表头必须包含列: ${required}`, rows: [] };
  }
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',').map((c) => c.trim().replace(/^"|"$/g, ''));
    const obj = {};
    headers.forEach((h, j) => {
      obj[h] = cols[j] ?? '';
    });
    if (!obj.input_text) continue;
    let slots = {};
    if (obj.expected_slots) {
      try {
        slots =
          typeof obj.expected_slots === 'string' && obj.expected_slots.trim()
            ? JSON.parse(obj.expected_slots.replace(/""/g, '"'))
            : {};
      } catch {
        return { error: `第 ${i + 1} 行 expected_slots 不是合法 JSON`, rows: [] };
      }
    }
    rows.push({
      input_text: obj.input_text,
      expected_intent: obj.expected_intent || null,
      expected_domain: obj.expected_domain || null,
      expected_slots: slots,
    });
  }
  if (!rows.length) return { error: '没有有效的数据行', rows: [] };
  return { error: null, rows };
}

async function fetchIntentNameOptions() {
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
  return [...names].sort().map((k) => ({ key: k, title: k }));
}

export default function BatchTest() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [modalOpen, setModalOpen] = useState(false);
  const [wizardStep, setWizardStep] = useState(0);
  const [wizardSubmitting, setWizardSubmitting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [profiles, setProfiles] = useState([]);
  const [profileFilter, setProfileFilter] = useState('');
  const [passFilter, setPassFilter] = useState('');
  const [intentTransferData, setIntentTransferData] = useState([]);
  const [transferTargetKeys, setTransferTargetKeys] = useState([]);
  const [excelRows, setExcelRows] = useState([]);
  const [excelError, setExcelError] = useState(null);
  const [reExecTarget, setReExecTarget] = useState(null);
  const [reExecLoading, setReExecLoading] = useState(false);

  const {
    batches,
    loading,
    total,
    page,
    pageSize,
    search,
    statusFilter,
    stats,
    fetchBatches,
    fetchStats,
    createBatch,
    deleteBatch,
    importCases,
    generateCases,
    executeBatch,
    setSearch,
    setStatusFilter,
    setPage,
    setPageSize,
  } = useBatchTestStore();

  useEffect(() => {
    fetchBatches();
    fetchStats();
  }, [fetchBatches, fetchStats, page, pageSize, search, statusFilter]);

  useEffect(() => {
    profileApi
      .listProfiles({ page: 1, page_size: 100 })
      .then((res) => {
        const data = res.data;
        setProfiles(data?.items || data || []);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!modalOpen) return;
    let cancelled = false;
    (async () => {
      const opts = await fetchIntentNameOptions();
      if (!cancelled) setIntentTransferData(opts);
    })();
    return () => {
      cancelled = true;
    };
  }, [modalOpen]);

  const belowThresholdCount = useMemo(() => {
    return batches.filter((b) => {
      if (b.is_pass === false) return true;
      if (b.is_pass === true) return false;
      return b.accuracy != null && b.accuracy < ACCURACY_THRESHOLD;
    }).length;
  }, [batches]);

  const filteredBatches = useMemo(() => {
    let list = batches;
    if (profileFilter) {
      list = list.filter((b) => b.profile_name === profileFilter || b.profile_id === profileFilter);
    }
    if (passFilter === 'pass') {
      list = list.filter((b) => {
        if (b.is_pass != null) return b.is_pass === true;
        return b.accuracy != null && b.accuracy >= ACCURACY_THRESHOLD;
      });
    } else if (passFilter === 'fail') {
      list = list.filter((b) => {
        if (b.is_pass != null) return b.is_pass === false;
        return b.accuracy != null && b.accuracy < ACCURACY_THRESHOLD;
      });
    }
    return list;
  }, [batches, profileFilter, passFilter]);

  const profileOptions = useMemo(() => {
    const fromProfiles = profiles.map((p) => ({ value: p.name || p.id, label: p.name }));
    const fromBatches = [...new Set(batches.map((b) => b.profile_name).filter(Boolean))]
      .filter((name) => !fromProfiles.some((p) => p.value === name))
      .map((name) => ({ value: name, label: name }));
    return [{ value: '', label: '全部方案' }, ...fromProfiles, ...fromBatches];
  }, [profiles, batches]);

  const resetWizard = useCallback(() => {
    setWizardStep(0);
    setTransferTargetKeys([]);
    setExcelRows([]);
    setExcelError(null);
    form.resetFields();
    form.setFieldsValue({
      accuracy_threshold: 95,
      latency_threshold_ms: 2000,
      case_source: CASE_SOURCE.MANUAL,
      llm_samples: 5,
      include_knowledge: false,
      include_chitchat: false,
    });
  }, [form]);

  const openCreate = useCallback(() => {
    resetWizard();
    setModalOpen(true);
  }, [resetWizard]);

  const handleWizardNext = useCallback(async () => {
    try {
      await form.validateFields(['name', 'description', 'profile_id', 'accuracy_threshold', 'latency_threshold_ms']);
      setWizardStep(1);
    } catch {
      /* validation */
    }
  }, [form]);

  const handleWizardCreate = useCallback(async () => {
    try {
      const v = await form.validateFields();
      const src = v.case_source || CASE_SOURCE.MANUAL;
      if (src === CASE_SOURCE.LLM && transferTargetKeys.length === 0) {
        message.warning('请至少选择一个意图');
        return;
      }
      if (src === CASE_SOURCE.EXCEL) {
        if (excelError) {
          message.warning('请先修复 CSV 列校验错误');
          return;
        }
        if (!excelRows.length) {
          message.warning('请上传 CSV 并包含有效数据行');
          return;
        }
      }
      setWizardSubmitting(true);
      const payload = {
        name: v.name,
        description: v.description,
        profile_id: v.profile_id,
        accuracy_threshold: (v.accuracy_threshold ?? 95) / 100,
        latency_threshold_ms: v.latency_threshold_ms ?? 2000,
      };
      const batch = await createBatch(payload);
      const bid = batch?.id;
      if (!bid) throw new Error('创建返回缺少 id');
      if (src === CASE_SOURCE.LLM) {
        await generateCases(bid, {
          intent_names: transferTargetKeys,
          samples_per_intent: v.llm_samples ?? 5,
          include_knowledge: !!v.include_knowledge,
          include_chitchat: !!v.include_chitchat,
        });
      } else if (src === CASE_SOURCE.EXCEL) {
        await importCases(bid, excelRows);
      }
      message.success('创建成功');
      setModalOpen(false);
      resetWizard();
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '操作失败');
    } finally {
      setWizardSubmitting(false);
    }
  }, [
    form,
    transferTargetKeys,
    excelError,
    excelRows,
    createBatch,
    generateCases,
    importCases,
    resetWizard,
  ]);

  const handleDownloadTemplate = useCallback(() => {
    const bom = '\uFEFF';
    const csv =
      `${bom}input_text,expected_intent,expected_domain,expected_slots\n` +
      '设定5分钟计时器,set_timer,command,{}\n';
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'batch-test-template.csv';
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  const handleExcelBeforeUpload = useCallback((file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = String(e.target?.result || '');
      const { error, rows } = parseBatchCsv(text);
      setExcelError(error);
      setExcelRows(rows);
      if (error) message.error(error);
      else message.success(`已解析 ${rows.length} 行`);
    };
    reader.readAsText(file, 'UTF-8');
    return false;
  }, []);

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await deleteBatch(deleteTarget.id);
      message.success('删除成功');
      setDeleteTarget(null);
    } catch (err) {
      message.error(err?.message || '删除失败');
    } finally {
      setDeleteLoading(false);
    }
  }, [deleteTarget, deleteBatch]);

  const handleReExecuteConfirm = useCallback(async () => {
    if (!reExecTarget) return;
    setReExecLoading(true);
    try {
      await executeBatch(reExecTarget.id);
      message.success('已重新执行');
      setReExecTarget(null);
      fetchBatches();
      fetchStats();
    } catch (err) {
      message.error(err?.message || '执行失败');
    } finally {
      setReExecLoading(false);
    }
  }, [reExecTarget, executeBatch, fetchBatches, fetchStats]);

  const handleReset = useCallback(() => {
    setSearch('');
    setStatusFilter('');
    setProfileFilter('');
    setPassFilter('');
  }, [setSearch, setStatusFilter]);

  const renderAccuracy = useCallback((v) => {
    if (v == null) return <Text type="secondary">-</Text>;
    const pct = v * 100;
    let color = '#ff4d4f';
    if (pct >= 95) color = '#52c41a';
    else if (pct >= 90) color = '#faad14';
    return (
      <Text strong style={{ color, fontFamily: 'var(--font-mono)' }}>
        {pct.toFixed(1)}%
      </Text>
    );
  }, []);

  const columns = useMemo(
    () => [
      {
        title: '名称',
        dataIndex: 'name',
        key: 'name',
        ellipsis: true,
        render: (text, record) => (
          <div>
            <Button
              type="link"
              style={{ padding: 0, height: 'auto', fontWeight: 600, display: 'block', textAlign: 'left' }}
              onClick={() => navigate(`/batch-test/${record.id}`)}
            >
              {text}
            </Button>
            <Text
              type="secondary"
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--font-size-sm)',
                display: 'block',
                lineHeight: 1.3,
              }}
            >
              {record.id}
            </Text>
          </div>
        ),
      },
      {
        title: '关联方案',
        dataIndex: 'profile_name',
        key: 'profile_name',
        width: 150,
        render: (val) => val || <Text type="secondary">-</Text>,
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 100,
        render: (status) => {
          const cfg = STATUS_TAG[status] || { color: 'default', label: status };
          return <Tag color={cfg.color}>{cfg.label}</Tag>;
        },
      },
      {
        title: '用例数',
        dataIndex: 'total_cases',
        key: 'total_cases',
        width: 80,
        align: 'center',
        render: (v) => (
          <Text style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{v}</Text>
        ),
      },
      {
        title: '准确率',
        dataIndex: 'accuracy',
        key: 'accuracy',
        width: 100,
        align: 'center',
        render: renderAccuracy,
      },
      {
        title: '达标',
        key: 'is_pass',
        width: 90,
        align: 'center',
        render: (_, record) => {
          const pass =
            record.is_pass != null
              ? record.is_pass
              : record.accuracy != null && record.accuracy >= ACCURACY_THRESHOLD;
          if (record.accuracy == null && record.is_pass == null) {
            return <Text type="secondary">-</Text>;
          }
          return pass ? <Tag color="success">达标</Tag> : <Tag color="error">未达标</Tag>;
        },
      },
      {
        title: '平均耗时',
        key: 'avg_latency',
        width: 100,
        align: 'center',
        render: (_, record) => {
          const val = record.avg_latency_ms ?? record.duration;
          return val != null ? (
            <Text style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-sm)' }}>
              {typeof val === 'number' ? `${val.toFixed(0)}ms` : val}
            </Text>
          ) : (
            <Text type="secondary">-</Text>
          );
        },
      },
      {
        title: '创建时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 170,
        render: (val) => (
          <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)' }}>
            {val ? dayjs(val).format('YYYY-MM-DD HH:mm') : '-'}
          </Text>
        ),
      },
      {
        title: '操作',
        key: 'actions',
        width: 220,
        render: (_, record) => (
          <Space size={4} wrap>
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/batch-test/${record.id}`)}
            >
              详情
            </Button>
            <Button
              type="link"
              size="small"
              icon={<RedoOutlined />}
              disabled={!record.total_cases || record.status === 'running'}
              onClick={() => setReExecTarget(record)}
            >
              重新执行
            </Button>
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => setDeleteTarget(record)}
            >
              删除
            </Button>
          </Space>
        ),
      },
    ],
    [navigate, renderAccuracy],
  );

  const caseSource = Form.useWatch('case_source', form);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={4} style={{ marginBottom: 4 }}>
            批量测试
          </Title>
          <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
            管理批量测试集，执行回归测试并分析 NLU 准确率
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          新建测试
        </Button>
      </div>

      <Row gutter={16}>
        {STAT_CARDS.map((card) => (
          <Col span={6} key={card.key}>
            <Card
              style={{ minWidth: 180, borderRadius: 'var(--radius-lg)', border: 'none', overflow: 'hidden' }}
              styles={{ body: { padding: '20px 24px' } }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: 'var(--radius-lg)',
                    background: card.gradient,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 22,
                    color: '#fff',
                    flexShrink: 0,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  }}
                >
                  {card.icon}
                </div>
                <div>
                  <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)', display: 'block' }}>
                    {card.label}
                  </Text>
                  <Text
                    strong
                    style={{
                      fontSize: 'var(--font-size-2xl)',
                      fontFamily: 'var(--font-mono)',
                      lineHeight: 1.2,
                    }}
                  >
                    {card.computed ? belowThresholdCount : stats[card.field] ?? 0}
                  </Text>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Card style={{ minWidth: 0 }} styles={{ body: { padding: 0 } }}>
        <div
          style={{
            padding: '16px 24px',
            display: 'flex',
            gap: 12,
            flexWrap: 'wrap',
            alignItems: 'center',
            borderBottom: '1px solid var(--color-border-light)',
          }}
        >
          <Input
            placeholder="搜索测试名称..."
            prefix={<SearchOutlined style={{ color: 'var(--color-text-tertiary)' }} />}
            allowClear
            style={{ width: 260 }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            options={STATUS_OPTIONS}
            style={{ width: 140 }}
          />
          <Select
            value={profileFilter}
            onChange={setProfileFilter}
            options={profileOptions}
            style={{ width: 160 }}
            placeholder="关联方案"
          />
          <Select
            value={passFilter}
            onChange={setPassFilter}
            options={PASS_OPTIONS}
            style={{ width: 150 }}
            placeholder="达标状态"
          />
          <Button type="primary" icon={<SearchOutlined />} onClick={() => fetchBatches()}>
            查询
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleReset}>
            重置
          </Button>
        </div>

        <div style={{ minWidth: 0, overflow: 'hidden' }}>
          <Table
            rowKey="id"
            columns={columns}
            dataSource={filteredBatches}
            loading={loading}
            tableLayout="fixed"
            scroll={{ x: true }}
            pagination={{
              current: page,
              pageSize,
              total,
              showSizeChanger: true,
              showTotal: (t) => `共 ${t} 条`,
              onChange: (p, ps) => {
                setPage(p);
                if (ps !== pageSize) setPageSize(ps);
              },
              style: { padding: '0 24px 16px' },
            }}
            locale={{
              emptyText: (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="暂无批量测试"
                  style={{ padding: '48px 0' }}
                >
                  <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
                    创建第一个测试
                  </Button>
                </Empty>
              ),
            }}
          />
        </div>
      </Card>

      <Modal
        open={modalOpen}
        title="新建批量测试"
        onCancel={() => {
          setModalOpen(false);
          resetWizard();
        }}
        footer={null}
        width={720}
        centered
        destroyOnHidden
        afterOpenChange={(open) => {
          if (open) {
            form.setFieldsValue({
              accuracy_threshold: 95,
              latency_threshold_ms: 2000,
              case_source: CASE_SOURCE.MANUAL,
              llm_samples: 5,
              include_knowledge: false,
              include_chitchat: false,
            });
          }
        }}
      >
        <Steps
          current={wizardStep}
          style={{ marginBottom: 24 }}
          items={[{ title: '基本信息' }, { title: '用例来源' }]}
        />
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            accuracy_threshold: 95,
            latency_threshold_ms: 2000,
            case_source: CASE_SOURCE.MANUAL,
            llm_samples: 5,
            include_knowledge: false,
            include_chitchat: false,
          }}
        >
          {wizardStep === 0 && (
            <>
              <Form.Item name="name" label="测试名称" rules={[{ required: true, message: '请输入测试名称' }]}>
                <Input placeholder="例如: v1.2 回归测试" maxLength={128} />
              </Form.Item>
              <Form.Item name="description" label="描述">
                <Input.TextArea rows={3} placeholder="测试目的描述..." maxLength={500} />
              </Form.Item>
              <Form.Item name="profile_id" label="关联对话方案">
                <Select
                  placeholder="选择方案（可选）"
                  allowClear
                  options={profiles.map((p) => ({ value: p.id, label: p.name }))}
                />
              </Form.Item>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="accuracy_threshold"
                    label="准确率阈值 (%)"
                    rules={[{ required: true, type: 'number', min: 0, max: 100 }]}
                  >
                    <InputNumber min={0} max={100} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="latency_threshold_ms"
                    label="延迟阈值 (ms)"
                    rules={[{ required: true, type: 'number', min: 0 }]}
                  >
                    <InputNumber min={0} step={50} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
            </>
          )}

          {wizardStep === 1 && (
            <>
              <Form.Item name="case_source" label="用例来源">
                <Radio.Group>
                  <Radio.Button value={CASE_SOURCE.MANUAL}>手动添加</Radio.Button>
                  <Radio.Button value={CASE_SOURCE.LLM}>LLM 生成</Radio.Button>
                  <Radio.Button value={CASE_SOURCE.EXCEL}>CSV / Excel 导入</Radio.Button>
                </Radio.Group>
              </Form.Item>

              {caseSource === CASE_SOURCE.LLM && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                    选择要覆盖的意图（来自意图库数据集）
                  </Text>
                  <Transfer
                    dataSource={intentTransferData}
                    targetKeys={transferTargetKeys}
                    onChange={setTransferTargetKeys}
                    render={(item) => item.title}
                    listStyle={{ width: 280, height: 260 }}
                    showSearch
                    filterOption={(input, item) =>
                      (item.title || '').toLowerCase().includes(input.toLowerCase())
                    }
                  />
                  <Row gutter={16} style={{ marginTop: 16 }}>
                    <Col span={8}>
                      <Form.Item name="llm_samples" label="每意图样本数">
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
                </div>
              )}

              {caseSource === CASE_SOURCE.EXCEL && (
                <div>
                  <Space align="start" wrap style={{ marginBottom: 12 }}>
                    <Button type="link" icon={<DownloadOutlined />} onClick={handleDownloadTemplate} style={{ padding: 0 }}>
                      下载 CSV 模板
                    </Button>
                    <Upload accept=".csv,.txt" maxCount={1} showUploadList beforeUpload={handleExcelBeforeUpload}>
                      <Button icon={<UploadOutlined />}>上传 CSV</Button>
                    </Upload>
                  </Space>
                  {excelError && (
                    <Text type="danger" style={{ display: 'block', marginBottom: 8 }}>
                      {excelError}
                    </Text>
                  )}
                  {excelRows.length > 0 && !excelError && (
                    <Table
                      size="small"
                      pagination={false}
                      scroll={{ y: 200 }}
                      rowKey={(_, i) => `p-${i}`}
                      dataSource={excelRows.slice(0, 8)}
                      columns={[
                        { title: 'input_text', dataIndex: 'input_text', ellipsis: true },
                        { title: 'expected_intent', dataIndex: 'expected_intent', width: 120 },
                        { title: 'expected_domain', dataIndex: 'expected_domain', width: 110 },
                      ]}
                    />
                  )}
                  {excelRows.length > 8 && !excelError && (
                    <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                      仅预览前 8 行，共 {excelRows.length} 行
                    </Text>
                  )}
                </div>
              )}
            </>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 24 }}>
            {wizardStep === 1 && <Button onClick={() => setWizardStep(0)}>上一步</Button>}
            <Button onClick={() => { setModalOpen(false); resetWizard(); }}>取消</Button>
            {wizardStep === 0 ? (
              <Button type="primary" onClick={handleWizardNext}>
                下一步
              </Button>
            ) : (
              <Button type="primary" loading={wizardSubmitting} onClick={handleWizardCreate}>
                创建
              </Button>
            )}
          </div>
        </Form>
      </Modal>

      <Modal
        open={!!reExecTarget}
        title="重新执行"
        okText="确认"
        cancelText="取消"
        confirmLoading={reExecLoading}
        onOk={handleReExecuteConfirm}
        onCancel={() => setReExecTarget(null)}
        centered
      >
        <Text>历史结果将被覆盖，确认重新执行？</Text>
      </Modal>

      <DangerConfirmModal
        open={!!deleteTarget}
        title="删除批量测试"
        description={`确定删除测试「${deleteTarget?.name}」？删除后所有关联的用例、执行结果和分析报告也将被删除。`}
        impactText="此操作不可恢复。"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        confirmLoading={deleteLoading}
      />
    </div>
  );
}

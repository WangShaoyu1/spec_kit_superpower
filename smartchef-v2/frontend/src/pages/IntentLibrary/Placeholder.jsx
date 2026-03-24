import { useEffect, useState, useCallback, useMemo, useRef, memo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Breadcrumb,
  Card,
  Descriptions,
  Tag,
  Button,
  Table,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  Tabs,
  Spin,
  Skeleton,
  Empty,
  Result,
  message,
  Drawer,
  Slider,
  Upload,
  Row,
  Col,
  Progress,
  Divider,
  List,
  Checkbox,
  Alert,
  Tooltip,
} from 'antd';
import {
  ArrowLeftOutlined,
  PlusOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  BugOutlined,
  ExperimentOutlined,
  MessageOutlined,
  ThunderboltOutlined,
  DownloadOutlined,
  CloudUploadOutlined,
  ApiOutlined,
  FileExcelOutlined,
  DatabaseOutlined,
  BarsOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { intentLibraryApi } from '../../services/intentLibraryApi';
import { batchTestApi } from '../../services/batchTestApi';
import DangerConfirmModal from '../../components/DangerConfirmModal';
import {
  getCoverageDatasetId,
  isEvaluationDataset,
  normalizeDatasetCollections,
} from './datasetPageUtils';
import {
  buildIntentLibraryBatchCreatePayload,
  buildIntentLibraryBatchImportPayload,
} from './batchTestBridge';
import { shouldLoadTrainingDatasetChildren } from './datasetDetailUtils';
import { getExcelImportFeedback, getLlmGenerationFeedback } from './feedbackUtils';
import { getDebugInfoFromMessage, getPaginatedMessageItems, removeTemporaryMessage } from './testMessageUtils';

const { Title, Text } = Typography;
const { TextArea } = Input;

const DATASET_TYPE_OPTIONS = [
  { value: 'manual', label: '手工构建' },
  { value: 'llm_synthesis', label: 'LLM 合成' },
  { value: 'import', label: '文件导入' },
];

const TYPE_TAG_CONFIG = {
  manual: { color: 'blue', label: '手工' },
  llm_synthesis: { color: 'purple', label: 'LLM 合成' },
  import: { color: 'orange', label: '导入' },
  training: { color: 'blue', label: '训练集' },
  evaluation: { color: 'orange', label: '评估集' },
};

const LLM_MODEL_OPTIONS = [
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'qwen-max', label: 'Qwen-Max' },
];

export const DatasetsPage = memo(function DatasetsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const [libraryName, setLibraryName] = useState('');
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingDataset, setEditingDataset] = useState(null);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [llmModalOpen, setLlmModalOpen] = useState(false);
  const [excelModalOpen, setExcelModalOpen] = useState(false);
  const [synthesisForm] = Form.useForm();
  const [excelFileList, setExcelFileList] = useState([]);
  const [coverageOptions, setCoverageOptions] = useState([]);
  const [generationDatasets, setGenerationDatasets] = useState([]);
  const [sampleCount, setSampleCount] = useState(120);

  const fetchDatasets = useCallback(async () => {
    setLoading(true);
    try {
      const [trainingRes, evaluationRes] = await Promise.all([
        intentLibraryApi.listDatasets(id, { page: 1, page_size: 100 }),
        intentLibraryApi.listEvalDatasets(id, { page: 1, page_size: 100 }),
      ]);
      const trainingPayload = trainingRes.data?.data ?? trainingRes.data;
      const evaluationPayload = evaluationRes.data?.data ?? evaluationRes.data;
      const trainingItems = Array.isArray(trainingPayload)
        ? trainingPayload
        : trainingPayload?.items ?? [];
      const evaluationItems = Array.isArray(evaluationPayload)
        ? evaluationPayload
        : evaluationPayload?.items ?? [];
      const mergedDatasets = normalizeDatasetCollections(trainingItems, evaluationItems);
      setDatasets(mergedDatasets);
      setGenerationDatasets(mergedDatasets);
    } catch {
      message.error('获取数据集列表失败');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    intentLibraryApi
      .getLibrary(id)
      .then((res) => {
        const lib = res.data?.data ?? res.data;
        setLibraryName(lib?.name ?? '');
      })
      .catch(() => {});
    fetchDatasets();
  }, [id, fetchDatasets]);

  const openCreate = useCallback(() => {
    setEditingDataset(null);
    form.resetFields();
    form.setFieldsValue({ dataset_kind: 'training', source_type: 'manual' });
    setModalOpen(true);
  }, [form]);

  const openEdit = useCallback(
    (record) => {
      setEditingDataset(record);
      form.setFieldsValue({
        dataset_kind: record.dataset_kind || 'training',
        name: record.name,
        description: record.description,
        source_type: record.source_type || record.type || 'manual',
      });
      setModalOpen(true);
    },
    [form],
  );

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      const payload = {
        name: values.name,
        description: values.description,
        source_type: values.source_type || values.type || 'manual',
      };
      const isEval = values.dataset_kind === 'evaluation';
      if (editingDataset) {
        if (isEval) {
          await intentLibraryApi.updateEvalDataset(editingDataset.id, payload);
        } else {
          await intentLibraryApi.updateDataset(editingDataset.id, payload);
        }
        message.success('更新成功');
      } else {
        if (isEval) {
          await intentLibraryApi.createEvalDataset(id, payload);
        } else {
          await intentLibraryApi.createDataset(id, payload);
        }
        message.success('创建成功');
      }
      setModalOpen(false);
      fetchDatasets();
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '操作失败');
    } finally {
      setSubmitLoading(false);
    }
  }, [form, editingDataset, id, fetchDatasets]);

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      if (isEvaluationDataset(deleteTarget)) {
        await intentLibraryApi.deleteEvalDataset(deleteTarget.id);
      } else {
        await intentLibraryApi.deleteDataset(deleteTarget.id);
      }
      message.success('删除成功');
      setDeleteTarget(null);
      fetchDatasets();
    } catch (err) {
      message.error(err?.message || '删除失败');
    } finally {
      setDeleteLoading(false);
    }
  }, [deleteTarget, fetchDatasets]);

  const loadCoverageForDataset = useCallback(async (datasetId) => {
    if (!datasetId) {
      setCoverageOptions([]);
      return;
    }
    const selectedDataset = generationDatasets.find((dataset) => dataset.id === datasetId);
    const coverageDatasetId = getCoverageDatasetId(selectedDataset);
    if (!coverageDatasetId) {
      setCoverageOptions([]);
      return;
    }
    try {
      const res = await intentLibraryApi.listIntents(coverageDatasetId, {});
      const raw = Array.isArray(res.data) ? res.data : res.data?.items ?? [];
      setCoverageOptions(
        raw.map((i) => ({ label: i.name_zh || i.intent_key, value: i.intent_key })),
      );
    } catch {
      setCoverageOptions([]);
    }
  }, [generationDatasets]);

  const llmModelWatch = Form.useWatch('llm_model', synthesisForm);

  const columns = useMemo(
    () => [
      {
        title: '名称',
        dataIndex: 'name',
        key: 'name',
        width: 200,
        ellipsis: true,
        render: (text) => <Text strong>{text}</Text>,
      },
      {
        title: '类型',
        dataIndex: 'dataset_kind',
        key: 'dataset_kind',
        width: 100,
        render: (_, record) => {
          const cfg =
            record.dataset_kind === 'evaluation'
              ? TYPE_TAG_CONFIG.evaluation
              : TYPE_TAG_CONFIG.training;
          return <Tag color={cfg.color}>{cfg.label}</Tag>;
        },
      },
      {
        title: '绑定',
        dataIndex: 'binding_status',
        key: 'binding_status',
        width: 96,
        render: (_, record) => {
          const st = record.config?.binding_status ?? (record.is_active ? 'active' : 'inactive');
          const label =
            st === 'active' ? '已绑定' : st === 'pending' ? '待绑定' : '未绑定';
          const color = st === 'active' ? 'success' : st === 'pending' ? 'warning' : 'default';
          return <Tag color={color}>{label}</Tag>;
        },
      },
      {
        title: '来源',
        key: 'source_llm',
        width: 88,
        render: (_, record) => {
          const isLlm =
            record.source_type === 'llm_synthesis' || record.config?.llm_source || record.config?.synthesis;
          return isLlm ? (
            <Tag color="purple" icon={<ApiOutlined />}>
              LLM
            </Tag>
          ) : (
            <Tag>手工</Tag>
          );
        },
      },
      {
        title: '样本数',
        key: 'sample_progress',
        width: 160,
        render: (_, record) => {
          const cur = record.sample_count ?? 0;
          const target = record.config?.sample_target;
          if (!target) {
            return (
              <Text style={{ fontFamily: 'var(--font-mono)' }}>
                {cur} 条
              </Text>
            );
          }
          const pct = Math.min(100, Math.round((cur / target) * 100));
          return (
            <Progress
              percent={pct}
              size="small"
              format={() => `${cur}/${target}`}
              strokeColor={cur >= target ? '#52c41a' : '#1677ff'}
            />
          );
        },
      },
      {
        title: '意图数',
        dataIndex: 'intent_count',
        key: 'intent_count',
        width: 88,
        align: 'center',
        render: (count) => (
          <Text style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
            {count ?? 0}
          </Text>
        ),
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
          <Space size={4}>
            <Tooltip title="导出元数据 JSON">
              <Button
                type="link"
                size="small"
                icon={<DownloadOutlined />}
                onClick={() => {
                  const blob = new Blob([JSON.stringify(record, null, 2)], {
                    type: 'application/json',
                  });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `dataset-${record.name || record.id}.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
              />
            </Tooltip>
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              disabled={isEvaluationDataset(record)}
              onClick={() => navigate(`/intent-library/${id}/datasets/${record.id}`)}
            >
              详情
            </Button>
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => openEdit(record)}
            >
              编辑
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
    [id, navigate, openEdit],
  );

  return (
    <Spin spinning={loading && datasets.length === 0} size="large">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        {/* Breadcrumb */}
        <Breadcrumb
          items={[
            {
              title: (
                <a onClick={() => navigate('/intent-library')} style={{ cursor: 'pointer' }}>
                  指令库管理
                </a>
              ),
            },
            {
              title: (
                <a
                  onClick={() => navigate(`/intent-library/${id}`)}
                  style={{ cursor: 'pointer' }}
                >
                  {libraryName || '指令库详情'}
                </a>
              ),
            },
            { title: '数据集管理' },
          ]}
        />

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Button
              type="text"
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate(`/intent-library/${id}`)}
            />
            <Title level={4} style={{ marginBottom: 0 }}>
              数据集管理
            </Title>
          </div>
          <Space>
            <Button
              icon={<ApiOutlined />}
              onClick={() => {
                synthesisForm.resetFields();
                synthesisForm.setFieldsValue({
                  llm_model: 'gpt-4o',
                  prompt_template:
                    '基于下列意图集合，为用户语料生成多样化口语化表述，保持领域一致：\n{intent_list}',
                });
                setSampleCount(120);
                setLlmModalOpen(true);
              }}
            >
              LLM 合成
            </Button>
            <Button
              icon={<FileExcelOutlined />}
              onClick={() => {
                setExcelFileList([]);
                setExcelModalOpen(true);
              }}
            >
              Excel 导入
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              新建数据集
            </Button>
          </Space>
        </div>

        {/* Table */}
        <Card styles={{ body: { padding: 0 } }}>
          <Table
            rowKey="id"
            columns={columns}
            dataSource={datasets}
            loading={loading}
            tableLayout="fixed"
            scroll={{ x: true }}
            pagination={{
              showSizeChanger: true,
              showTotal: (t) => `共 ${t} 条`,
              style: { padding: '0 24px 16px' },
            }}
            locale={{
              emptyText: (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="暂无数据集"
                  style={{ padding: '48px 0' }}
                >
                  <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
                    创建第一个数据集
                  </Button>
                </Empty>
              ),
            }}
          />
        </Card>

        {/* Create / Edit Modal */}
        <Modal
          open={modalOpen}
          title={editingDataset ? '编辑数据集' : '新建数据集'}
          onCancel={() => setModalOpen(false)}
          onOk={handleSubmit}
          confirmLoading={submitLoading}
          okText={editingDataset ? '保存' : '创建'}
          cancelText="取消"
          width={480}
          centered
          destroyOnHidden
        >
          <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
            <Form.Item
              name="dataset_kind"
              label="数据集类型"
              rules={[{ required: true, message: '请选择数据集类型' }]}
            >
              <Select
                disabled={!!editingDataset}
                options={[
                  { value: 'training', label: '训练集' },
                  { value: 'evaluation', label: '评估集' },
                ]}
              />
            </Form.Item>
            <Form.Item
              name="name"
              label="名称"
              rules={[{ required: true, message: '请输入数据集名称' }]}
            >
              <Input placeholder="例如: 烹饪意图训练集 v1" />
            </Form.Item>
            <Form.Item name="description" label="描述">
              <Input.TextArea rows={3} placeholder="数据集的用途描述..." />
            </Form.Item>
            <Form.Item
              name="source_type"
              label="来源类型"
              rules={[{ required: true, message: '请选择来源类型' }]}
            >
              <Select options={DATASET_TYPE_OPTIONS} />
            </Form.Item>
          </Form>
        </Modal>

        <Modal
          title="LLM 数据合成"
          open={llmModalOpen}
          onCancel={() => setLlmModalOpen(false)}
          width={640}
          centered
          destroyOnHidden
          confirmLoading={submitLoading}
          onOk={async () => {
            try {
              const values = await synthesisForm.validateFields();
              setSubmitLoading(true);
              const payload = {
                model_name: values.llm_model,
                samples_per_intent: sampleCount,
                prompt_template: values.prompt_template,
              };
              const ds = generationDatasets.find((d) => d.id === values.dataset_id);
              const isEval = isEvaluationDataset(ds);
              let data;
              if (isEval) {
                const res = await intentLibraryApi.generateEvaluationData(values.dataset_id, payload);
                data = res.data;
              } else {
                const startRes = await intentLibraryApi.startTrainingGenerationJob(
                  values.dataset_id,
                  payload,
                );
                const jobId = startRes.data?.job_id;
                const pollMs = (startRes.data?.poll_interval_sec ?? 6) * 1000;
                message.loading({
                  content: '已提交相似问生成任务…',
                  duration: 0,
                  key: 'llm-train-job',
                });
                let status = null;
                try {
                  for (;;) {
                    const stRes = await intentLibraryApi.getTrainingGenerationJob(
                      values.dataset_id,
                      jobId,
                    );
                    status = stRes.data;
                    const idx = status.intent_index ?? 0;
                    const total = status.intent_total ?? 0;
                    const gen = status.generated_count ?? 0;
                    message.loading({
                      content: `相似问生成中：意图 ${idx}/${total || '…'}，已写入 ${gen} 条`,
                      duration: 0,
                      key: 'llm-train-job',
                    });
                    if (status.status === 'completed' || status.status === 'failed') {
                      break;
                    }
                    await new Promise((r) => setTimeout(r, pollMs));
                  }
                } finally {
                  message.destroy('llm-train-job');
                }
                if (!status || status.status === 'failed') {
                  message.error(status?.error || status?.message || '生成失败');
                  return;
                }
                data = status;
              }
              const feedback = getLlmGenerationFeedback(data);
              message[feedback.level](feedback.text, feedback.level === 'warning' ? 8 : undefined);
              setLlmModalOpen(false);
              fetchDatasets();
            } catch (e) {
              if (e?.errorFields) return;
              const serverMsg = e?.response?.data?.msg;
              message.error(serverMsg || `LLM 合成失败: ${e?.message || '未知错误'}`);
            } finally {
              setSubmitLoading(false);
            }
          }}
        >
          <Form form={synthesisForm} layout="vertical">
            <Form.Item
              name="dataset_id"
              label="目标数据集"
              rules={[{ required: true, message: '请选择数据集' }]}
            >
              <Select
                placeholder="选择已有数据集"
                options={generationDatasets.map((d) => ({
                  value: d.id,
                  label: `${d.name}（${isEvaluationDataset(d) ? '评估集' : '训练集'}）`,
                }))}
                onChange={(v) => loadCoverageForDataset(v)}
              />
            </Form.Item>
            <Form.Item
              name="llm_model"
              label="合成模型"
              rules={[{ required: true, message: '请选择模型' }]}
            >
              <Select options={LLM_MODEL_OPTIONS} />
            </Form.Item>
            <Form.Item label={`目标样本数（${sampleCount}）`} required>
              <Slider
                min={10}
                max={500}
                value={sampleCount}
                onChange={setSampleCount}
                marks={{ 10: '10', 500: '500' }}
              />
            </Form.Item>
            <Form.Item
              name="prompt_template"
              label="提示词模板"
              rules={[{ required: true, message: '请输入模板' }]}
            >
              <TextArea rows={5} style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-sm)' }} />
            </Form.Item>
            <Form.Item label="涉及意图预览">
              <Alert
                type="info"
                showIcon
                message="当前版本会对所选数据集关联的全部意图执行生成。按意图子集定向生成尚未接入，已显式延期。"
                description={
                  coverageOptions.length ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
                      {coverageOptions.map((option) => (
                        <Tag key={option.value}>{option.label}</Tag>
                      ))}
                    </div>
                  ) : (
                    '当前数据集暂无可预览意图。'
                  )
                }
              />
            </Form.Item>
            <Card
              size="small"
              variant="borderless"
              style={{ borderRadius: 12, background: 'rgba(22, 119, 255, 0.06)' }}
            >
              <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                预估成本（示意）：
              </Text>
              <Text strong style={{ marginLeft: 8, fontFamily: 'var(--font-mono)' }}>
                ~$
                {(
                  sampleCount * (llmModelWatch === 'qwen-max' ? 0.0012 : 0.0025)
                ).toFixed(2)}{' '}
                USD
              </Text>
            </Card>
          </Form>
        </Modal>

        <Modal
          title="Excel 批量导入"
          open={excelModalOpen}
          onCancel={() => setExcelModalOpen(false)}
          width={560}
          centered
          destroyOnHidden
          onOk={() => {
            const f = excelFileList[0]?.originFileObj;
            if (!f) {
              message.warning('请选择 .xlsx / .xls 文件');
              return;
            }
            if (!/\.xlsx?$/i.test(f.name)) {
              message.error('仅支持 Excel 文件');
              return;
            }
            const feedback = getExcelImportFeedback({ fileName: f.name });
            message[feedback.level](feedback.text, 6);
            setExcelModalOpen(false);
            setExcelFileList([]);
          }}
        >
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
            message="模板列：intent_key | utterance | label | slot_json（可选）"
          />
          <Upload.Dragger
            accept=".xlsx,.xls"
            maxCount={1}
            fileList={excelFileList}
            beforeUpload={(file) => {
              const ok = /\.xlsx?$/i.test(file.name);
              if (!ok) message.error('格式错误');
              return ok ? false : Upload.LIST_IGNORE;
            }}
            onChange={({ fileList }) => setExcelFileList(fileList)}
          >
            <p className="ant-upload-drag-icon">
              <CloudUploadOutlined style={{ color: '#1677ff', fontSize: 42 }} />
            </p>
            <p className="ant-upload-text">拖拽或点击上传</p>
          </Upload.Dragger>
        </Modal>

        {/* Delete confirmation */}
        <DangerConfirmModal
          open={!!deleteTarget}
          title="删除数据集"
          description={`确定删除数据集「${deleteTarget?.name}」？删除后其中的所有意图数据也将被删除。`}
          impactText="此操作不可恢复，数据集中的意图数据将被永久移除。"
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
          confirmLoading={deleteLoading}
        />
      </div>
    </Spin>
  );
});

const DATASET_TYPE_MAP = {
  manual: { label: '手工', color: 'blue' },
  llm_synthesis: { label: 'LLM 合成', color: 'purple' },
  import: { label: '导入', color: 'orange' },
  training: { label: '训练集', color: 'blue' },
  evaluation: { label: '评估集', color: 'orange' },
  test: { label: '测试集', color: 'green' },
};

const PAGE_SIZE = 10;

const detailStatCardStyle = {
  borderRadius: 12,
  boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
};

export const DatasetDetailPage = memo(function DatasetDetailPage() {
  const { id, datasetId } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [drawerForm] = Form.useForm();

  const [dataset, setDataset] = useState(null);
  const [datasetKind, setDatasetKind] = useState(null);
  const [datasetLoading, setDatasetLoading] = useState(true);
  const [intents, setIntents] = useState([]);
  const [intentsLoading, setIntentsLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: PAGE_SIZE, total: 0 });
  const [modalOpen, setModalOpen] = useState(false);
  const [editingIntent, setEditingIntent] = useState(null);
  const [submitLoading, setSubmitLoading] = useState(false);

  const [mainTab, setMainTab] = useState('intents');
  const [slots, setSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [entityTotal, setEntityTotal] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerIntent, setDrawerIntent] = useState(null);
  const [drawerSaving, setDrawerSaving] = useState(false);
  const [similarDraft, setSimilarDraft] = useState([]);
  const [negDraft, setNegDraft] = useState([]);

  const fetchDataset = useCallback(async () => {
    setDatasetLoading(true);
    try {
      const res = await intentLibraryApi.getDataset(datasetId);
      setDataset(res.data?.data ?? res.data);
      setDatasetKind('training');
    } catch {
      try {
        const evalRes = await intentLibraryApi.getEvalDataset(datasetId);
        setDataset(evalRes.data?.data ?? evalRes.data);
        setDatasetKind('evaluation');
      } catch {
        setDataset(null);
        setDatasetKind(null);
      }
    } finally {
      setDatasetLoading(false);
    }
  }, [datasetId]);

  const fetchIntents = useCallback(async () => {
    setIntentsLoading(true);
    try {
      const res = await intentLibraryApi.listIntents(datasetId, {});
      const items = Array.isArray(res.data) ? res.data : res.data?.items ?? [];
      setIntents(items);
      setPagination((p) => ({ ...p, total: items.length }));
    } catch {
      setIntents([]);
    } finally {
      setIntentsLoading(false);
    }
  }, [datasetId]);

  const fetchSlotsMeta = useCallback(async () => {
    setSlotsLoading(true);
    try {
      const res = await intentLibraryApi.listSlots(datasetId);
      const list = Array.isArray(res.data) ? res.data : [];
      setSlots(list);
      let ent = 0;
      await Promise.all(
        list.map(async (s) => {
          try {
            const er = await intentLibraryApi.listSlotEntities(s.id);
            const el = Array.isArray(er.data) ? er.data : [];
            ent += el.length;
          } catch {
            /* ignore */
          }
        }),
      );
      setEntityTotal(ent);
    } catch {
      setSlots([]);
      setEntityTotal(0);
    } finally {
      setSlotsLoading(false);
    }
  }, [datasetId]);

  useEffect(() => {
    fetchDataset();
  }, [fetchDataset]);

  const canLoadTrainingChildren = shouldLoadTrainingDatasetChildren({
    datasetId,
    datasetKind,
    datasetLoading,
  });

  useEffect(() => {
    if (canLoadTrainingChildren) {
      fetchIntents();
      if (datasetId) fetchSlotsMeta();
    } else {
      setIntents([]);
      setSlots([]);
      setEntityTotal(0);
    }
  }, [canLoadTrainingChildren, fetchIntents, fetchSlotsMeta, datasetId]);

  useEffect(() => {
    if (canLoadTrainingChildren && mainTab === 'slots' && datasetId) fetchSlotsMeta();
  }, [mainTab, datasetId, fetchSlotsMeta, canLoadTrainingChildren]);

  const openCreateModal = useCallback(() => {
    setEditingIntent(null);
    form.resetFields();
    setModalOpen(true);
  }, [form]);

  const openDrawerForIntent = useCallback(
    async (record) => {
      drawerForm.setFieldsValue({
        name_zh: record.name_zh,
        hit_responses: record.hit_responses?.length ? record.hit_responses : [''],
        slot_keys: record.slot_keys ?? [],
      });
      setDrawerOpen(true);
      try {
        const [sqRes, neRes] = await Promise.all([
          intentLibraryApi.listSimilarQuestions(record.id),
          intentLibraryApi.listNegativeExamples(record.id),
        ]);
        const sqList = Array.isArray(sqRes.data) ? sqRes.data : [];
        const neList = Array.isArray(neRes.data) ? neRes.data : [];
        setSimilarDraft(sqList.map((x) => ({ id: x.id, text: x.text })));
        setNegDraft(neList.map((x) => ({ id: x.id, text: x.text })));
        setDrawerIntent({ ...record, _sqOrig: sqList, _neOrig: neList });
      } catch {
        setSimilarDraft([]);
        setNegDraft([]);
        setDrawerIntent({ ...record, _sqOrig: [], _neOrig: [] });
      }
    },
    [drawerForm],
  );

  const saveDrawer = useCallback(async () => {
    if (!drawerIntent) return;
    try {
      const values = await drawerForm.validateFields();
      setDrawerSaving(true);
      const hitResponses = (values.hit_responses || [])
        .map((s) => (typeof s === 'string' ? s.trim() : ''))
        .filter(Boolean);
      await intentLibraryApi.updateIntent(drawerIntent.id, {
        name_zh: values.name_zh,
        slot_keys: values.slot_keys || [],
        hit_responses: hitResponses,
      });

      const draftSqIds = new Set(similarDraft.filter((r) => r.id).map((r) => r.id));
      for (const o of drawerIntent._sqOrig || []) {
        if (!draftSqIds.has(o.id)) {
          await intentLibraryApi.deleteSimilarQuestion(o.id);
        }
      }
      for (const row of similarDraft) {
        if (row.id) {
          await intentLibraryApi.updateSimilarQuestion(row.id, { text: row.text });
        } else if (row.text?.trim()) {
          await intentLibraryApi.createSimilarQuestion(drawerIntent.id, {
            text: row.text.trim(),
          });
        }
      }

      const draftNeIds = new Set(negDraft.filter((r) => r.id).map((r) => r.id));
      for (const o of drawerIntent._neOrig || []) {
        if (!draftNeIds.has(o.id)) {
          await intentLibraryApi.deleteNegativeExample(o.id);
        }
      }
      for (const row of negDraft) {
        if (!row.id && row.text?.trim()) {
          await intentLibraryApi.createNegativeExample(drawerIntent.id, {
            text: row.text.trim(),
          });
        }
      }

      message.success('已保存');
      setDrawerOpen(false);
      fetchIntents();
      fetchDataset();
      fetchSlotsMeta();
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '保存失败');
    } finally {
      setDrawerSaving(false);
    }
  }, [
    drawerForm,
    drawerIntent,
    similarDraft,
    negDraft,
    fetchIntents,
    fetchDataset,
    fetchSlotsMeta,
  ]);

  const openEditModal = useCallback(
    (record) => {
      setEditingIntent(record);
      form.setFieldsValue({
        intent_key: record.intent_key,
        name_zh: record.name_zh,
        description: record.description,
      });
      setModalOpen(true);
    },
    [form],
  );

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);

      if (editingIntent) {
        await intentLibraryApi.updateIntent(editingIntent.id, {
          name_zh: values.name_zh,
          description: values.description,
        });
        message.success('意图更新成功');
      } else {
        await intentLibraryApi.createIntent(datasetId, {
          intent_key: values.intent_key,
          name_zh: values.name_zh,
          description: values.description,
          slot_keys: [],
          hit_responses: [],
        });
        message.success('意图创建成功');
      }

      setModalOpen(false);
      form.resetFields();
      setEditingIntent(null);
      fetchIntents();
      fetchDataset();
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '操作失败');
    } finally {
      setSubmitLoading(false);
    }
  }, [form, editingIntent, datasetId, fetchIntents, fetchDataset]);

  const handleDelete = useCallback(
    (record) => {
      Modal.confirm({
        title: '删除意图',
        content: `确认删除意图「${record.name_zh || record.intent_key}」？此操作不可撤销。`,
        okText: '确认删除',
        okButtonProps: { danger: true },
        cancelText: '取消',
        onOk: async () => {
          try {
            await intentLibraryApi.deleteIntent(record.id);
            message.success('意图已删除');
            fetchIntents();
            fetchDataset();
          } catch (err) {
            message.error(err?.message || '删除失败');
          }
        },
      });
    },
    [fetchIntents, fetchDataset],
  );

  const slotKeyOptions = useMemo(
    () => slots.map((s) => ({ value: s.slot_key, label: `${s.slot_key} (${s.name_zh})` })),
    [slots],
  );

  const columns = useMemo(
    () => [
      {
        title: 'Key',
        dataIndex: 'intent_key',
        key: 'intent_key',
        width: 140,
        ellipsis: true,
        render: (text) => (
          <Text code style={{ fontSize: 'var(--font-size-xs)' }}>
            {text}
          </Text>
        ),
      },
      {
        title: '中文名',
        dataIndex: 'name_zh',
        key: 'name_zh',
        width: 300,
        render: (text) => <Text strong>{text}</Text>,
      },
      {
        title: '槽位',
        dataIndex: 'slot_keys',
        key: 'slot_keys',
        width: 160,
        ellipsis: true,
        render: (keys) =>
          Array.isArray(keys) && keys.length ? (
            <Space size={4} wrap>
              {keys.map((k) => (
                <Tag key={k}>{k}</Tag>
              ))}
            </Space>
          ) : (
            <Text type="secondary">-</Text>
          ),
      },
      {
        title: '描述',
        dataIndex: 'description',
        key: 'description',
        ellipsis: true,
        render: (text) => text || <Text type="secondary">-</Text>,
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
        width: 160,
        render: (_, record) => (
          <Space size={4} onClick={(e) => e.stopPropagation()}>
            <Button type="link" size="small" onClick={() => openDrawerForIntent(record)}>
              配置
            </Button>
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => openEditModal(record)}
            >
              编辑
            </Button>
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            >
              删除
            </Button>
          </Space>
        ),
      },
    ],
    [openEditModal, handleDelete, openDrawerForIntent],
  );

  if (datasetLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        <Skeleton active paragraph={{ rows: 1 }} />
        <Card>
          <Skeleton active paragraph={{ rows: 4 }} />
        </Card>
        <Card>
          <Skeleton active paragraph={{ rows: 6 }} />
        </Card>
      </div>
    );
  }

  if (!dataset) {
    return (
      <Empty description="数据集不存在或加载失败">
        <Button type="primary" onClick={() => navigate(`/intent-library/${id}/datasets`)}>
          返回数据集列表
        </Button>
      </Empty>
    );
  }

  if (datasetKind === 'evaluation') {
    return (
      <Result
        status="info"
        title="评估集暂无数据明细编辑页"
        subTitle="当前页面仅支持训练集的意图、词槽、实体与相似问维护。评估集可在数据集列表中进行查看、生成和删除。"
        extra={
          <Button type="primary" onClick={() => navigate(`/intent-library/${id}/datasets`)}>
            返回数据集列表
          </Button>
        }
      />
    );
  }

  const typeInfo =
    DATASET_TYPE_MAP[dataset.source_type || dataset.type] ?? {
      label: dataset.source_type || dataset.type,
      color: 'default',
    };

  const evalSamples = dataset.config?.eval_sample_count ?? dataset.config?.eval_samples ?? 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      <Breadcrumb
        items={[
          {
            title: (
              <a onClick={() => navigate('/intent-library')} style={{ cursor: 'pointer' }}>
                指令库管理
              </a>
            ),
          },
          {
            title: (
              <a onClick={() => navigate(`/intent-library/${id}`)} style={{ cursor: 'pointer' }}>
                {dataset.library_name ?? '指令库'}
              </a>
            ),
          },
          {
            title: (
              <a
                onClick={() => navigate(`/intent-library/${id}/datasets`)}
                style={{ cursor: 'pointer' }}
              >
                数据集管理
              </a>
            ),
          },
          { title: dataset.name },
        ]}
      />

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(`/intent-library/${id}/datasets`)}
        />
        <Title level={4} style={{ marginBottom: 0, flex: 1 }}>
          {dataset.name}
        </Title>
      </div>

      <Row gutter={[12, 12]}>
        {[
          { label: '总意图数', value: dataset.intent_count ?? 0 },
          { label: '训练样本数', value: dataset.sample_count ?? 0 },
          { label: '评估样本数', value: evalSamples },
          { label: '槽位数', value: slots.length },
          { label: '实体数', value: entityTotal },
        ].map((s) => (
          <Col xs={24} sm={12} md={8} lg={8} xl={4} key={s.label}>
            <Card variant="borderless" style={detailStatCardStyle}>
              <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                {s.label}
              </Text>
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--font-size-2xl)',
                  fontWeight: 700,
                  marginTop: 4,
                }}
              >
                {s.value}
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Card variant="borderless" style={detailStatCardStyle}>
        <Descriptions
          column={3}
          size="small"
          styles={{ label: { color: 'var(--color-text-secondary)', fontWeight: 500 } }}
        >
          <Descriptions.Item label="名称">
            <Text strong>{dataset.name}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="类型">
            <Tag color={typeInfo.color}>{typeInfo.label}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="样本数">
            <Text style={{ fontFamily: 'var(--font-mono)' }}>{dataset.sample_count ?? 0}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dataset.created_at ? dayjs(dataset.created_at).format('YYYY-MM-DD HH:mm') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="描述" span={2}>
            {dataset.description || <Text type="secondary">暂无描述</Text>}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card variant="borderless" style={{ ...detailStatCardStyle, padding: 0 }} styles={{ body: { padding: 0 } }}>
        <Tabs
          activeKey={mainTab}
          onChange={setMainTab}
          tabBarStyle={{ paddingLeft: 24, marginBottom: 0 }}
          items={[
            {
              key: 'intents',
              label: (
                <span>
                  <BarsOutlined style={{ marginRight: 6 }} />
                  意图列表
                </span>
              ),
              children: (
                <div style={{ padding: 0 }}>
                  <div
                    style={{
                      padding: '12px 24px',
                      borderBottom: '1px solid var(--color-border-light)',
                      display: 'flex',
                      justifyContent: 'flex-end',
                    }}
                  >
                    <Button type="primary" size="small" icon={<PlusOutlined />} onClick={openCreateModal}>
                      新建意图
                    </Button>
                  </div>
                  <Table
                    rowKey="id"
                    columns={columns}
                    dataSource={intents}
                    loading={intentsLoading}
                    pagination={{
                      current: pagination.current,
                      pageSize: pagination.pageSize,
                      total: pagination.total,
                      showSizeChanger: true,
                      showTotal: (total) => `共 ${total} 条`,
                      onChange: (page, pageSize) =>
                        setPagination((p) => ({ ...p, current: page, pageSize: pageSize ?? p.pageSize })),
                    }}
                    tableLayout="fixed"
                    scroll={{ x: true }}
                    onRow={(record) => ({
                      onClick: () => openDrawerForIntent(record),
                      style: { cursor: 'pointer' },
                    })}
                    locale={{
                      emptyText: (
                        <Empty
                          image={Empty.PRESENTED_IMAGE_SIMPLE}
                          description="暂无意图"
                          style={{ padding: '32px 0' }}
                        />
                      ),
                    }}
                  />
                </div>
              ),
            },
            {
              key: 'slots',
              label: (
                <span>
                  <DatabaseOutlined style={{ marginRight: 6 }} />
                  槽位与实体
                </span>
              ),
              children: (
                <div style={{ padding: 24 }}>
                  <Space style={{ marginBottom: 16 }}>
                    <Button
                      onClick={() => {
                        const blob = new Blob([JSON.stringify({ slots }, null, 2)], {
                          type: 'application/json',
                        });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `slots-${dataset.name || datasetId}.json`;
                        a.click();
                        URL.revokeObjectURL(url);
                      }}
                    >
                      导出槽位 JSON
                    </Button>
                    <Upload
                      accept=".json"
                      showUploadList={false}
                      beforeUpload={(file) => {
                        const reader = new FileReader();
                        reader.onload = () => {
                          try {
                            const data = JSON.parse(reader.result);
                            message.info(
                              `已解析 ${data.slots?.length ?? 0} 条槽位（演示：批量写入待接入 API）`,
                            );
                          } catch {
                            message.error('JSON 无效');
                          }
                        };
                        reader.readAsText(file);
                        return false;
                      }}
                    >
                      <Button icon={<CloudUploadOutlined />}>批量导入</Button>
                    </Upload>
                  </Space>
                  <Spin spinning={slotsLoading}>
                    <Row gutter={[16, 16]}>
                      {slots.map((slot) => (
                        <Col xs={24} md={12} lg={8} key={slot.id}>
                          <Card
                            size="small"
                            variant="borderless"
                            style={{
                              borderRadius: 12,
                              boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
                              border: '1px solid var(--color-border-light)',
                            }}
                            title={
                              <Space>
                                <Text strong>{slot.slot_key}</Text>
                                <Tag color={slot.slot_type === 'system' ? 'blue' : 'orange'}>
                                  {slot.slot_type === 'system' ? '系统' : '自定义'}
                                </Tag>
                              </Space>
                            }
                          >
                            <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
                              {slot.name_zh}
                            </Text>
                            <Divider style={{ margin: '12px 0' }} />
                            <SlotEntityList slotId={slot.id} />
                          </Card>
                        </Col>
                      ))}
                    </Row>
                    {!slots.length && !slotsLoading ? (
                      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无槽位" />
                    ) : null}
                  </Spin>
                </div>
              ),
            },
          ]}
        />
      </Card>

      <Drawer
        title={drawerIntent ? `意图配置 · ${drawerIntent.intent_key}` : '意图配置'}
        width={640}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        destroyOnClose
        extra={
          <Space>
            <Button onClick={() => setDrawerOpen(false)}>取消</Button>
            <Button type="primary" loading={drawerSaving} onClick={saveDrawer}>
              保存
            </Button>
          </Space>
        }
      >
        <Form form={drawerForm} layout="vertical">
          <Form.Item label="intent_key">
            <Input value={drawerIntent?.intent_key} disabled style={{ fontFamily: 'var(--font-mono)' }} />
          </Form.Item>
          <Form.Item
            name="name_zh"
            label="中文名"
            rules={[{ required: true, message: '必填' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="slot_keys" label="绑定槽位 (slot_keys)">
            <Select mode="multiple" options={slotKeyOptions} placeholder="选择槽位" allowClear />
          </Form.Item>
          <Divider>相似问</Divider>
          <List
            size="small"
            dataSource={similarDraft}
            locale={{ emptyText: '暂无相似问，点击下方添加' }}
            renderItem={(item, idx) => (
              <List.Item>
                <Input
                  value={item.text}
                  placeholder="相似句式"
                  onChange={(e) => {
                    const next = [...similarDraft];
                    next[idx] = { ...next[idx], text: e.target.value };
                    setSimilarDraft(next);
                  }}
                  addonAfter={
                    <Button
                      type="link"
                      danger
                      size="small"
                      onClick={() => setSimilarDraft(similarDraft.filter((_, i) => i !== idx))}
                    >
                      删除
                    </Button>
                  }
                />
              </List.Item>
            )}
          />
          <Button type="dashed" block onClick={() => setSimilarDraft([...similarDraft, { text: '' }])}>
            添加相似问
          </Button>
          <Divider>负例</Divider>
          <List
            size="small"
            dataSource={negDraft}
            locale={{ emptyText: '暂无负例' }}
            renderItem={(item, idx) => (
              <List.Item>
                <Input
                  value={item.text}
                  placeholder="不应命中本意图的表述"
                  onChange={(e) => {
                    const next = [...negDraft];
                    next[idx] = { ...next[idx], text: e.target.value };
                    setNegDraft(next);
                  }}
                  addonAfter={
                    <Button
                      type="link"
                      danger
                      size="small"
                      onClick={() => setNegDraft(negDraft.filter((_, i) => i !== idx))}
                    >
                      删除
                    </Button>
                  }
                />
              </List.Item>
            )}
          />
          <Button type="dashed" block onClick={() => setNegDraft([...negDraft, { text: '' }])}>
            添加负例
          </Button>
          <Divider>命中话术</Divider>
          <Form.List name="hit_responses">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...rest }) => (
                  <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                    <Form.Item {...rest} name={name} style={{ flex: 1, marginBottom: 0 }}>
                      <Input placeholder="命中回复模板" />
                    </Form.Item>
                    <Button type="text" danger icon={<DeleteOutlined />} onClick={() => remove(name)} />
                  </Space>
                ))}
                <Form.Item>
                  <Button type="dashed" onClick={() => add()} block>
                    添加命中话术
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>
        </Form>
      </Drawer>

      <Modal
        open={modalOpen}
        title={editingIntent ? '编辑意图' : '新建意图'}
        onCancel={() => {
          setModalOpen(false);
          setEditingIntent(null);
        }}
        onOk={handleSubmit}
        confirmLoading={submitLoading}
        okText={editingIntent ? '保存' : '创建'}
        cancelText="取消"
        width={520}
        centered
        destroyOnHidden
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          {!editingIntent && (
            <Form.Item
              name="intent_key"
              label="intent_key"
              rules={[
                { required: true, message: '请输入 intent_key' },
                { pattern: /^[a-zA-Z0-9_.-]+$/, message: '仅字母数字 . - _' },
              ]}
            >
              <Input placeholder="e.g. query_weather" style={{ fontFamily: 'var(--font-mono)' }} />
            </Form.Item>
          )}
          <Form.Item
            name="name_zh"
            label="中文名"
            rules={[{ required: true, message: '请输入中文名' }]}
          >
            <Input placeholder="例如: 查询天气" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="意图描述..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
});

function SlotEntityList({ slotId }) {
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    intentLibraryApi
      .listSlotEntities(slotId)
      .then((res) => {
        if (!cancelled) setEntities(Array.isArray(res.data) ? res.data : []);
      })
      .catch(() => !cancelled && setEntities([]))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [slotId]);
  if (loading) return <Spin size="small" />;
  if (!entities.length) return <Text type="secondary">暂无实体值</Text>;
  return (
    <ul style={{ margin: 0, paddingLeft: 18, fontSize: 'var(--font-size-sm)' }}>
      {entities.map((e) => (
        <li key={e.id} style={{ marginBottom: 6 }}>
          <Text strong style={{ fontFamily: 'var(--font-mono)' }}>{e.value}</Text>
          {e.synonyms?.length ? (
            <Text type="secondary" style={{ marginLeft: 8 }}>
              （同义: {e.synonyms.join('、')}）
            </Text>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

/* ─── Confidence color helper ─── */
function confidenceColor(val) {
  if (val == null) return undefined;
  if (val >= 0.8) return 'var(--color-success)';
  if (val >= 0.5) return 'var(--color-warning)';
  return 'var(--color-error)';
}

function confidenceTag(val) {
  if (val == null) return <Text type="secondary">-</Text>;
  const pct = (val * 100).toFixed(1);
  let color = 'green';
  if (val < 0.5) color = 'red';
  else if (val < 0.8) color = 'orange';
  return (
    <Tag color={color} style={{ fontFamily: 'var(--font-mono)', margin: 0 }}>
      {pct}%
    </Tag>
  );
}

/* ─── Styles ─── */
const styles = {
  pageWrap: {
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--space-4)',
    height: '100%',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    flexShrink: 0,
  },
  chatLayout: {
    display: 'flex',
    gap: 'var(--space-4)',
    flex: 1,
    minHeight: 0,
    overflow: 'hidden',
  },
  sidebar: {
    width: 260,
    flexShrink: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--space-3)',
    overflow: 'hidden',
  },
  sidebarCard: {
    borderRadius: 'var(--radius-lg)',
    boxShadow: 'var(--shadow-sm)',
    overflow: 'hidden',
  },
  chatPanel: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    borderRadius: 'var(--radius-lg)',
    boxShadow: 'var(--shadow-sm)',
    border: '1px solid var(--color-border-light)',
    background: 'var(--color-bg-elevated)',
    overflow: 'hidden',
    minWidth: 0,
  },
  chatMessages: {
    flex: 1,
    overflow: 'auto',
    padding: 'var(--space-4)',
    background: 'var(--color-fill)',
  },
  inputBar: {
    padding: 'var(--space-3) var(--space-4)',
    borderTop: '1px solid var(--color-border-light)',
    display: 'flex',
    gap: 'var(--space-2)',
    alignItems: 'flex-end',
    background: 'var(--color-bg-elevated)',
  },
  debugPanel: {
    width: 300,
    flexShrink: 0,
    borderRadius: 'var(--radius-lg)',
    boxShadow: 'var(--shadow-sm)',
    border: '1px solid var(--color-border-light)',
    background: 'var(--color-bg-elevated)',
    overflow: 'auto',
  },
  bubble: (isUser) => ({
    display: 'flex',
    justifyContent: isUser ? 'flex-end' : 'flex-start',
    marginBottom: 'var(--space-3)',
  }),
  bubbleInner: (isUser) => ({
    maxWidth: '70%',
    padding: 'var(--space-2) var(--space-3)',
    borderRadius: 'var(--radius-lg)',
    background: isUser ? 'var(--color-primary)' : 'var(--color-bg-elevated)',
    color: isUser ? '#fff' : 'var(--color-text)',
    boxShadow: 'var(--shadow-sm)',
    border: isUser ? 'none' : '1px solid var(--color-border-light)',
    fontSize: 'var(--font-size-base)',
    lineHeight: 1.6,
    wordBreak: 'break-word',
    cursor: 'pointer',
  }),
  bubbleIcon: (isUser) => ({
    width: 32,
    height: 32,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: isUser
      ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      : 'linear-gradient(135deg, #52c41a 0%, #95de64 100%)',
    color: '#fff',
    fontSize: 16,
    flexShrink: 0,
  }),
  sessionItem: (active) => ({
    padding: '8px 12px',
    cursor: 'pointer',
    borderRadius: 'var(--radius-md)',
    background: active ? 'var(--color-primary-bg)' : 'transparent',
    borderLeft: active ? '3px solid var(--color-primary)' : '3px solid transparent',
    transition: 'all 0.2s',
  }),
};

/* ─── Single Test Tab ─── */
function SingleTestTab({ libId }) {
  const [models, setModels] = useState([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [selectedModelId, setSelectedModelId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const [selectedMsg, setSelectedMsg] = useState(null);
  const [creatingSession, setCreatingSession] = useState(false);
  const chatEndRef = useRef(null);
  const selectedDebug = useMemo(
    () => (selectedMsg ? getDebugInfoFromMessage(selectedMsg) : null),
    [selectedMsg],
  );

  useEffect(() => {
    let cancelled = false;
    setModelsLoading(true);
    intentLibraryApi
      .listModels(libId)
      .then((res) => {
        if (cancelled) return;
        const raw = res.data;
        const list = Array.isArray(raw) ? raw : raw?.items ?? [];
        setModels(list);
      })
      .catch(() => !cancelled && setModels([]))
      .finally(() => !cancelled && setModelsLoading(false));
    return () => { cancelled = true; };
  }, [libId]);

  const fetchSessions = useCallback(
    (modelId) => {
      if (!modelId) return;
      setSessionsLoading(true);
      intentLibraryApi
        .listTestSessions(modelId)
        .then((res) => {
          const list = res.data ?? res ?? [];
          setSessions(Array.isArray(list) ? list : []);
        })
        .catch(() => setSessions([]))
        .finally(() => setSessionsLoading(false));
    },
    [],
  );

  useEffect(() => {
    if (selectedModelId) {
      fetchSessions(selectedModelId);
      setActiveSessionId(null);
      setMessages([]);
      setSelectedMsg(null);
    }
  }, [selectedModelId, fetchSessions]);

  const fetchMessages = useCallback((sessionId) => {
    if (!sessionId) return;
    setMessagesLoading(true);
    intentLibraryApi
      .getTestMessages(sessionId, { page: 1, page_size: 200 })
      .then((res) => {
        setMessages(getPaginatedMessageItems(res.data));
      })
      .catch(() => setMessages([]))
      .finally(() => setMessagesLoading(false));
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      fetchMessages(activeSessionId);
      setSelectedMsg(null);
    }
  }, [activeSessionId, fetchMessages]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleCreateSession = useCallback(async () => {
    if (!selectedModelId) {
      message.warning('请先选择模型');
      return;
    }
    setCreatingSession(true);
    try {
      const res = await intentLibraryApi.createTestSession(selectedModelId, {});
      const session = res.data ?? res;
      message.success('会话已创建');
      fetchSessions(selectedModelId);
      if (session?.id) setActiveSessionId(session.id);
    } catch {
      message.error('创建会话失败');
    } finally {
      setCreatingSession(false);
    }
  }, [selectedModelId, fetchSessions]);

  const handleSend = useCallback(async () => {
    const text = inputText.trim();
    if (!text || !activeSessionId) return;
    setInputText('');
    const tempId = `temp-${Date.now()}`;
    const userMsg = {
      id: tempId,
      role: 'user',
      text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setSending(true);
    try {
      const res = await intentLibraryApi.sendTestMessage(activeSessionId, { content: text });
      // 后端 success_response(data) 的 data 为 [userMsg, assistantMsg] 数组，非单条 bot
      const payload = res.data ?? res;
      const incoming = Array.isArray(payload) ? payload : payload ? [payload] : [];
      if (incoming.length) {
        setMessages((prev) => {
          const withoutTemp = removeTemporaryMessage(prev, tempId);
          return [...withoutTemp, ...incoming];
        });
      }
    } catch {
      setMessages((prev) => removeTemporaryMessage(prev, tempId));
      message.error('发送失败');
    } finally {
      setSending(false);
    }
  }, [inputText, activeSessionId]);

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const modelOptions = useMemo(
    () =>
      models.map((m) => ({
        value: m.id,
        label: `${m.version_name || m.id}${m.status ? ` (${m.status})` : ''}`,
      })),
    [models],
  );

  return (
    <div style={styles.chatLayout}>
      {/* Left sidebar */}
      <div style={styles.sidebar}>
        <Card
          size="small"
          title={<Text strong style={{ fontSize: 'var(--font-size-sm)' }}>选择模型</Text>}
          style={styles.sidebarCard}
          styles={{ body: { padding: 12 } }}
        >
          <Select
            placeholder="选择要测试的模型"
            style={{ width: '100%' }}
            loading={modelsLoading}
            options={modelOptions}
            value={selectedModelId}
            onChange={setSelectedModelId}
            notFoundContent={modelsLoading ? <Spin size="small" /> : '暂无模型'}
          />
        </Card>

        <Card
          size="small"
          title={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text strong style={{ fontSize: 'var(--font-size-sm)' }}>会话列表</Text>
              <Button
                type="primary"
                size="small"
                icon={<PlusOutlined />}
                loading={creatingSession}
                disabled={!selectedModelId}
                onClick={handleCreateSession}
              >
                新建会话
              </Button>
            </div>
          }
          style={{ ...styles.sidebarCard, flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
          styles={{ body: { padding: 8, overflow: 'auto', flex: 1 } }}
        >
          {sessionsLoading ? (
            <div style={{ textAlign: 'center', padding: 24 }}><Spin size="small" /></div>
          ) : sessions.length === 0 ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无会话" style={{ padding: 16 }} />
          ) : (
            sessions.map((s) => (
              <div
                key={s.id}
                style={styles.sessionItem(activeSessionId === s.id)}
                onClick={() => setActiveSessionId(s.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <MessageOutlined style={{ color: 'var(--color-text-tertiary)', fontSize: 12 }} />
                  <Text
                    ellipsis
                    strong={activeSessionId === s.id}
                    style={{ fontSize: 'var(--font-size-sm)', flex: 1 }}
                  >
                    {s.name || `会话 ${s.id?.slice(-6) ?? ''}`}
                  </Text>
                </div>
                {s.created_at && (
                  <Text
                    type="secondary"
                    style={{ fontSize: 'var(--font-size-xs)', marginLeft: 18, display: 'block' }}
                  >
                    {dayjs(s.created_at).format('MM-DD HH:mm')}
                  </Text>
                )}
              </div>
            ))
          )}
        </Card>
      </div>

      {/* Center chat area */}
      <div style={styles.chatPanel}>
        {!activeSessionId ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={selectedModelId ? '请选择或新建会话开始测试' : '请先选择模型'}
            />
          </div>
        ) : (
          <>
            <div style={styles.chatMessages}>
              {messagesLoading ? (
                <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>
              ) : messages.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <RobotOutlined style={{ fontSize: 40, color: 'var(--color-text-disabled)' }} />
                  <div style={{ marginTop: 12, color: 'var(--color-text-tertiary)' }}>
                    发送消息开始测试
                  </div>
                </div>
              ) : (
                messages.map((msg) => {
                  const isUser = msg.role === 'user';
                  const isSelected = selectedMsg?.id === msg.id;
                  return (
                    <div key={msg.id} style={styles.bubble(isUser)}>
                      <div
                        style={{
                          display: 'flex',
                          gap: 8,
                          alignItems: 'flex-start',
                          flexDirection: isUser ? 'row-reverse' : 'row',
                        }}
                      >
                        <div style={styles.bubbleIcon(isUser)}>
                          {isUser ? <UserOutlined /> : <RobotOutlined />}
                        </div>
                        <div
                          style={{
                            ...styles.bubbleInner(isUser),
                            outline: isSelected ? `2px solid var(--color-primary)` : 'none',
                            outlineOffset: 2,
                          }}
                          onClick={() => !isUser && setSelectedMsg(msg)}
                        >
                          {msg.text || msg.content || msg.message || ''}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={chatEndRef} />
            </div>

            <div style={styles.inputBar}>
              <TextArea
                placeholder="输入测试文本..."
                autoSize={{ minRows: 1, maxRows: 4 }}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={sending}
                style={{ flex: 1, borderRadius: 'var(--radius-md)' }}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                loading={sending}
                disabled={!inputText.trim()}
                onClick={handleSend}
                style={{ borderRadius: 'var(--radius-md)', height: 40 }}
              >
                发送
              </Button>
            </div>
          </>
        )}
      </div>

      {/* Right debug panel */}
      <div style={styles.debugPanel}>
        <div
          style={{
            padding: 'var(--space-3) var(--space-4)',
            borderBottom: '1px solid var(--color-border-light)',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <BugOutlined style={{ color: 'var(--color-primary)' }} />
          <Text strong style={{ fontSize: 'var(--font-size-sm)' }}>调试信息</Text>
        </div>
        <div style={{ padding: 'var(--space-3)' }}>
          {selectedMsg && selectedDebug ? (
            <Descriptions
              column={1}
              size="small"
              styles={{ label: { color: 'var(--color-text-secondary)', fontWeight: 500, width: 80 } }}
            >
              <Descriptions.Item label="领域">
                {selectedDebug.domain ? (
                  <Tag color="geekblue" style={{ margin: 0 }}>
                    {selectedDebug.domain}
                  </Tag>
                ) : (
                  <Text type="secondary">-</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="意图">
                {selectedDebug.intent ? (
                  <Tag color="blue" style={{ margin: 0 }}>
                    {selectedDebug.intent}
                  </Tag>
                ) : (
                  <Text type="secondary">-</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="置信度">
                <Space size={8}>
                  {confidenceTag(selectedDebug.confidence)}
                  {selectedDebug.confidence != null && (
                    <div
                      style={{
                        width: 60,
                        height: 6,
                        borderRadius: 3,
                        background: 'var(--color-border-light)',
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        style={{
                          width: `${((selectedDebug.confidence ?? 0) * 100).toFixed(0)}%`,
                          height: '100%',
                          borderRadius: 3,
                          background: confidenceColor(selectedDebug.confidence),
                          transition: 'width 0.3s',
                        }}
                      />
                    </div>
                  )}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="槽位">
                {selectedDebug.slots && Object.keys(selectedDebug.slots).length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {Object.entries(selectedDebug.slots).map(([k, v]) => (
                      <Tag key={k} style={{ margin: 0, fontFamily: 'var(--font-mono)', fontSize: 'var(--font-size-xs)' }}>
                        {k}: {String(v)}
                      </Tag>
                    ))}
                  </div>
                ) : (
                  <Text type="secondary">-</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="延迟">
                {selectedDebug.latency_ms != null ? (
                  <Text style={{ fontFamily: 'var(--font-mono)' }}>
                    {selectedDebug.latency_ms} ms
                  </Text>
                ) : (
                  <Text type="secondary">-</Text>
                )}
              </Descriptions.Item>
              {selectedDebug.fallback != null && (
                <Descriptions.Item label="兜底">
                  <Tag color={selectedDebug.fallback ? 'orange' : 'green'} style={{ margin: 0 }}>
                    {selectedDebug.fallback ? '是' : '否'}
                  </Tag>
                </Descriptions.Item>
              )}
              {selectedDebug.raw && (
                <Descriptions.Item label="原始响应">
                  <pre
                    style={{
                      fontSize: 'var(--font-size-xs)',
                      fontFamily: 'var(--font-mono)',
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-all',
                      maxHeight: 200,
                      overflow: 'auto',
                      background: 'var(--color-fill)',
                      padding: 8,
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    {typeof selectedDebug.raw === 'string'
                      ? selectedDebug.raw
                      : JSON.stringify(selectedDebug.raw, null, 2)}
                  </pre>
                </Descriptions.Item>
              )}
            </Descriptions>
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="点击机器人回复查看调试信息"
              style={{ padding: '40px 0' }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function BatchTestTab({ libId }) {
  const navigate = useNavigate();
  const [models, setModels] = useState([]);
  const [selectedModelId, setSelectedModelId] = useState(null);
  const [rows, setRows] = useState([]);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    intentLibraryApi
      .listModels(libId)
      .then((res) => {
        const raw = res.data;
        const list = Array.isArray(raw) ? raw : raw?.items ?? [];
        setModels(list);
      })
      .catch(() => setModels([]));
  }, [libId]);

  const modelOptions = useMemo(
    () =>
      models.map((m) => ({
        value: m.id,
        label: `${m.version_name || m.id} (${m.status})`,
      })),
    [models],
  );

  const addRow = useCallback(() => {
    setRows((r) => [
      ...r,
      {
        id: `r-${Date.now()}`,
        input: '',
        expected: '',
        actual: null,
        confidence: null,
        match: null,
      },
    ]);
  }, []);

  const runBatch = useCallback(async () => {
    setRunning(true);
    try {
      const createPayload = buildIntentLibraryBatchCreatePayload({
        modelId: selectedModelId,
        libraryId: libId,
      });
      const importPayload = buildIntentLibraryBatchImportPayload(rows);
      const batchRes = await batchTestApi.create(createPayload);
      const batch = batchRes.data ?? batchRes;
      const batchId = batch?.id;
      if (!batchId) throw new Error('创建批量测试失败，缺少 batch id');

      await batchTestApi.importCases(batchId, importPayload.cases);
      await batchTestApi.execute(batchId);

      message.success('已创建真实批量测试并开始执行');
      navigate(`/batch-test/${batchId}`);
    } catch (e) {
      message.error(e?.message || '创建批量测试失败');
    } finally {
      setRunning(false);
    }
  }, [selectedModelId, libId, rows, navigate]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <Card
        variant="borderless"
        style={{ borderRadius: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}
      >
        <Space wrap style={{ marginBottom: 16 }}>
          <Select
            placeholder="选择模型版本"
            style={{ minWidth: 260 }}
            options={modelOptions}
            value={selectedModelId}
            onChange={setSelectedModelId}
          />
          <Button onClick={addRow}>
            添加用例
          </Button>
          <Button type="primary" icon={<ThunderboltOutlined />} loading={running} onClick={runBatch}>
            创建并执行真实批量测试
          </Button>
        </Space>
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message="当前会基于所选模型创建真实 batch-test、导入测试用例并跳转到结果详情页；批量结果与分析以后端状态源为准。"
        />
        <Table
          rowKey="id"
          size="small"
          pagination={false}
          scroll={{ x: 960 }}
          columns={[
            {
              title: '输入',
              dataIndex: 'input',
              width: 220,
              render: (_, record) => (
                <Input
                  value={record.input}
                  placeholder="用户说法"
                  onChange={(e) =>
                    setRows((rs) =>
                      rs.map((x) => (x.id === record.id ? { ...x, input: e.target.value } : x)),
                    )
                  }
                />
              ),
            },
            {
              title: '期望意图',
              dataIndex: 'expected',
              width: 160,
              render: (_, record) => (
                <Input
                  value={record.expected}
                  placeholder="可选"
                  style={{ fontFamily: 'var(--font-mono)' }}
                  onChange={(e) =>
                    setRows((rs) =>
                      rs.map((x) =>
                        x.id === record.id ? { ...x, expected: e.target.value } : x,
                      ),
                    )
                  }
                />
              ),
            },
            {
              title: '操作',
              key: 'op',
              width: 72,
              render: (_, record) => (
                <Button
                  type="link"
                  danger
                  size="small"
                  onClick={() => setRows((rs) => rs.filter((x) => x.id !== record.id))}
                >
                  删除
                </Button>
              ),
            },
          ]}
          dataSource={rows}
          locale={{
            emptyText: (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description='点击「添加用例」开始批量测试' />
            ),
          }}
        />
      </Card>
    </div>
  );
}

/* ─── Model Test Page ─── */
export function ModelTestPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const tabItems = useMemo(
    () => [
      {
        key: 'single',
        label: (
          <span>
            <ExperimentOutlined style={{ marginRight: 6 }} />
            单条测试
          </span>
        ),
        children: <SingleTestTab libId={id} />,
      },
      {
        key: 'batch',
        label: (
          <span>
            <ThunderboltOutlined style={{ marginRight: 6 }} />
            批量测试
          </span>
        ),
        children: <BatchTestTab libId={id} />,
      },
    ],
    [id],
  );

  return (
    <div style={styles.pageWrap}>
      <div style={styles.header}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(`/intent-library/${id}`)}
        />
        <Title level={4} style={{ marginBottom: 0, flex: 1 }}>
          模型测试
        </Title>
      </div>

      <Tabs
        defaultActiveKey="single"
        items={tabItems}
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        styles={{
          content: { flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' },
        }}
      />
    </div>
  );
}

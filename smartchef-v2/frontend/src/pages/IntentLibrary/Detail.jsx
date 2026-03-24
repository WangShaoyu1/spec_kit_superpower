import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
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
  Select,
  AutoComplete,
  Progress,
  Skeleton,
  message,
  Tooltip,
  Empty,
  Checkbox,
  Switch,
  InputNumber,
  Row,
  Col,
  Divider,
  Popconfirm,
} from 'antd';
import {
  ArrowLeftOutlined,
  PlusOutlined,
  ThunderboltOutlined,
  ExperimentOutlined,
  CheckCircleOutlined,
  CloudUploadOutlined,
  InboxOutlined,
  UndoOutlined,
  DownloadOutlined,
  DatabaseOutlined,
  StopOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import useIntentLibraryStore from '../../stores/intentLibraryStore';
import ModelStatusTag from '../../components/ModelStatusTag';
import { intentLibraryApi } from '../../services/intentLibraryApi';

const { Title, Text } = Typography;

const MAX_MODELS = 5;

// 默认 Hub id；也可填本机目录（须含 config.json），见 README「离线预训练模型」
const BASE_MODEL_OPTIONS = [
  { value: 'bert-base-chinese', label: 'bert-base-chinese（中文推荐）' },
  { value: 'distilbert-base-uncased', label: 'distilbert-base-uncased（英文）' },
  { value: 'prajjwal1/bert-tiny', label: 'prajjwal1/bert-tiny（极小/调试用）' },
];

const cardStyle = {
  borderRadius: 12,
  boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
};

function ModelActions({ record, onAction }) {
  const { status } = record;

  const buttons = useMemo(() => {
    const items = [];

    if (status === 'draft') {
      items.push({
        key: 'train',
        label: '训练',
        icon: <ThunderboltOutlined />,
        action: 'train',
      });
    }

    if (status === 'trained') {
      items.push(
        {
          key: 'evaluate',
          label: '评估',
          icon: <ExperimentOutlined />,
          action: 'evaluate',
        },
        {
          key: 'setTestable',
          label: '设为测试态',
          icon: <CheckCircleOutlined />,
          action: 'setTestable',
        },
      );
    }

    if (status === 'testable') {
      items.push(
        {
          key: 'publish',
          label: '发布',
          icon: <CloudUploadOutlined />,
          action: 'publish',
          type: 'primary',
        },
        {
          key: 'archive',
          label: '归档',
          icon: <InboxOutlined />,
          action: 'archive',
        },
      );
    }

    if (status === 'published') {
      items.push({
        key: 'archive',
        label: '归档',
        icon: <InboxOutlined />,
        action: 'archive',
      });
    }

    if (status === 'archived') {
      items.push({
        key: 'restore',
        label: '恢复',
        icon: <UndoOutlined />,
        action: 'restore',
      });
    }

    return items;
  }, [status]);

  return (
    <Space size={4} wrap>
      {status === 'training' && (
        <Popconfirm
          title="确定停止训练？进度将丢失。"
          okText="停止"
          cancelText="取消"
          onConfirm={() => onAction('cancelTraining', record)}
        >
          <Button type="link" size="small" danger icon={<StopOutlined />}>
            停止训练
          </Button>
        </Popconfirm>
      )}
      {['draft', 'failed', 'archived'].includes(status) && (
        <Popconfirm
          title="确定删除该版本记录？不可恢复。"
          okText="删除"
          cancelText="取消"
          onConfirm={() => onAction('deleteModel', record)}
        >
          <Button type="link" size="small" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      )}
      {buttons.map((btn) => (
        <Button
          key={btn.key}
          type={btn.type || 'link'}
          size="small"
          icon={btn.icon}
          onClick={() => onAction(btn.action, record)}
        >
          {btn.label}
        </Button>
      ))}
      <Tooltip title="下载模型">
        <Button
          type="link"
          size="small"
          icon={<DownloadOutlined />}
          disabled={!['trained', 'testable', 'published'].includes(status)}
          onClick={() => onAction('download', record)}
        />
      </Tooltip>
    </Space>
  );
}

export default function IntentLibraryDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [modelForm] = Form.useForm();
  const [trainForm] = Form.useForm();
  const [modelModalOpen, setModelModalOpen] = useState(false);
  const [modelSubmitLoading, setModelSubmitLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [trainingDatasets, setTrainingDatasets] = useState([]);

  const [trainModalOpen, setTrainModalOpen] = useState(false);
  const [trainTarget, setTrainTarget] = useState(null);
  const [trainSubmitLoading, setTrainSubmitLoading] = useState(false);

  const [publishModalOpen, setPublishModalOpen] = useState(false);
  const [publishTarget, setPublishTarget] = useState(null);
  const [publishAck, setPublishAck] = useState(false);
  const [publishTick, setPublishTick] = useState(5);
  const publishTimerRef = useRef(null);

  const {
    currentLibrary: library,
    detailLoading,
    models,
    modelsLoading,
    fetchLibraryDetail,
    fetchModels,
    startTrainJob,
    pollTrainingUntilDone,
    evaluateModel,
    setTestable,
    publishModel,
    archiveModel,
    cancelTraining,
    deleteModel,
    restoreModel,
    createModel,
    clearDetail,
  } = useIntentLibraryStore();

  useEffect(() => {
    fetchLibraryDetail(id);
    fetchModels(id);
    return () => clearDetail();
  }, [id, fetchLibraryDetail, fetchModels, clearDetail]);

  useEffect(() => {
    if (!id) return;
    intentLibraryApi
      .listDatasets(id, { page: 1, page_size: 100 })
      .then((res) => {
        const payload = res.data;
        const raw = payload?.items ?? payload ?? [];
        setTrainingDatasets(Array.isArray(raw) ? raw : []);
      })
      .catch(() => setTrainingDatasets([]));
  }, [id]);

  useEffect(() => {
    if (!publishModalOpen) {
      if (publishTimerRef.current) clearInterval(publishTimerRef.current);
      publishTimerRef.current = null;
      setPublishAck(false);
      setPublishTick(5);
      return;
    }
    setPublishAck(false);
    setPublishTick(5);
    if (publishTimerRef.current) clearInterval(publishTimerRef.current);
    publishTimerRef.current = setInterval(() => {
      setPublishTick((t) => {
        if (t <= 1) {
          if (publishTimerRef.current) clearInterval(publishTimerRef.current);
          publishTimerRef.current = null;
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => {
      if (publishTimerRef.current) clearInterval(publishTimerRef.current);
      publishTimerRef.current = null;
    };
  }, [publishModalOpen]);

  const publishedBaseline = useMemo(
    () => models.find((m) => m.status === 'published' || m.is_published),
    [models],
  );

  const handleCreateModel = useCallback(async () => {
    try {
      const values = await modelForm.validateFields();
      setModelSubmitLoading(true);
      await createModel(id, {
        version_name: values.version_name,
        train_dataset_id: values.train_dataset_id,
        notes: values.notes,
      });
      message.success('模型版本创建成功');
      setModelModalOpen(false);
      modelForm.resetFields();
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '创建失败');
    } finally {
      setModelSubmitLoading(false);
    }
  }, [modelForm, id, createModel]);

  const runTrain = useCallback(async () => {
    if (!trainTarget) return;
    const modelIdForPoll = trainTarget.id;
    try {
      const values = await trainForm.validateFields();
      setTrainSubmitLoading(true);
      const early = values.early_stopping;
      await startTrainJob(modelIdForPoll, {
        base_model: values.base_model,
        learning_rate: values.learning_rate,
        batch_size: values.batch_size,
        epochs: values.epochs,
        early_stopping: early,
        early_stopping_patience: early ? values.early_stopping_patience : undefined,
      });
      message.success('训练任务已提交，正在后台训练…');
      setTrainModalOpen(false);
      setTrainTarget(null);
      trainForm.resetFields();
      void pollTrainingUntilDone(modelIdForPoll, id).then((result) => {
        if (result.ok) {
          message.success('训练完成，可下载模型包');
        } else if (result.ok === false) {
          const errText = result.error || result.model?.notes || '';
          if (String(errText).includes('取消')) {
            message.warning('训练已取消');
          } else {
            message.error(errText || '训练失败');
          }
        } else if (result.timeout) {
          message.warning('训练耗时较长，请稍后刷新页面查看状态');
        }
      });
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '操作失败');
    } finally {
      setTrainSubmitLoading(false);
    }
  }, [trainForm, trainTarget, startTrainJob, pollTrainingUntilDone, id]);

  const runPublish = useCallback(async () => {
    if (!publishTarget || publishTick > 0 || !publishAck) return;
    setActionLoading(publishTarget.id);
    try {
      await publishModel(publishTarget.id);
      message.success('发布成功');
      setPublishModalOpen(false);
      setPublishTarget(null);
    } catch (err) {
      message.error(err?.message || '发布失败');
    } finally {
      setActionLoading(null);
    }
  }, [publishTarget, publishTick, publishAck, publishModel]);

  const handleModelAction = useCallback(
    async (action, record) => {
      const modelId = record.id;
      if (action === 'train') {
        setTrainTarget(record);
        trainForm.setFieldsValue({
          base_model: 'bert-base-chinese',
          learning_rate: 2e-5,
          batch_size: 32,
          epochs: 10,
          early_stopping: true,
          early_stopping_patience: 2,
        });
        setTrainModalOpen(true);
        return;
      }
      if (action === 'publish') {
        setPublishTarget(record);
        setPublishModalOpen(true);
        return;
      }

      setActionLoading(modelId);
      try {
        switch (action) {
          case 'evaluate':
            await evaluateModel(modelId, {});
            message.success('评估任务已提交');
            break;
          case 'setTestable':
            await setTestable(modelId);
            message.success('已设为测试态');
            break;
          case 'archive':
            await archiveModel(modelId);
            message.success('已归档');
            break;
          case 'restore':
            await restoreModel(modelId);
            message.success('已恢复');
            break;
          case 'download': {
            const res = await intentLibraryApi.downloadModel(modelId);
            const blob = new Blob([res.data]);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `model-${record.version_name || modelId}.zip`;
            a.click();
            URL.revokeObjectURL(url);
            break;
          }
          case 'cancelTraining':
            await cancelTraining(modelId);
            message.success('已请求停止训练');
            break;
          case 'deleteModel':
            await deleteModel(modelId);
            message.success('已删除该版本');
            break;
          default:
            break;
        }
      } catch (err) {
        message.error(err?.message || '操作失败');
      } finally {
        setActionLoading(null);
      }
    },
    [
      trainForm,
      evaluateModel,
      setTestable,
      archiveModel,
      restoreModel,
      cancelTraining,
      deleteModel,
      id,
    ],
  );

  const modelColumns = useMemo(
    () => [
      {
        title: '版本名称',
        dataIndex: 'version_name',
        key: 'version_name',
        render: (text) => <Text strong>{text}</Text>,
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 120,
        render: (status) => <ModelStatusTag status={status} />,
      },
      {
        title: '训练集',
        dataIndex: 'dataset_name',
        key: 'dataset_name',
        ellipsis: true,
        render: (text, record) =>
          text || record.train_dataset_name || <Text type="secondary">-</Text>,
      },
      {
        title: 'F1-Score',
        key: 'metrics',
        width: 200,
        render: (_, record) => {
          if (record.status === 'training') {
            const pct = record.training_progress ?? record.progress ?? 0;
            // progress=0：准备阶段；1–19：已进入 PyTorch 线程，加载 BERT 权重或首个 epoch 结束前可能停留较久
            if (pct === 0) {
              return (
                <Tooltip title="准备中：加载数据或首次下载预训练模型（可能较慢，请稍候）">
                  <Progress percent={0} status="active" size="small" format={() => '准备中'} />
                </Tooltip>
              );
            }
            if (pct > 0 && pct < 20) {
              return (
                <Tooltip title="训练中：加载预训练编码器或跑首个 epoch（无 epoch 日志属正常；CPU 上可能需数分钟）">
                  <Progress percent={pct} status="active" size="small" />
                </Tooltip>
              );
            }
            return <Progress percent={pct} size="small" />;
          }
          if (record.status === 'evaluating') {
            return (
              <Progress
                percent={record.eval_progress ?? record.progress ?? 0}
                size="small"
                status="active"
                strokeColor="#faad14"
              />
            );
          }
          const metrics = record.metrics;
          if (!metrics) return <Text type="secondary">-</Text>;
          const intentF1 =
            metrics.best_val_intent_f1 ?? metrics.val_intent_f1 ?? metrics.f1 ?? metrics.intent_f1;
          return (
            <Space size={8}>
              {metrics.accuracy != null && (
                <Tooltip title="Accuracy">
                  <Tag color="blue" style={{ fontFamily: 'var(--font-mono)', margin: 0 }}>
                    Acc {(metrics.accuracy * 100).toFixed(1)}%
                  </Tag>
                </Tooltip>
              )}
              {intentF1 != null && (
                <Tooltip title="Intent F1">
                  <Tag color="green" style={{ fontFamily: 'var(--font-mono)', margin: 0 }}>
                    Intent F1 {(intentF1 * 100).toFixed(1)}%
                  </Tag>
                </Tooltip>
              )}
            </Space>
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
        width: 280,
        render: (_, record) => (
          <ModelActions record={record} onAction={handleModelAction} />
        ),
      },
    ],
    [handleModelAction],
  );

  const datasetOptions = useMemo(
    () =>
      trainingDatasets.map((d) => ({
        value: d.id,
        label: d.name || d.id,
      })),
    [trainingDatasets],
  );

  if (detailLoading) {
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

  if (!library) {
    return (
      <Empty description="指令库不存在或加载失败">
        <Button type="primary" onClick={() => navigate('/intent-library')}>
          返回列表
        </Button>
      </Empty>
    );
  }

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
          { title: library.name },
        ]}
      />

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/intent-library')}
        />
        <div style={{ flex: 1 }}>
          <Title level={4} style={{ marginBottom: 0 }}>
            {library.name}
          </Title>
        </div>
        <Space>
          <Button
            icon={<DatabaseOutlined />}
            onClick={() => navigate(`/intent-library/${id}/datasets`)}
          >
            数据集
          </Button>
          <Button
            icon={<ExperimentOutlined />}
            onClick={() => navigate(`/intent-library/${id}/test`)}
          >
            测试
          </Button>
        </Space>
      </div>

      <Card variant="borderless" style={cardStyle}>
        <Descriptions
          column={3}
          size="small"
          styles={{ label: { color: 'var(--color-text-secondary)', fontWeight: 500 } }}
        >
          <Descriptions.Item label="Key">
            <Text code>{library.library_key}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="语言">
            {library.language === 'zh' ? (
              <Tag color="blue">中文</Tag>
            ) : (
              <Tag color="green">English</Tag>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {library.created_at ? dayjs(library.created_at).format('YYYY-MM-DD HH:mm') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="置信度阈值">
            <Text style={{ fontFamily: 'var(--font-mono)' }}>
              {library.confidence_threshold?.toFixed(2) ?? '-'}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="模糊阈值">
            <Text style={{ fontFamily: 'var(--font-mono)' }}>
              {library.ambiguity_threshold?.toFixed(2) ?? '-'}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="意图 F1 阈值">
            <Text style={{ fontFamily: 'var(--font-mono)' }}>
              {library.intent_f1_threshold != null
                ? Number(library.intent_f1_threshold).toFixed(2)
                : '-'}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="描述" span={3}>
            {library.description || <Text type="secondary">暂无描述</Text>}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card
        variant="borderless"
        style={cardStyle}
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text strong style={{ fontSize: 'var(--font-size-lg)' }}>
              模型版本
            </Text>
            <Tooltip
              title={models.length >= MAX_MODELS ? `最多 ${MAX_MODELS} 个模型版本` : undefined}
            >
              <Button
                type="primary"
                size="small"
                icon={<PlusOutlined />}
                disabled={models.length >= MAX_MODELS}
                onClick={() => {
                  modelForm.resetFields();
                  setModelModalOpen(true);
                }}
              >
                新建模型版本
              </Button>
            </Tooltip>
          </div>
        }
        styles={{ body: { padding: 0 } }}
      >
        <Table
          rowKey="id"
          columns={modelColumns}
          dataSource={models}
          loading={modelsLoading || !!actionLoading}
          pagination={false}
          scroll={{ x: 900 }}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无模型版本"
                style={{ padding: '32px 0' }}
              />
            ),
          }}
        />
      </Card>

      <Modal
        open={modelModalOpen}
        title="新建模型版本"
        onCancel={() => setModelModalOpen(false)}
        onOk={handleCreateModel}
        confirmLoading={modelSubmitLoading}
        okText="创建"
        cancelText="取消"
        width={480}
        centered
        destroyOnHidden
      >
        <Form form={modelForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="version_name"
            label="版本名称"
            rules={[{ required: true, message: '请输入版本名称' }]}
          >
            <Input placeholder="例如: v1.0.0" />
          </Form.Item>

          <Form.Item name="train_dataset_id" label="训练数据集">
            <Select
              placeholder="选择训练数据集（可选）"
              allowClear
              options={datasetOptions}
              notFoundContent="暂无可用数据集"
            />
          </Form.Item>

          <Form.Item name="notes" label="备注 / 描述">
            <Input.TextArea rows={3} placeholder="版本说明..." />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        open={trainModalOpen}
        title="训练配置"
        onCancel={() => {
          setTrainModalOpen(false);
          setTrainTarget(null);
        }}
        onOk={runTrain}
        confirmLoading={trainSubmitLoading}
        okText="开始训练"
        cancelText="取消"
        width={520}
        centered
        destroyOnHidden
      >
        <Form form={trainForm} layout="vertical" style={{ marginTop: 8 }}>
          <Form.Item
            name="base_model"
            label="基础模型"
            rules={[{ required: true, message: '请选择或输入基础模型' }]}
            extra="可选 Hub 名称（如 bert-base-chinese），或本机路径：绝对路径，或相对 backend 的目录（内含 config.json）。离线请预置到 data/hf_cache 或 data/models/pretrained/ 并设 HF_LOCAL_FILES_ONLY=1。"
          >
            <AutoComplete
              options={BASE_MODEL_OPTIONS}
              placeholder="选择或输入 Hub id / 本机模型目录"
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase()) ||
                (option?.value ?? '').toLowerCase().includes(input.toLowerCase())
              }
              style={{ width: '100%' }}
            />
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="learning_rate"
                label="学习率"
                rules={[{ required: true, message: '必填' }]}
              >
                <InputNumber min={1e-6} max={1} step={1e-5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="batch_size"
                label="批次大小"
                rules={[{ required: true, message: '必填' }]}
              >
                <InputNumber min={1} max={512} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="epochs"
                label="训练轮数"
                rules={[{ required: true, message: '必填' }]}
              >
                <InputNumber min={1} max={200} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="early_stopping" label="早停" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(p, c) => p.early_stopping !== c.early_stopping}>
            {({ getFieldValue }) =>
              getFieldValue('early_stopping') ? (
                <Form.Item
                  name="early_stopping_patience"
                  label="Patience"
                  rules={[{ required: true, message: '请输入 patience' }]}
                >
                  <InputNumber min={1} max={20} style={{ width: '100%' }} />
                </Form.Item>
              ) : null
            }
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        open={publishModalOpen}
        title="发布模型"
        onCancel={() => {
          setPublishModalOpen(false);
          setPublishTarget(null);
        }}
        footer={[
          <Button key="cancel" onClick={() => setPublishModalOpen(false)}>
            取消
          </Button>,
          <Button
            key="ok"
            type="primary"
            disabled={!publishAck || publishTick > 0}
            style={{ background: publishTick > 0 ? undefined : '#52c41a', borderColor: '#52c41a' }}
            onClick={runPublish}
          >
            {publishTick > 0 ? `确认发布 (${publishTick}s)` : '确认发布'}
          </Button>,
        ]}
        width={640}
        centered
        destroyOnHidden
      >
        <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)', display: 'block', marginBottom: 16 }}>
          发布后将切换线上推理使用的模型版本，请仔细核对差异。
        </Text>
        <Row gutter={16}>
          <Col span={12}>
            <Card
              variant="borderless"
              style={{
                ...cardStyle,
                background: 'rgba(0,0,0,0.04)',
                border: '1px solid var(--color-border-light)',
              }}
              title={<Text type="secondary">当前线上版本</Text>}
            >
              {publishedBaseline ? (
                <>
                  <Text strong style={{ display: 'block', marginBottom: 8 }}>
                    {publishedBaseline.version_name}
                  </Text>
                  <Tag color="default">{publishedBaseline.status}</Tag>
                  <Divider style={{ margin: '12px 0' }} />
                  <Text style={{ fontSize: 'var(--font-size-sm)' }}>
                    F1:{' '}
                    {publishedBaseline.metrics?.f1 != null
                      ? `${(publishedBaseline.metrics.f1 * 100).toFixed(1)}%`
                      : '-'}
                  </Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)' }}>
                    {publishedBaseline.created_at
                      ? dayjs(publishedBaseline.created_at).format('YYYY-MM-DD HH:mm')
                      : ''}
                  </Text>
                </>
              ) : (
                <Text type="secondary">暂无已发布版本（首次发布）</Text>
              )}
            </Card>
          </Col>
          <Col span={12}>
            <Card
              variant="borderless"
              style={{
                ...cardStyle,
                background: 'rgba(82, 196, 26, 0.08)',
                border: '1px solid #b7eb8f',
              }}
              title={
                <Text style={{ color: '#52c41a' }}>
                  <CheckCircleOutlined /> 即将发布
                </Text>
              }
            >
              {publishTarget ? (
                <>
                  <Text strong style={{ display: 'block', marginBottom: 8 }}>
                    {publishTarget.version_name}
                  </Text>
                  <Tag color="success">{publishTarget.status}</Tag>
                  <Divider style={{ margin: '12px 0' }} />
                  <Text style={{ fontSize: 'var(--font-size-sm)' }}>
                    F1:{' '}
                    {publishTarget.metrics?.f1 != null
                      ? `${(publishTarget.metrics.f1 * 100).toFixed(1)}%`
                      : '-'}
                  </Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 'var(--font-size-xs)' }}>
                    {publishTarget.created_at
                      ? dayjs(publishTarget.created_at).format('YYYY-MM-DD HH:mm')
                      : ''}
                  </Text>
                </>
              ) : null}
            </Card>
          </Col>
        </Row>
        <Checkbox
          style={{ marginTop: 20 }}
          checked={publishAck}
          onChange={(e) => setPublishAck(e.target.checked)}
        >
          我已确认新版本已评估通过，并了解回滚需重新发布其他版本
        </Checkbox>
      </Modal>
    </div>
  );
}

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
  InputNumber,
  message,
  Empty,
  Upload,
  Progress,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  BookOutlined,
  RocketOutlined,
  ExperimentOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  UploadOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  InboxOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import useIntentLibraryStore from '../../stores/intentLibraryStore';
import DangerConfirmModal from '../../components/DangerConfirmModal';
import { intentLibraryApi } from '../../services/intentLibraryApi';

const { Title, Text, Paragraph } = Typography;

const LANGUAGE_OPTIONS = [
  { value: '', label: '全部语言' },
  { value: 'zh', label: '中文' },
  { value: 'en', label: 'English' },
];

const STATUS_OPTIONS = [
  { value: '', label: '全部状态' },
  { value: 'published', label: '已发布' },
  { value: 'draft', label: '草稿' },
];

const MAX_MODEL_SLOTS = 5;

const STAT_CARDS = [
  {
    key: 'total',
    label: '指令库总数',
    icon: <BookOutlined />,
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    getValue: (_libs, opts) => opts?.total ?? _libs.length,
  },
  {
    key: 'published',
    label: '已发布',
    icon: <CheckCircleOutlined />,
    gradient: 'linear-gradient(135deg, #52c41a 0%, #95de64 100%)',
    getValue: (_libs, opts) => opts?.publishedCount ?? 0,
  },
  {
    key: 'training',
    label: '训练中',
    icon: <ExperimentOutlined />,
    gradient: 'linear-gradient(135deg, #faad14 0%, #ffc53d 100%)',
    getValue: (_libs, opts) => opts?.trainingCount ?? 0,
  },
  {
    key: 'nearFull',
    label: '即将满额',
    icon: <RocketOutlined />,
    gradient: 'linear-gradient(135deg, #1677ff 0%, #69b1ff 100%)',
    getValue: () => '-',
  },
];

export default function IntentLibrary() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingLib, setEditingLib] = useState(null);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [importOpen, setImportOpen] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const [importFileList, setImportFileList] = useState([]);

  const {
    libraries,
    loading,
    total,
    page,
    pageSize,
    search,
    languageFilter,
    fetchLibraries,
    createLibrary,
    updateLibrary,
    deleteLibrary,
    setSearch,
    setLanguageFilter,
    setPage,
    setPageSize,
  } = useIntentLibraryStore();

  useEffect(() => {
    const ac = new AbortController();
    fetchLibraries(ac.signal);
    return () => ac.abort();
  }, [fetchLibraries, page, pageSize, search, languageFilter]);

  const computedStats = useMemo(() => {
    const publishedCount = libraries.filter(
      (lib) => lib.latest_model_status === 'published',
    ).length;
    const trainingCount = libraries.filter(
      (lib) => lib.latest_model_status === 'training',
    ).length;
    return { total, publishedCount, trainingCount };
  }, [libraries, total]);

  const filteredLibraries = useMemo(() => {
    if (!statusFilter) return libraries;
    if (statusFilter === 'published') {
      return libraries.filter((lib) => lib.latest_model_status === 'published');
    }
    return libraries.filter((lib) => lib.latest_model_status !== 'published');
  }, [libraries, statusFilter]);

  const openCreate = useCallback(() => {
    setEditingLib(null);
    form.resetFields();
    form.setFieldsValue({
      language: 'zh',
      confidence_threshold: 0.7,
      ambiguity_threshold: 0.15,
    });
    setModalOpen(true);
  }, [form]);

  const openEdit = useCallback(
    (record) => {
      setEditingLib(record);
      form.setFieldsValue({
        name: record.name,
        language: record.language,
        description: record.description,
        confidence_threshold: record.confidence_threshold,
        ambiguity_threshold: record.ambiguity_threshold,
      });
      setModalOpen(true);
    },
    [form],
  );

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      if (editingLib) {
        await updateLibrary(editingLib.id, values);
        message.success('更新成功');
      } else {
        await createLibrary(values);
        message.success('创建成功');
      }
      setModalOpen(false);
    } catch (err) {
      if (err?.errorFields) return;
      message.error(err?.message || '操作失败');
    } finally {
      setSubmitLoading(false);
    }
  }, [form, editingLib, createLibrary, updateLibrary]);

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await deleteLibrary(deleteTarget.id);
      message.success('删除成功');
      setDeleteTarget(null);
    } catch (err) {
      message.error(err?.message || '删除失败');
    } finally {
      setDeleteLoading(false);
    }
  }, [deleteTarget, deleteLibrary]);

  const handleReset = useCallback(() => {
    setSearch('');
    setLanguageFilter('');
    setStatusFilter('');
  }, [setSearch, setLanguageFilter]);

  const handleImportOk = useCallback(async () => {
    const file = importFileList[0]?.originFileObj;
    if (!file) {
      message.warning('请选择 JSON 或 ZIP 文件');
      return;
    }
    setImportLoading(true);
    try {
      if (file.name?.toLowerCase().endsWith('.json')) {
        const text = await file.text();
        let data;
        try {
          data = JSON.parse(text);
        } catch {
          message.error('JSON 格式无效');
          return;
        }
        const items = Array.isArray(data) ? data : data.libraries;
        if (!Array.isArray(items)) {
          message.error('JSON 需为数组或 { libraries: [] }');
          return;
        }
        let ok = 0;
        for (const item of items) {
          if (!item?.library_key || !item?.name) continue;
          await createLibrary({
            library_key: item.library_key,
            name: item.name,
            language: item.language || 'zh',
            description: item.description,
            confidence_threshold: item.confidence_threshold ?? item.default_confidence_threshold ?? 0.7,
            ambiguity_threshold:
              item.ambiguity_threshold ?? item.default_slot_f1_threshold ?? 0.15,
          });
          ok += 1;
        }
        message.success(`已导入 ${ok} 个指令库`);
        setImportOpen(false);
        setImportFileList([]);
        await fetchLibraries();
        return;
      }
      const formData = new FormData();
      formData.append('file', file);
      try {
        await intentLibraryApi.importLibraries(formData);
        message.success('导入任务已提交');
        setImportOpen(false);
        setImportFileList([]);
        await fetchLibraries();
      } catch {
        message.warning('ZIP 或远程导入需服务端 /intent-libraries/import；可改用 JSON 批量导入');
      }
    } catch (err) {
      message.error(err?.message || '导入失败');
    } finally {
      setImportLoading(false);
    }
  }, [importFileList, createLibrary, fetchLibraries]);

  const columns = useMemo(
    () => [
      {
        title: '名称',
        dataIndex: 'name',
        key: 'name',
        width: 160,
        ellipsis: true,
        render: (text, record) => (
          <Button
            type="link"
            style={{ padding: 0, fontWeight: 500 }}
            onClick={() => navigate(`/intent-library/${record.id}`)}
          >
            {text}
          </Button>
        ),
      },
      {
        title: 'Key',
        dataIndex: 'library_key',
        key: 'library_key',
        width: 160,
        ellipsis: true,
        render: (text) => (
          <Text code style={{ fontSize: 'var(--font-size-xs)' }}>
            {text}
          </Text>
        ),
      },
      {
        title: '语言',
        dataIndex: 'language',
        key: 'language',
        width: 100,
        render: (lang) =>
          lang === 'zh' ? (
            <Tag color="blue">中文</Tag>
          ) : (
            <Tag color="green">English</Tag>
          ),
      },
      {
        title: '状态',
        key: 'status',
        width: 120,
        render: (_, record) => {
          const st = record.latest_model_status;
          if (st === 'published') {
            return (
              <Tag icon={<CheckCircleOutlined />} color="success">
                已发布
              </Tag>
            );
          }
          if (st === 'training' || st === 'evaluating') {
            return (
              <Tag icon={<SyncOutlined spin />} color="warning">
                {st === 'training' ? '训练中' : '评估中'}
              </Tag>
            );
          }
          return (
            <Tag icon={<InboxOutlined />} color="default">
              草稿
            </Tag>
          );
        },
      },
      {
        title: '意图数',
        dataIndex: 'intent_count',
        key: 'intent_count',
        width: 88,
        align: 'center',
        render: (n) => (
          <Text style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
            {n ?? 0}
          </Text>
        ),
      },
      {
        title: '模型额度',
        dataIndex: 'model_count',
        key: 'model_count',
        width: 140,
        align: 'center',
        render: (count) => {
          const n = Math.min(count ?? 0, MAX_MODEL_SLOTS);
          return (
            <Progress
              percent={Math.round((n / MAX_MODEL_SLOTS) * 100)}
              format={() => `${n}/${MAX_MODEL_SLOTS}`}
              size="small"
              style={{ minWidth: 96 }}
              strokeColor={n >= MAX_MODEL_SLOTS ? '#ff4d4f' : '#1677ff'}
            />
          );
        },
      },
      {
        title: '置信度阈值',
        dataIndex: 'confidence_threshold',
        key: 'confidence_threshold',
        width: 120,
        align: 'center',
        render: (val) => (
          <Text style={{ fontFamily: 'var(--font-mono)' }}>
            {val != null ? val.toFixed(2) : '-'}
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
        width: 200,
        render: (_, record) => (
          <Space size={4}>
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/intent-library/${record.id}`)}
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
    [navigate, openEdit],
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={4} style={{ marginBottom: 4 }}>
            指令库管理
          </Title>
          <Text type="secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
            管理意图识别模型的指令库，包括训练数据、模型版本和评估
          </Text>
        </div>
        <Space>
          <Button icon={<UploadOutlined />} onClick={() => setImportOpen(true)}>
            导入
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新建指令库
          </Button>
        </Space>
      </div>

      {/* Stat cards */}
      <Row gutter={16}>
        {STAT_CARDS.map((card) => (
          <Col span={6} key={card.key}>
            <Card
              style={{
                borderRadius: 'var(--radius-lg)',
                border: 'none',
                overflow: 'hidden',
                minWidth: 180,
              }}
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
                  <Text
                    type="secondary"
                    style={{ fontSize: 'var(--font-size-xs)', display: 'block' }}
                  >
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
                    {card.getValue(libraries, computedStats)}
                  </Text>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Filter bar + Table */}
      <Card
        style={{ minWidth: 0 }}
        styles={{
          body: { padding: 0 },
        }}
      >
        <div
          style={{
            padding: '16px 24px',
            display: 'flex',
            gap: 12,
            borderBottom: '1px solid var(--color-border-light)',
          }}
        >
          <Input
            placeholder="搜索指令库名称或 Key..."
            prefix={<SearchOutlined style={{ color: 'var(--color-text-tertiary)' }} />}
            allowClear
            style={{ width: 320 }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Select
            value={languageFilter}
            onChange={setLanguageFilter}
            options={LANGUAGE_OPTIONS}
            style={{ width: 140 }}
          />
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            options={STATUS_OPTIONS}
            style={{ width: 140 }}
          />
          <Button type="primary" onClick={() => fetchLibraries()}>
            查询
          </Button>
          <Button onClick={handleReset}>重置</Button>
        </div>

        <div style={{ minWidth: 0 }}>
          <Table
            rowKey="id"
            columns={columns}
            dataSource={filteredLibraries}
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
                description="暂无指令库"
                style={{ padding: '48px 0' }}
              >
                <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
                  创建第一个指令库
                </Button>
              </Empty>
            ),
          }}
        />
        </div>
      </Card>

      {/* Create / Edit Modal */}
      <Modal
        open={modalOpen}
        title={editingLib ? '编辑指令库' : '新建指令库'}
        onCancel={() => setModalOpen(false)}
        onOk={handleSubmit}
        confirmLoading={submitLoading}
        okText={editingLib ? '保存' : '创建'}
        cancelText="取消"
        width={520}
        centered
        destroyOnHidden
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          {!editingLib && (
            <Form.Item
              name="library_key"
              label="指令库 Key"
              rules={[
                { required: true, message: '请输入 Key' },
                { pattern: /^[a-z][a-z0-9_]*$/, message: '仅允许小写字母、数字和下划线，以字母开头' },
              ]}
              extra="创建后不可修改"
            >
              <Input placeholder="例如: smart_cooking_zh" style={{ fontFamily: 'var(--font-mono)' }} />
            </Form.Item>
          )}

          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="例如: 智能烹饪中文指令库" />
          </Form.Item>

          <Form.Item
            name="language"
            label="语言"
            rules={[{ required: true, message: '请选择语言' }]}
          >
            <Select
              options={[
                { value: 'zh', label: '中文' },
                { value: 'en', label: 'English' },
              ]}
            />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="指令库的用途描述..." />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="confidence_threshold"
                label="置信度阈值"
                rules={[{ required: true, message: '请输入' }]}
              >
                <InputNumber min={0} max={1} step={0.05} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="ambiguity_threshold"
                label="模糊阈值"
                rules={[{ required: true, message: '请输入' }]}
              >
                <InputNumber min={0} max={1} step={0.05} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Delete confirmation */}
      <DangerConfirmModal
        open={!!deleteTarget}
        title="删除指令库"
        description={`确定删除指令库「${deleteTarget?.name}」？删除后所有关联的数据集和模型版本也将被删除。`}
        impactText="此操作不可恢复，关联的训练数据、模型文件将被永久移除。"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        confirmLoading={deleteLoading}
      />

      <Modal
        title="导入指令库"
        open={importOpen}
        onCancel={() => {
          setImportOpen(false);
          setImportFileList([]);
        }}
        onOk={handleImportOk}
        confirmLoading={importLoading}
        okText="开始导入"
        width={520}
        centered
        destroyOnHidden
      >
        <Paragraph type="secondary" style={{ fontSize: 'var(--font-size-sm)', marginBottom: 12 }}>
          支持 <Text strong>JSON</Text>（数组或 {'{ libraries: [...] }'}，字段含 library_key、name）或{' '}
          <Text strong>ZIP</Text>（需服务端配置导入接口）。
        </Paragraph>
        <Upload.Dragger
          accept=".json,.zip,application/json,application/zip"
          maxCount={1}
          fileList={importFileList}
          beforeUpload={() => false}
          onChange={({ fileList: fl }) => setImportFileList(fl)}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ color: '#1677ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此处</p>
          <p className="ant-upload-hint" style={{ fontSize: 'var(--font-size-sm)' }}>
            单文件，最大建议 20MB
          </p>
        </Upload.Dragger>
      </Modal>
    </div>
  );
}
